// The boat: rigid-body physics on the real water surface, controls, cameras,
// boarding, mooring, wake and spray emission.
//
// Buoyancy is sampled at 18 hull points against the same surface function the
// water is rendered with (WaterProbe queries, read back asynchronously), so
// the boat rides exactly the waves you see - including its own wake and the
// shore breakers.

import * as THREE from 'three/webgpu';
import { buildBoatModel, hullSamplePoints, BOAT, sheerY, zOf, halfBeam } from './boatModel.js';

const RHO = 1025, G = 9.81;
const MASS = 2600;
const CG = new THREE.Vector3(0, 0.15, 1.35);
const tmpV = new THREE.Vector3(), tmpV2 = new THREE.Vector3(), tmpQ = new THREE.Quaternion();
const up = new THREE.Vector3(0, 1, 0);

export class Boat {
  constructor({ scene, probe, collision, wake, spray = null, mooring }) {
    this.model = buildBoatModel();
    this.group = this.model.group;
    scene.add(this.group);
    this.probe = probe;
    this.collision = collision;
    this.wake = wake;
    this.spray = spray;
    this.samples = hullSamplePoints();
    this.qBase = probe.allocQueries(this.samples.length + 1);
    // state
    this.pos = new THREE.Vector3(mooring.x, 0, mooring.z);
    // heading h (0 = north/-z, +90° = east) is a rotation of -h about +y
    this.quat = new THREE.Quaternion().setFromAxisAngle(up, -mooring.heading);
    this.vel = new THREE.Vector3();
    this.angVel = new THREE.Vector3();
    this.throttle = 0; this.throttleCmd = 0;
    this.rudder = 0;
    this.moored = true;
    this.mooring = mooring;
    this.occupant = null;
    this.thirdPerson = false;
    this.camYaw = 0; this.camPitch = -0.1;
    this.orbitYaw = Math.PI; this.orbitPitch = 0.28; this.orbitDist = 13;
    this.camPos = new THREE.Vector3();
    this.camReady = false;
    // inertia of a box L x B x H with the mass, then a bit more roll inertia
    const L = BOAT.L, B = BOAT.B, H = 1.5;
    this.inertia = new THREE.Vector3(MASS * (B * B + H * H) / 12 * 1.2, MASS * (L * L + B * B) / 12, MASS * (L * L + H * H) / 12);
    // buoyancy area per sample: total supports ~2.3x the weight when fully immersed
    const wsum = this.samples.reduce((a, s) => a + s.w, 0);
    this.areaPerW = MASS * 2.9 / (RHO * 0.55 * wsum);
    this.lastWaterAt = new Float32Array(this.samples.length).fill(0);
    this.speed = 0;
    this.slam = 0;
    this.night = 0;
    this.group.position.copy(this.pos);
    this.group.quaternion.copy(this.quat);
    this.worldMatrix = new THREE.Matrix4();
    this._placeFenders(true);
  }

  get heading() {
    const f = tmpV.set(0, 0, -1).applyQuaternion(this.quat);
    return Math.atan2(f.x, -f.z);
  }

  /** player-facing: can the player at `p` board? */
  canBoard(p) {
    const local = tmpV.copy(p).sub(this.pos).applyQuaternion(tmpQ.copy(this.quat).invert());
    return Math.abs(local.x) < BOAT.B / 2 + 2.2 && Math.abs(local.z) < BOAT.L / 2 + 1.5 && Math.abs(local.y) < 3.5;
  }

  board(player) {
    this.occupant = player;
    player.setMode('boat');
    player.boat = this;
    this.camYaw = 0; this.camPitch = -0.08;
    this.camReady = false;
  }

  boardFromMenu(player) { this.board(player); }

  leave(player) {
    this.occupant = null;
    player.boat = null;
    // step off onto whatever is walkable next to the boat, else into the water
    const side = new THREE.Vector3(BOAT.B / 2 + 1.1, 0, 0.6).applyQuaternion(this.quat);
    const candidates = [side.clone(), side.clone().multiplyScalar(-1), new THREE.Vector3(0, 0, BOAT.L / 2 + 1).applyQuaternion(this.quat)];
    let best = null;
    for (const c of candidates) {
      const x = this.pos.x + c.x, z = this.pos.z + c.z;
      const g = this.collision.groundAt(x, z, this.pos.y + 3);
      const water = this.probe.query(this.qBase + this.samples.length).height;
      if (g.y > water - 0.3 && (!best || g.y > best.y)) best = { x, z, y: g.y };
    }
    const yaw = player.yaw;
    if (best) {
      player.feet.set(best.x, best.y, best.z);
      player.eye.copy(player.feet).y += 1.62;
      player.mode = 'walk';
      player.onGround = true;
    } else {
      const c = candidates[0];
      player.eye.set(this.pos.x + c.x, this.pos.y + 0.1, this.pos.z + c.z);
      player.mode = 'swim';
    }
    player.vel.set(0, 0, 0);
    player.yaw = yaw;
    player.easeY = 0;
    player.emit('mode', player.mode, 'boat');
  }

  _placeFenders(show) { this.model.fenders.visible = show; }

  update(dt, time, input, env) {
    if (dt <= 0) { this._sync(); return; }
    const steps = Math.min(4, Math.ceil(dt / (1 / 120)));
    const h = dt / steps;
    // controls
    if (this.occupant && input) {
      const t = input.axis('KeyS', 'KeyW');
      this.throttleCmd = THREE.MathUtils.clamp(this.throttleCmd + t * dt * 0.7, -0.4, 1);
      if (t === 0 && Math.abs(this.throttleCmd) < 0.04) this.throttleCmd = 0;
      if (input.down('KeyX')) this.throttleCmd *= Math.exp(-dt * 4);
      const r = input.axis('KeyD', 'KeyA');
      this.rudder += ((r * 0.6) - this.rudder) * (1 - Math.exp(-dt * (r ? 2.2 : 3)));
      if (input.pressed('KeyV')) this.thirdPerson = !this.thirdPerson;
      if (Math.abs(this.throttleCmd) > 0.05 && this.moored) { this.moored = false; this._placeFenders(false); }
    } else {
      this.throttleCmd *= Math.exp(-dt * 1.5);
      this.rudder *= Math.exp(-dt * 1.5);
    }
    this.throttle += (this.throttleCmd - this.throttle) * (1 - Math.exp(-dt * 1.6));

    // water heights at the hull samples (latest readback)
    const water = [];
    for (let k = 0; k < this.samples.length; k++) {
      const q = this.probe.query(this.qBase + k);
      if (this.probe.frame > 0 && Number.isFinite(q.height) && q.height > -3.9) this.lastWaterAt[k] = q.height;
      water.push(this.lastWaterAt[k]);
    }
    for (let i = 0; i < steps; i++) this._step(h, water);
    // request the next water samples at the hull points' current xz
    this.worldMatrix.compose(this.pos, this.quat, tmpV2.set(1, 1, 1));
    for (let k = 0; k < this.samples.length; k++) {
      const p = tmpV.copy(this.samples[k].p).applyMatrix4(this.worldMatrix);
      this.probe.setQuery(this.qBase + k, p.x, p.z, 1);
    }
    this.probe.setQuery(this.qBase + this.samples.length, this.pos.x, this.pos.z);

    // wake source: the hull's footprint (draft follows the actual immersion)
    const fwd = tmpV.set(0, 0, -1).applyQuaternion(this.quat);
    this.speed = this.vel.dot(fwd);
    const meanWater = water.reduce((a, b) => a + b, 0) / water.length;
    const draft = THREE.MathUtils.clamp(meanWater - this.pos.y + 0.55, 0, 1.1);
    this.wake?.setHull(0, this.pos.x, this.pos.z, this.heading, draft * 0.55, BOAT.L * 0.95, BOAT.B * 0.9, this.throttle, Math.max(this.speed, 0));

    // bow spray when slamming into waves / pushing hard
    if (this.spray) {
      const bow = tmpV2.set(0, 0.0, -BOAT.L / 2 + 1.1).applyMatrix4(this.worldMatrix);
      const rate = Math.max(this.speed - 2.2, 0) * 90 + this.slam * 900;
      if (rate > 1) {
        const side = new THREE.Vector3(1, 0, 0).applyQuaternion(this.quat);
        for (const sgn of [-1, 1]) {
          this.spray.emit({
            position: bow.clone().addScaledVector(side, sgn * (halfBeam(0.85) + 0.25)), count: rate * dt,
            velocity: side.clone().multiplyScalar(sgn * (1.5 + this.speed * 0.35)).add(new THREE.Vector3(0, 1.6 + this.slam * 3 + this.speed * 0.15, 0)).addScaledVector(this.vel, 0.6),
            spread: 0.9, size: 0.035, life: 1.2,
          });
        }
      }
      // propeller wash churn
      if (Math.abs(this.throttle) > 0.15) {
        const stern = tmpV2.set(0, 0.0, BOAT.L / 2 + 0.3).applyMatrix4(this.worldMatrix);
        this.spray.emit({ position: stern, count: Math.abs(this.throttle) * 40 * dt, velocity: new THREE.Vector3(0, 0.9, 0).addScaledVector(fwd, -1.2 * Math.sign(this.throttle)), spread: 0.6, size: 0.03, life: 0.7 });
      }
    }
    this._sync();
    // lights at night
    const n = env.nightFactor.value;
    this.model.cabLight.intensity = n > 0.25 ? 6 * THREE.MathUtils.smoothstep(n, 0.25, 0.6) : 0;
    this.model.deckLight.intensity = n > 0.25 ? 12 * THREE.MathUtils.smoothstep(n, 0.25, 0.6) : 0;
    const glow = 0.25 + 4 * n;
    this.model.lampMats[0].color.setRGB(1 * glow, 0.95 * glow, 0.86 * glow);
    this.model.lampMats[1].color.setRGB(1 * glow, 0.17 * glow, 0.1 * glow);
    this.model.lampMats[2].color.setRGB(0.1 * glow, 1 * glow, 0.35 * glow);
    // animate helm
    this.model.wheel.rotation.z = -this.rudder * 3.2;
    this.model.lever.rotation.x = -this.throttle * 0.8;
  }

  _step(h, water) {
    const force = new THREE.Vector3();
    const torque = new THREE.Vector3();
    const R = new THREE.Matrix4().makeRotationFromQuaternion(this.quat);
    const invQ = this.quat.clone().invert();
    let wetCount = 0, slam = 0;
    const addForceAt = (f, p) => {
      force.add(f);
      torque.add(tmpV.copy(p).sub(this.pos).cross(f));
    };
    // gravity at the centre of mass: aft of midships (engine, wheelhouse)
    addForceAt(new THREE.Vector3(0, -MASS * G, 0), CG.clone().applyMatrix4(R).add(this.pos));
    for (let k = 0; k < this.samples.length; k++) {
      const s = this.samples[k];
      const p = s.p.clone().applyMatrix4(R).add(this.pos);
      const depth = water[k] - p.y;
      if (depth <= 0) continue;
      wetCount++;
      const A = this.areaPerW * s.w;
      const imm = Math.min(depth, 1.1);
      // point velocity
      const r = p.clone().sub(this.pos);
      const vp = this.vel.clone().add(this.angVel.clone().cross(r));
      const fb = RHO * G * A * imm;
      // heave damping (radiation + viscous), stronger when moving down into the water
      const damp = -vp.y * A * RHO * (vp.y < 0 ? 1.7 : 1.0);
      if (vp.y < -2.2) slam = Math.max(slam, -vp.y - 2.2);
      addForceAt(new THREE.Vector3(0, fb + damp, 0), p);
    }
    // hydrodynamic drag in the boat frame (quadratic; lateral >> longitudinal)
    const wetFrac = wetCount / this.samples.length;
    const vl = this.vel.clone().applyQuaternion(invQ);
    const dragL = new THREE.Vector3(
      -vl.x * Math.abs(vl.x) * 2600 - vl.x * 900,
      0,
      -vl.z * Math.abs(vl.z) * 105 - vl.z * 60,
    ).multiplyScalar(wetFrac);
    force.add(dragL.applyQuaternion(this.quat));
    // propeller thrust below the transom, rudder side force
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(this.quat);
    const side = new THREE.Vector3(1, 0, 0).applyQuaternion(this.quat);
    const prop = new THREE.Vector3(0, -0.45, BOAT.L / 2 - 0.4).applyMatrix4(R).add(this.pos);
    const thrust = this.throttle * (this.throttle > 0 ? 7200 : 3200) * wetFrac;
    addForceAt(fwd.clone().multiplyScalar(thrust), prop);
    const flow = Math.max(-vl.z, 0) + Math.abs(this.throttle) * 3.2;   // prop wash over the rudder
    const rudderF = this.rudder * flow * flow * 55 * wetFrac;
    // helm to port (A) swings the stern to starboard, the bow to port
    addForceAt(side.clone().multiplyScalar(rudderF), prop);
    // dynamic lift on the forward bottom at speed: the bow rises and the
    // stern squats (semi-displacement hull)
    const fwdSpeed = Math.max(-vl.z, 0);
    const lift = fwdSpeed * fwdSpeed * 55 * wetFrac;
    addForceAt(new THREE.Vector3(0, lift, 0), new THREE.Vector3(0, -0.5, -BOAT.L / 2 + 1.6).applyMatrix4(R).add(this.pos));
    addForceAt(new THREE.Vector3(0, -lift * 0.55, 0), new THREE.Vector3(0, -0.5, BOAT.L / 2 - 0.6).applyMatrix4(R).add(this.pos));
    // mooring lines: soft springs to the dock while moored
    if (this.moored) {
      const m = this.mooring;
      const target = new THREE.Vector3(m.x, this.pos.y, m.z);
      const d = target.sub(this.pos);
      force.add(d.multiplyScalar(2600)).add(new THREE.Vector3(this.vel.x, 0, this.vel.z).multiplyScalar(-2200));
      const dh = Math.atan2(Math.sin(m.heading - this.heading), Math.cos(m.heading - this.heading));
      torque.y += -dh * 9000 - this.angVel.y * 7000;
    }
    // grounding: keel points below the seabed push up and scrape
    for (const s of [this.samples[0], this.samples[9], this.samples[15]]) {
      const p = s.p.clone().applyMatrix4(R).add(this.pos);
      const bed = this.collision.terrainHeight(p.x, p.z);
      if (p.y < bed) {
        const pen = bed - p.y;
        addForceAt(new THREE.Vector3(0, pen * 90000, 0), p);
        force.add(new THREE.Vector3(this.vel.x, 0, this.vel.z).multiplyScalar(-4000));
      }
    }
    // integrate (semi-implicit Euler)
    this.vel.addScaledVector(force, h / MASS);
    // angular: body-frame inertia
    const tl = torque.clone().applyQuaternion(invQ);
    const wl = this.angVel.clone().applyQuaternion(invQ);
    wl.x += tl.x / this.inertia.x * h;
    wl.y += tl.y / this.inertia.y * h;
    wl.z += tl.z / this.inertia.z * h;
    // rotational damping (roll damps least)
    wl.x *= Math.exp(-h * 1.2 * (0.3 + wetFrac));
    wl.y *= Math.exp(-h * 1.6 * (0.3 + wetFrac));
    wl.z *= Math.exp(-h * 0.8 * (0.3 + wetFrac));
    this.angVel.copy(wl.applyQuaternion(this.quat));
    this.pos.addScaledVector(this.vel, h);
    const w = this.angVel;
    const dq = new THREE.Quaternion(w.x * h * 0.5, w.y * h * 0.5, w.z * h * 0.5, 0).multiply(this.quat);
    this.quat.x += dq.x; this.quat.y += dq.y; this.quat.z += dq.z; this.quat.w += dq.w;
    this.quat.normalize();
    this.slam = Math.max(this.slam * Math.exp(-h * 8), slam);
  }

  _sync() {
    this.group.position.copy(this.pos);
    this.group.quaternion.copy(this.quat);
    this.group.updateMatrixWorld(true);
  }

  /** camera while aboard: helm view or orbit */
  updateCamera(camera, player, dt, input) {
    if (input.locked) {
      if (this.thirdPerson) {
        this.orbitYaw -= input.mouseDX * player.sensitivity;
        this.orbitPitch = THREE.MathUtils.clamp(this.orbitPitch + input.mouseDY * player.sensitivity, -0.15, 1.2);
        this.orbitDist = THREE.MathUtils.clamp(this.orbitDist + input.wheel * 1.2, 6, 40);
      } else {
        this.camYaw = THREE.MathUtils.clamp(this.camYaw - input.mouseDX * player.sensitivity, -2.4, 2.4);
        this.camPitch = THREE.MathUtils.clamp(this.camPitch - input.mouseDY * player.sensitivity, -1.2, 1.1);
      }
    }
    if (this.thirdPerson) {
      // orbit around the boat, yaw relative to the boat's heading
      const hdg = this.heading;
      const yaw = hdg + this.orbitYaw;
      const target = this.pos.clone().add(new THREE.Vector3(0, 1.6, 0));
      const off = new THREE.Vector3(Math.sin(yaw) * Math.cos(this.orbitPitch), Math.sin(this.orbitPitch), -Math.cos(yaw) * Math.cos(this.orbitPitch)).multiplyScalar(this.orbitDist);
      const want = target.clone().add(off);
      if (!this.camReady) { this.camPos.copy(want); this.camReady = true; }
      this.camPos.lerp(want, 1 - Math.exp(-dt * 6));
      const minY = Math.max(this.collision.terrainHeight(this.camPos.x, this.camPos.z), 0) + 0.8;
      if (this.camPos.y < minY) this.camPos.y = minY;
      camera.position.copy(this.camPos);
      camera.up.set(0, 1, 0);
      camera.lookAt(target);
    } else {
      // helm seat: rides with the hull (roll and pitch included)
      const eye = this.model.helmEye.clone().applyMatrix4(this.group.matrixWorld);
      camera.position.copy(eye);
      const look = new THREE.Quaternion().setFromEuler(new THREE.Euler(this.camPitch, this.camYaw, 0, 'YXZ'));
      // keep the horizon a little steadier than the hull (the head compensates)
      const hull = this.quat.clone();
      const level = new THREE.Quaternion().setFromAxisAngle(up, -this.heading);
      hull.slerp(level, 0.45);
      camera.quaternion.copy(hull).multiply(look);
    }
  }
}

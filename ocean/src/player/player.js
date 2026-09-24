// First-person player: walking, swimming, free flight, and a seat in the boat.
//
//  walk  capsule on the terrain + walkable props, gravity, jumping, wading
//        slows you down; deep water hands over to swimming without a jump
//        in eye height (every discontinuity is eased out, see _ease)
//  swim  free 3D swimming. Near the surface you float and ride the waves;
//        once you dive you stay at the depth you chose (neutral buoyancy)
//  fly   noclip. Leaving it drops you with gravity from where you are
//  boat  the boat owns the camera (1st / 3rd person)

import * as THREE from 'three/webgpu';

const EYE = 1.62;           // eye above the feet when standing
const RADIUS = 0.3;
const HEIGHT = 1.78;
const GRAVITY = 9.81;
const SWIM_DEPTH = 1.3;     // water depth where wading turns into swimming
const SURFACE_EYE = 0.07;   // eye height above the water when floating

const tmpV = new THREE.Vector3();
const tmpF = new THREE.Vector3();
const tmpR = new THREE.Vector3();

export class Player {
  constructor({ camera, input, collision, probe, queryIndex = 0 }) {
    this.camera = camera;
    this.input = input;
    this.collision = collision;
    this.probe = probe;
    this.qi = queryIndex;
    this.mode = 'walk';
    this.feet = new THREE.Vector3();
    this.eye = new THREE.Vector3();
    this.vel = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = 0;
    this.onGround = false;
    this.groundSurface = null;
    this.easeY = 0;           // eased-out vertical discontinuities
    this.stepPhase = 0;
    this.bob = new THREE.Vector3();
    this.bobAmp = 0;
    this.sensitivity = 0.0021;
    this.walkSpeed = 1.9;
    this.runSpeed = 4.6;
    this.swimSpeed = 1.25;
    this.flySpeed = 9;
    this.boat = null;          // set by the boat system
    this.thirdPerson = false;
    this.listeners = {};
    this.lastWaterH = 0;
    this.headUnderwater = false;
  }

  on(ev, fn) { (this.listeners[ev] ||= []).push(fn); }
  emit(ev, ...a) { for (const f of this.listeners[ev] || []) f(...a); }

  /** place the player standing at (x, z), looking along yaw (deg, 0 = north) */
  spawn(x, z, yawDeg = 0, pitchDeg = 0) {
    const g = this.collision.groundAt(x, z, Infinity);
    this.feet.set(x, g.y, z);
    this.vel.set(0, 0, 0);
    this.mode = 'walk';
    this.onGround = true;
    this.yaw = THREE.MathUtils.degToRad(yawDeg);
    this.pitch = THREE.MathUtils.degToRad(pitchDeg);
    this.eye.copy(this.feet).y += EYE;
    this.easeY = 0;
  }

  /** place the camera freely (debug / fly) */
  setView(x, y, z, yawDeg, pitchDeg) {
    this.mode = 'fly';
    this.eye.set(x, y, z);
    this.vel.set(0, 0, 0);
    this.yaw = THREE.MathUtils.degToRad(yawDeg);
    this.pitch = THREE.MathUtils.degToRad(pitchDeg);
    this.easeY = 0;
  }

  waterHeight() {
    const q = this.probe.query(this.qi);
    if (this.probe.frame > 0 && Number.isFinite(q.height)) this.lastWaterH = q.height;
    return this.lastWaterH;
  }

  forward(out = tmpF) {
    const cp = Math.cos(this.pitch);
    return out.set(Math.sin(this.yaw) * cp, Math.sin(this.pitch), -Math.cos(this.yaw) * cp);
  }

  flatForward(out = tmpF) { return out.set(Math.sin(this.yaw), 0, -Math.cos(this.yaw)); }
  right(out = tmpR) { return out.set(Math.cos(this.yaw), 0, Math.sin(this.yaw)); }

  _ease(oldEyeY, newEyeY) { this.easeY += oldEyeY - newEyeY; }

  setMode(mode) {
    if (mode === this.mode) return;
    const prev = this.mode;
    const oldEye = this.eye.y;
    if (mode === 'walk') {
      this.feet.copy(this.eye).y -= EYE;
      this.onGround = false;
      if (prev === 'fly') this.vel.set(this.vel.x * 0.3, 0, this.vel.z * 0.3);
    } else if (mode === 'swim') {
      if (prev === 'walk') this.eye.copy(this.feet).y += EYE;
    } else if (mode === 'fly') {
      this.vel.set(0, 0, 0);
    }
    this.mode = mode;
    if (mode !== 'fly') this._ease(oldEye, this.eye.y);
    this.emit('mode', mode, prev);
  }

  update(dt) {
    dt = Math.min(dt, 0.05);
    const inp = this.input;
    if (inp.locked && this.mode !== 'boat') {
      this.yaw += inp.mouseDX * this.sensitivity;
      this.pitch -= inp.mouseDY * this.sensitivity;
      this.pitch = THREE.MathUtils.clamp(this.pitch, -1.53, 1.53);
    }
    if (this.mode === 'boat') {
      this.boat?.updateCamera(this.camera, this, dt, inp);
      this.eye.copy(this.camera.position);
      return;
    }
    if (inp.pressed('KeyG')) this.setMode(this.mode === 'fly' ? 'walk' : 'fly');

    // the probe query follows the body
    const qx = this.mode === 'walk' ? this.feet.x : this.eye.x;
    const qz = this.mode === 'walk' ? this.feet.z : this.eye.z;
    this.probe.setQuery(this.qi, qx, qz);

    if (this.mode === 'walk') this._walk(dt);
    else if (this.mode === 'swim') this._swim(dt);
    else if (this.mode === 'fly') this._fly(dt);

    this.easeY *= Math.exp(-dt / 0.11);
    if (Math.abs(this.easeY) < 1e-4) this.easeY = 0;
    if (this.mode !== 'boat') this._applyCamera(dt);
  }

  _wish(out) {
    const inp = this.input;
    const f = inp.axis('KeyS', 'KeyW'), s = inp.axis('KeyA', 'KeyD');
    const fwd = this.flatForward(tmpF), rgt = this.right(tmpR);
    out.set(0, 0, 0).addScaledVector(fwd, f).addScaledVector(rgt, s);
    if (out.lengthSq() > 1) out.normalize();
    return out;
  }

  _walk(dt) {
    const inp = this.input;
    const col = this.collision;
    const wish = this._wish(tmpV);
    const waterH = this.waterHeight();
    const ground = col.groundAt(this.feet.x, this.feet.z, this.feet.y);
    const wade = Math.max(0, waterH - Math.max(ground.y, this.feet.y));
    const wadeSlow = 1 - 0.55 * THREE.MathUtils.smoothstep(wade, 0.25, 1.1);
    const speed = (inp.down('ShiftLeft') || inp.down('ShiftRight') ? this.runSpeed : this.walkSpeed) * wadeSlow;
    const accel = this.onGround ? 11 : 1.8;
    const k = 1 - Math.exp(-accel * dt);
    this.vel.x += (wish.x * speed - this.vel.x) * k;
    this.vel.z += (wish.z * speed - this.vel.z) * k;
    if (this.onGround && inp.pressed('Space') && wade < 0.9) {
      this.vel.y = 4.3;
      this.onGround = false;
      this.emit('jump');
    }
    // gravity, with buoyancy/drag once the body is in water
    const sub = THREE.MathUtils.clamp((waterH - this.feet.y) / HEIGHT, 0, 1);
    this.vel.y -= GRAVITY * (1 - sub * 0.9) * dt;
    if (sub > 0) this.vel.y *= Math.exp(-dt * 3 * sub);

    const oldY = this.feet.y;
    this.feet.x += this.vel.x * dt;
    this.feet.z += this.vel.z * dt;
    this.feet.y += this.vel.y * dt;
    col.resolve(this.feet, RADIUS, this.feet.y, this.feet.y + HEIGHT);

    const g = col.groundAt(this.feet.x, this.feet.z, Math.max(this.feet.y, oldY));
    const wasGround = this.onGround;
    if (this.feet.y <= g.y + 0.02 && this.vel.y <= 0.01) {
      const stepUp = g.y - this.feet.y;
      if (wasGround && stepUp > 0.03) this._ease(this.feet.y, g.y);  // smooth stairs / deck edges
      if (!wasGround && this.vel.y < -3) this.emit('land', -this.vel.y, g.surface);
      this.feet.y = g.y;
      this.vel.y = 0;
      this.onGround = true;
      this.groundSurface = g.surface;
    } else if (wasGround && this.feet.y - g.y < 0.35 && this.vel.y <= 0) {
      // walking down a slope or off a low step: stick to the ground
      this._ease(this.feet.y, g.y);
      this.feet.y = g.y;
      this.vel.y = 0;
      this.groundSurface = g.surface;
    } else {
      this.onGround = false;
    }
    const ceil = col.ceilingAt(this.feet.x, this.feet.z, this.feet.y + 0.5);
    if (this.feet.y + HEIGHT > ceil) { this.feet.y = ceil - HEIGHT; this.vel.y = Math.min(this.vel.y, 0); }

    // head bob + footsteps while moving on the ground
    const hs = Math.hypot(this.vel.x, this.vel.z);
    const moving = this.onGround && hs > 0.3;
    this.bobAmp += ((moving ? 1 : 0) - this.bobAmp) * (1 - Math.exp(-dt * 6));
    if (moving) {
      const prev = this.stepPhase;
      this.stepPhase += hs * dt / 0.72;           // one step per ~0.72 m
      if (Math.floor(prev) !== Math.floor(this.stepPhase)) {
        this.emit('step', { speed: hs, surface: this.groundSurface, wade, x: this.feet.x, z: this.feet.z });
      }
    }
    const ph = this.stepPhase * Math.PI;
    const amp = Math.min(hs / 4.6, 1) * 0.035 + 0.012;
    this.bob.set(Math.cos(ph) * amp * 0.45 * this.bobAmp, -Math.abs(Math.sin(ph)) * amp * this.bobAmp, 0);

    this.eye.copy(this.feet).y += EYE;
    // deep enough to float: hand over to swimming
    const depth = waterH - g.y;
    if (depth > SWIM_DEPTH && this.feet.y < waterH - SWIM_DEPTH * 0.8) this.setMode('swim');
  }

  _swim(dt) {
    const inp = this.input;
    const col = this.collision;
    const waterH = this.waterHeight();
    const s = this.eye.y - waterH;                 // eye above the water
    const fast = inp.down('ShiftLeft') || inp.down('ShiftRight');
    const speed = this.swimSpeed * (fast ? 2 : 1);
    const f = inp.axis('KeyS', 'KeyW'), st = inp.axis('KeyA', 'KeyD');
    const up = (inp.down('Space') ? 1 : 0) - (inp.down('KeyC') || inp.down('ControlLeft') ? 1 : 0);
    const atSurface = s > -0.5;
    const diving = this.pitch < -0.45 && f > 0;
    // underwater (or diving) you swim where you look; at the surface you paddle flat
    const fwd = (atSurface && !diving) ? this.flatForward(tmpF) : this.forward(tmpF);
    const wish = tmpV.set(0, 0, 0).addScaledVector(fwd, f).addScaledVector(this.right(tmpR), st);
    wish.y += up;
    if (wish.lengthSq() > 1) wish.normalize();
    const k = 1 - Math.exp(-3.2 * dt);
    this.vel.x += (wish.x * speed - this.vel.x) * k;
    this.vel.z += (wish.z * speed - this.vel.z) * k;
    this.vel.y += (wish.y * speed - this.vel.y) * k;
    // float: ride the waves while near the surface and not heading down
    if (atSurface && up >= 0 && !diving) {
      const target = waterH + SURFACE_EYE;
      const spring = 18, damp = 7;
      this.vel.y += ((target - this.eye.y) * spring - this.vel.y * damp) * dt;
      if (up > 0) this.vel.y = Math.min(this.vel.y, 0.8);
    }
    // out of the water (jumped off something / wave trough): fall back in
    if (s > 0.35) this.vel.y -= GRAVITY * dt;
    this.eye.addScaledVector(this.vel, dt);
    col.resolve(this.eye, 0.35, this.eye.y - 1.2, this.eye.y + 0.2, 0.2);
    const g = col.groundAt(this.eye.x, this.eye.z, this.eye.y);
    const minEye = g.y + 0.4;
    if (this.eye.y < minEye) { this.eye.y = minEye; this.vel.y = Math.max(this.vel.y, 0); }
    // feet reach the bottom in shallow water: stand up
    const depth = waterH - g.y;
    if (depth < SWIM_DEPTH - 0.1 && this.eye.y - g.y < EYE + 0.1) {
      this.feet.set(this.eye.x, g.y, this.eye.z);
      this.vel.y = 0;
      this.onGround = true;
      const oldEye = this.eye.y;
      this.mode = 'walk';
      this.eye.copy(this.feet).y += EYE;
      this._ease(oldEye, this.eye.y);
      this.emit('mode', 'walk', 'swim');
    }
    // gentle sway while swimming
    this.stepPhase += dt * (0.8 + Math.hypot(this.vel.x, this.vel.z) * 0.8);
    this.bob.set(Math.sin(this.stepPhase * 2.1) * 0.02, Math.sin(this.stepPhase * 1.3) * 0.015, 0);
    this.bobAmp = 0;
  }

  _fly(dt) {
    const inp = this.input;
    const fast = inp.down('ShiftLeft') || inp.down('ShiftRight');
    const speed = this.flySpeed * (fast ? 5 : 1) * (inp.down('AltLeft') ? 0.15 : 1);
    const f = inp.axis('KeyS', 'KeyW'), st = inp.axis('KeyA', 'KeyD');
    const up = (inp.down('Space') || inp.down('KeyE') ? 1 : 0) - (inp.down('KeyC') || inp.down('KeyQ') || inp.down('ControlLeft') ? 1 : 0);
    const wish = tmpV.set(0, 0, 0).addScaledVector(this.forward(tmpF), f).addScaledVector(this.right(tmpR), st);
    wish.y += up;
    const k = 1 - Math.exp(-8 * dt);
    this.vel.x += (wish.x * speed - this.vel.x) * k;
    this.vel.y += (wish.y * speed - this.vel.y) * k;
    this.vel.z += (wish.z * speed - this.vel.z) * k;
    this.eye.addScaledVector(this.vel, dt);
    this.bob.set(0, 0, 0);
  }

  _applyCamera(dt) {
    const cam = this.camera;
    const r = this.right(tmpR);
    cam.position.copy(this.eye);
    cam.position.y += this.easeY + this.bob.y;
    cam.position.addScaledVector(r, this.bob.x);
    cam.rotation.set(this.pitch, -this.yaw, 0, 'YXZ');
    this.headUnderwater = cam.position.y < this.lastWaterH;
  }
}

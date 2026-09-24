// Hand-held torch: a spot light that trails the view a little, plus the
// uniforms the composite uses to draw its beam through the water.

import * as THREE from 'three/webgpu';
import { env } from '../env.js';

const tmp = new THREE.Vector3();

export class Flashlight {
  constructor(scene) {
    this.light = new THREE.SpotLight(0xfff0dc, 0, 60, 0.36, 0.6, 1.7);
    this.light.name = 'flashlight';
    this.light.castShadow = false;   // at the eye its shadows are hidden anyway
    scene.add(this.light, this.light.target);
    this.on = false;
    this.power = 16;
    this.level = 0;
    this.dir = new THREE.Vector3(0, 0, -1);
  }

  toggle(force) {
    this.on = force === undefined ? !this.on : !!force;
    return this.on;
  }

  update(camera, dt) {
    const target = this.on ? 1 : 0;
    this.level += (target - this.level) * (1 - Math.exp(-dt * 18));
    if (this.level < 0.002) this.level = 0;
    const fwd = camera.getWorldDirection(tmp);
    // the beam lags the view slightly, like a torch held in a hand
    this.dir.lerp(fwd, 1 - Math.exp(-dt * 14)).normalize();
    const right = new THREE.Vector3().crossVectors(fwd, camera.up).normalize();
    const pos = this.light.position.copy(camera.position).addScaledVector(right, 0.16).add(new THREE.Vector3(0, -0.12, 0));
    this.light.target.position.copy(pos).addScaledVector(this.dir, 10);
    this.light.intensity = this.power * this.level;
    this.light.visible = this.level > 0;
    env.flashlight.value = this.level > 0 ? 1 : 0;
    env.flashlightPos.value.copy(pos);
    env.flashlightDir.value.copy(this.dir);
  }
}

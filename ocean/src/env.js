// Shared environment state (CPU values + TSL uniforms) used across systems.

import * as THREE from 'three/webgpu';
import { uniform } from 'three/tsl';

export const env = {
  time: uniform(0),
  dt: uniform(0.016),
  sunDir: uniform(new THREE.Vector3(0, 0.3, -1).normalize()),   // toward the main light
  sunColor: uniform(new THREE.Color(1, 1, 1)),                   // irradiance (includes E, transmittance)
  skyIrradiance: uniform(new THREE.Color(0.3, 0.4, 0.5)),
  sunDiskDir: uniform(new THREE.Vector3(0, 0.3, -1)),

  // water optics, per metre (clear tropical coastal water)
  waterAbsorption: uniform(new THREE.Vector3(0.45, 0.068, 0.024)),   // a(λ): R 650, G 550, B 450 nm
  waterScattering: uniform(new THREE.Vector3(0.035, 0.045, 0.06)),   // b(λ): total scattering (beam attenuation)
  waterBackscatter: uniform(new THREE.Vector3(0.0006, 0.0012, 0.0028)), // molecular b_b(λ)
  particleBackscatter: uniform(0.0018),  // broadband (grey) particulate backscatter b_bp
  waterLevel: uniform(0),

  cameraUnderwater: uniform(0),
  cameraDepth: uniform(0),              // metres below the local surface (>0 underwater)
  windDir: uniform(new THREE.Vector2(0.5, 0.86)),
  windSpeed: uniform(7),
  exposure: uniform(1),
  nightFactor: uniform(0),
  flashlight: uniform(0),               // 0/1 on
  flashlightPos: uniform(new THREE.Vector3()),
  flashlightDir: uniform(new THREE.Vector3(0, 0, -1)),
};

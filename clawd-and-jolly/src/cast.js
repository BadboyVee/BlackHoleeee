// Where everyone stands in the moss bowl (world coordinates)
import * as THREE from 'three';
import { BOWL } from './desk.js';

export const JOLLY_SPOT = new THREE.Vector3(BOWL.x + 2.2, 0, BOWL.z + 1.0);
export const JOLLY_YAW = -1.0;
export const CLAWD_MEET = new THREE.Vector3(BOWL.x - 2.9, 0, BOWL.z + 1.4);
export const PLANT_SPOT = new THREE.Vector3(BOWL.x - 0.5, 0, BOWL.z - 1.3);

// Jolly asleep: closed eyes, slow breathing, head nodding forward
export function sleepingJolly(jolly, t, k = 1) {
  const P = jolly.pose;
  P.blink = k;
  P.squash = 0.035 * Math.sin(t * Math.PI * 2 / 3.4) * k;
  P.lean = 0.12 * k + 0.02 * Math.sin(t * Math.PI * 2 / 3.4) * k;
  P.tilt = 0.08 * k;
}

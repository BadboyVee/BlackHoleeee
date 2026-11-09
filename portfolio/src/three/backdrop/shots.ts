/**
 * Camera "shots" around the black hole, one per page section. Scrolling into a
 * section blends the camera from the previous shot to that section's shot, so
 * reading the page is a slow orbit that ends with a dive towards the horizon.
 *
 * dist   distance from the hole (Schwarzschild radii)
 * elev   height above the disk plane (degrees); low = the classic edge-on look
 * az     orbit angle (degrees)
 * roll   camera roll (degrees)
 * shiftX horizontal position of the hole, -1 (left edge) .. 1 (right edge)
 * shiftY vertical position, -1 (bottom) .. 1 (top)
 * dim    0 = full brightness, 1 = hidden behind the page colour
 */
export type Shot = {
  dist: number
  elev: number
  az: number
  roll: number
  shiftX: number
  shiftY: number
  fov: number
  exposure: number
  disk: number
  dim: number
}

export type ShotName = 'hero' | 'about' | 'work' | 'toolkit' | 'process' | 'experience' | 'contact'

const base: Shot = { dist: 22, elev: 7, az: 0, roll: -10, shiftX: 0.4, shiftY: 0.06, fov: 46, exposure: 1.15, disk: 1, dim: 0 }

export const desktopShots: Record<ShotName, Shot> = {
  hero: base,
  about: { ...base, dist: 27, elev: 19, az: 38, roll: -3, shiftX: -0.5, shiftY: 0.02, exposure: 1, dim: 0.42 },
  work: { ...base, dist: 36, elev: 30, az: 74, roll: 5, shiftX: -0.15, shiftY: 0.38, exposure: 0.95, dim: 0.74 },
  toolkit: { ...base, dist: 25, elev: 56, az: 112, roll: 0, shiftX: 0.0, shiftY: 0.05, exposure: 1, dim: 0.5 },
  process: { ...base, dist: 31, elev: 34, az: 150, roll: -7, shiftX: 0.45, shiftY: -0.05, exposure: 1, dim: 0.66 },
  experience: { ...base, dist: 26, elev: 15, az: 192, roll: -9, shiftX: -0.42, shiftY: 0.08, exposure: 1.05, dim: 0.5 },
  contact: { ...base, dist: 15.5, elev: 4.5, az: 238, roll: 8, shiftX: 0, shiftY: 0.1, fov: 52, exposure: 1.3, dim: 0.06 },
}

const mobileBase: Shot = { ...base, dist: 26, roll: -14, shiftX: 0, shiftY: 0.3, fov: 58 }

export const mobileShots: Record<ShotName, Shot> = {
  hero: mobileBase,
  about: { ...mobileBase, dist: 30, elev: 20, az: 38, roll: -4, shiftY: -0.35, dim: 0.5 },
  work: { ...mobileBase, dist: 38, elev: 30, az: 74, roll: 5, shiftY: 0.45, dim: 0.78 },
  toolkit: { ...mobileBase, dist: 28, elev: 56, az: 112, roll: 0, shiftY: 0.0, dim: 0.55 },
  process: { ...mobileBase, dist: 34, elev: 34, az: 150, roll: -7, shiftY: -0.3, dim: 0.7 },
  experience: { ...mobileBase, dist: 30, elev: 15, az: 192, roll: -9, shiftY: 0.3, dim: 0.55 },
  contact: { ...mobileBase, dist: 17, elev: 4.5, az: 238, roll: 8, shiftY: 0.18, fov: 62, exposure: 1.3, dim: 0.08 },
}

/** Target shot, written by the scroll timeline. */
export const target: Shot = { ...base }

/** Extra state for the intro and the pointer. */
export const extras = {
  /** 0 → 1 when the preloader lifts: the camera rushes in and the disk ignites. */
  intro: 0,
  pointerX: 0,
  pointerY: 0,
}

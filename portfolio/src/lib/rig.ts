// The scroll-driven camera path.
//
// Each keyframe pins a camera pose to a place in the page ("when the middle of
// #about is in the middle of the screen, be here"). The positions are measured
// from the real DOM, so the 3D journey stays glued to the layout at any screen
// size. Between keyframes the pose is blended; CameraRig then damps toward it.

const DEG = Math.PI / 180

/** Where the orrery model floats, in black-hole radii. */
export const ORRERY_POSITION: [number, number, number] = [44, 10, -30]

export interface Pose {
  /** Point the camera orbits and looks at. */
  fx: number
  fy: number
  fz: number
  /** Orbit distance, elevation above the disk plane and azimuth (radians). */
  r: number
  elev: number
  az: number
  /** Camera roll (radians) and vertical field of view (degrees). */
  roll: number
  fov: number
  /** Screen-space shift of the subject: 1 = half a viewport right / up. */
  sx: number
  sy: number
  /** Brightness of the accretion disk and of the star field. */
  disk: number
  stars: number
}

interface Key {
  /** CSS selector of the section this keyframe is tied to. */
  el: string
  /** 0 = the section's top edge, 1 = its bottom edge. */
  at: number
  /** Where on screen that edge should be: 0 = top of the viewport, 1 = bottom. */
  anchor: number
  pose: Pose
  /** Overrides for portrait / narrow screens. */
  narrow?: Partial<Pose>
}

const [ox, oy, oz] = ORRERY_POSITION
const orreryAz = Math.atan2(ox, oz)

const base: Pose = { fx: 0, fy: 0, fz: 0, r: 25, elev: 0, az: 0, roll: 0, fov: 34, sx: 0, sy: 0, disk: 1, stars: 1 }
const pose = (p: Partial<Pose>): Pose => ({ ...base, ...p })

const KEYS: Key[] = [
  // Hero — the classic edge-on view: disk arching over and under the shadow.
  {
    el: '#hero',
    at: 0,
    anchor: 0,
    pose: pose({ r: 24, elev: 6.5 * DEG, az: -14 * DEG, roll: -11 * DEG, sx: 0.3, sy: 0.06 }),
    narrow: { r: 40, sx: 0, sy: 0.22 },
  },
  // Leaving the hero — rise above the disk, push the hole to the right.
  {
    el: '#hero',
    at: 1,
    anchor: 0,
    pose: pose({ r: 31, elev: 19 * DEG, az: 16 * DEG, roll: -17 * DEG, sx: 0.52, sy: 0.02, disk: 0.9 }),
    narrow: { r: 52, sx: 0, sy: 0.4, disk: 0.6 },
  },
  // About — a calm three-quarter view while the statement reads.
  {
    el: '#about',
    at: 0.55,
    anchor: 0.5,
    pose: pose({ r: 34, elev: 31 * DEG, az: 52 * DEG, roll: -8 * DEG, sx: 0.56, sy: -0.1, disk: 0.75 }),
    narrow: { r: 60, sx: 0, sy: -0.45, disk: 0.5 },
  },
  // Work — drift out into open space; the hole falls away behind the gallery.
  {
    el: '#work',
    at: 0,
    anchor: 0,
    pose: pose({ fx: ox * 0.25, fy: oy * 0.25, fz: oz * 0.25, r: 46, elev: 22 * DEG, az: 88 * DEG, roll: 4 * DEG, sx: 0.2, sy: -0.2, disk: 0.55, stars: 1.25 }),
    narrow: { r: 70, sx: 0 },
  },
  {
    el: '#work',
    at: 1,
    anchor: 1,
    pose: pose({ fx: ox, fy: oy, fz: oz, r: 26, elev: 16 * DEG, az: orreryAz + 4 * DEG, roll: 6 * DEG, sx: -0.3, sy: 0, disk: 0.7, stars: 1.2 }),
    narrow: { r: 30, sx: 0, sy: 0.3 },
  },
  // Stack — close on the orrery, the hole a small ember far behind it.
  {
    el: '#stack',
    at: 0.5,
    anchor: 0.5,
    pose: pose({ fx: ox, fy: oy, fz: oz, r: 11.5, elev: 13 * DEG, az: orreryAz + 30 * DEG, roll: -4 * DEG, fov: 36, sx: -0.48, sy: 0.02, disk: 0.85 }),
    narrow: { r: 15, sx: 0, sy: 0.52 },
  },
  {
    el: '#approach',
    at: 0,
    anchor: 0,
    pose: pose({ fx: ox, fy: oy, fz: oz, r: 10, elev: 20 * DEG, az: orreryAz + 62 * DEG, roll: -8 * DEG, fov: 36, sx: -0.5, sy: 0.3, disk: 0.85 }),
    narrow: { r: 14, sx: 0, sy: 0.9 },
  },
  // While the light "approach" sheet hides the canvas, cut back to the hole…
  {
    el: '#approach',
    at: 1,
    anchor: 1,
    pose: pose({ r: 40, elev: 44 * DEG, az: -40 * DEG, roll: 24 * DEG, fov: 40, disk: 0.9 }),
    narrow: { r: 62 },
  },
  // …and fall straight in: the shadow swallows the screen behind the CTA.
  {
    el: '#contact',
    at: 0.5,
    anchor: 0.5,
    pose: pose({ r: 8.8, elev: 84 * DEG, az: 30 * DEG, roll: 0, fov: 48, disk: 1.05, stars: 0.8 }),
    narrow: { r: 17.5 },
  },
  {
    el: '#contact',
    at: 1,
    anchor: 1,
    pose: pose({ r: 7.9, elev: 86 * DEG, az: 62 * DEG, roll: 0, fov: 48, disk: 1.05, stars: 0.8 }),
    narrow: { r: 16 },
  },
]

interface Measured {
  y: number
  pose: Pose
}

let measured: Measured[] = []
const POSE_FIELDS = Object.keys(base) as (keyof Pose)[]

/** Re-read section positions from the DOM. Call after layout changes. */
export function measureRig() {
  const vh = window.innerHeight
  const narrow = window.innerWidth / vh < 0.9
  const scrollY = window.scrollY
  const next: Measured[] = []

  for (const key of KEYS) {
    const el = document.querySelector<HTMLElement>(key.el)
    if (!el) continue
    const rect = el.getBoundingClientRect()
    const y = rect.top + scrollY + key.at * rect.height - key.anchor * vh
    next.push({ y, pose: narrow && key.narrow ? { ...key.pose, ...key.narrow } : key.pose })
  }

  // Keyframes are authored in page order; keep them monotonic even if a short
  // section makes two anchors cross.
  for (let i = 1; i < next.length; i++) next[i].y = Math.max(next[i].y, next[i - 1].y + 1)
  measured = next
}

/** Write the pose for a given scroll position into `out`. */
export function samplePose(scroll: number, out: Pose) {
  if (measured.length === 0) {
    Object.assign(out, KEYS[0].pose)
    return out
  }

  let i = 0
  while (i < measured.length - 2 && scroll > measured[i + 1].y) i++
  const a = measured[i]
  const b = measured[Math.min(i + 1, measured.length - 1)]

  let t = b.y > a.y ? (scroll - a.y) / (b.y - a.y) : 0
  t = Math.min(1, Math.max(0, t))
  // Mostly eased, a little linear: settles into each scene without stalling.
  const eased = t * t * (3 - 2 * t)
  t = eased * 0.7 + t * 0.3

  for (const f of POSE_FIELDS) out[f] = a.pose[f] + (b.pose[f] - a.pose[f]) * t
  return out
}

export function createPose(): Pose {
  return { ...KEYS[0].pose }
}

import { gpuTier } from './env'

const tier = gpuTier()

/**
 * Render budget for the two WebGL layers. The black hole is a ray-marched
 * full-screen shader, so the number of pixels it shades is the main lever. It
 * runs at a fraction of the screen resolution (the image is soft, so upscaling
 * is invisible) within a fixed pixel budget, and at most 60 fps even on
 * 120/144 Hz screens. The adaptive controller below steps the resolution down
 * within about a second if frames run long, then halves the frame rate.
 */
export const quality = {
  tier,
  /** Max ray-march steps for the black hole. */
  steps: tier === 'high' ? 140 : tier === 'mid' ? 120 : 90,
  /** Ray-march step length as a fraction of the distance to the hole. */
  stepScale: tier === 'high' ? 0.08 : tier === 'mid' ? 0.09 : 0.11,
  /** Backdrop resolution as a fraction of CSS pixels... */
  backdropBase: tier === 'high' ? 0.7 : tier === 'mid' ? 0.5 : 0.35,
  /** ...and never more than this many shaded pixels. */
  backdropPixels: tier === 'high' ? 900_000 : tier === 'mid' ? 480_000 : 200_000,
  /** Adaptive multiplier on the backdrop resolution. */
  backdropScale: 1,
  /** Frame-rate cap for the backdrop. */
  backdropFps: tier === 'low' ? 30 : 60,
  /** Size of one face of the baked sky cube map. */
  skySize: tier === 'high' ? 1024 : 512,
  /** Device pixel ratio range for the 3D model layer. */
  sceneDpr: (tier === 'high' ? [1, 1.5] : tier === 'mid' ? [1, 1.25] : [1, 1]) as [number, number],
  orbCount: tier === 'high' ? 22 : 15,
}

/** Pixel ratio for the black hole canvas, within the pixel budget. */
export function backdropDpr() {
  const css = Math.max(1, window.innerWidth * window.innerHeight)
  const dpr = Math.min(quality.backdropBase, Math.sqrt(quality.backdropPixels / css)) * quality.backdropScale
  return Math.min(1, Math.max(0.2, dpr))
}

const listeners = new Set<() => void>()
export const onQualityChange = (fn: () => void) => {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}
const notify = () => listeners.forEach((fn) => fn())

let warmupUntil = 0
let sum = 0
let count = 0
let goodWindows = 0

/** Feed the frame delta (ms) once per frame. */
export function sampleFrame(deltaMs: number) {
  const now = performance.now()
  if (!warmupUntil) warmupUntil = now + 700 // let shaders compile first
  if (now < warmupUntil || deltaMs > 250) return // a hitch or tab switch, not a trend
  sum += deltaMs
  count++
  if (count < 20) return

  const avg = sum / count
  sum = 0
  count = 0

  if (avg > 19.5) {
    goodWindows = 0
    if (quality.backdropScale > 0.5) {
      quality.backdropScale = Math.max(0.5, quality.backdropScale * 0.8)
    } else if (quality.backdropFps > 30) {
      quality.backdropFps = 30
    } else {
      quality.steps = Math.max(70, quality.steps - 20)
    }
    notify()
  } else if (avg < 17.4) {
    goodWindows++
    if (goodWindows >= 6 && quality.backdropScale < 1) {
      quality.backdropScale = Math.min(1, quality.backdropScale * 1.12)
      goodWindows = 0
      notify()
    }
  } else {
    goodWindows = 0
  }
}

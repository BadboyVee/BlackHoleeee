import { gpuTier, isSmallScreen } from './env'

const tier = gpuTier()

/**
 * Render budget for the two WebGL layers. The black hole is a ray-marched
 * full-screen shader, so its resolution is the main lever; the adaptive
 * controller below lowers it when frames run long and raises it again when
 * there is headroom.
 */
export const quality = {
  tier,
  /** Max ray-march steps for the black hole. */
  steps: tier === 'high' ? 220 : tier === 'mid' ? 150 : 90,
  /** Ray-march step length as a fraction of the distance to the hole. */
  stepScale: tier === 'high' ? 0.06 : tier === 'mid' ? 0.08 : 0.11,
  /** Noise octaves in the accretion disk. */
  octaves: tier === 'high' ? 4 : 3,
  /** Backdrop resolution as a fraction of CSS pixels (before the adaptive scale). */
  backdropBase: tier === 'high' ? 0.75 : tier === 'mid' ? (isSmallScreen() ? 0.7 : 0.6) : 0.4,
  /** Adaptive multiplier, 0.45..1. */
  backdropScale: 1,
  /** Device pixel ratio range for the 3D model layer. */
  sceneDpr: (tier === 'low' ? [1, 1] : [1, 1.75]) as [number, number],
  orbCount: tier === 'high' ? 22 : 15,
}

const listeners = new Set<() => void>()
export const onQualityChange = (fn: () => void) => {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

let window_ = 0
let windowFrames = 0
let goodWindows = 0
let warmup = 90

/** Feed the frame delta (ms) once per frame. */
export function sampleFrame(deltaMs: number) {
  if (warmup > 0) {
    warmup--
    return
  }
  if (deltaMs > 120) return // tab switch or a hitch, not a trend
  window_ += deltaMs
  windowFrames++
  if (windowFrames < 30) return

  const avg = window_ / windowFrames
  window_ = 0
  windowFrames = 0

  if (avg > 21 && quality.backdropScale > 0.45) {
    quality.backdropScale = Math.max(0.45, quality.backdropScale * 0.85)
    goodWindows = 0
    listeners.forEach((fn) => fn())
  } else if (avg < 17.6) {
    goodWindows++
    if (goodWindows >= 4 && quality.backdropScale < 1) {
      quality.backdropScale = Math.min(1, quality.backdropScale * 1.1)
      goodWindows = 0
      listeners.forEach((fn) => fn())
    }
  } else {
    goodWindows = 0
  }
}

/** Ask for a fresh warm-up, e.g. after the intro when shaders have compiled. */
export const resetQualityWarmup = (frames = 60) => {
  warmup = frames
}

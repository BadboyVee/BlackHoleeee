// A tiny shared, mutable store. Values that change every frame (scroll, pointer)
// live here instead of in React state so the DOM tree never re-renders for
// them; the WebGL scene and the GSAP tickers just read the latest numbers.

type Listener = () => void

export const store = {
  /** Smoothed page scroll in px, straight from Lenis. */
  scroll: 0,
  /** Scroll velocity in px/frame (signed). */
  velocity: 0,
  /** 0 → 1 through the whole document. */
  progress: 0,
  /** Pointer in normalised device coords, -1 → 1, y up. */
  pointer: { x: 0, y: 0 },
  /** Index of the capability row being hovered, or -1. Drives the orrery. */
  activeSkill: -1,
  /** True while an opaque section fully covers the canvas, so it can sleep. */
  canvasHidden: false,
  /** `prefers-reduced-motion: reduce`. */
  reducedMotion: false,
  /** Set once the first WebGL frame is on screen (or WebGL is unavailable). */
  sceneReady: false,
  /** Set once the preloader has finished and the page is revealed. */
  introDone: false,
}

const listeners = new Map<string, Set<Listener>>()

export function on(event: 'sceneReady' | 'introDone' | 'canvasHidden', fn: Listener) {
  let set = listeners.get(event)
  if (!set) listeners.set(event, (set = new Set()))
  set.add(fn)
  return () => {
    set.delete(fn)
  }
}

export function emit(event: 'sceneReady' | 'introDone' | 'canvasHidden') {
  listeners.get(event)?.forEach((fn) => fn())
}

export function markSceneReady() {
  if (store.sceneReady) return
  store.sceneReady = true
  emit('sceneReady')
}

export function markIntroDone() {
  if (store.introDone) return
  store.introDone = true
  emit('introDone')
}

export function setCanvasHidden(hidden: boolean) {
  if (store.canvasHidden === hidden) return
  store.canvasHidden = hidden
  emit('canvasHidden')
}

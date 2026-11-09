import { advance } from '@react-three/fiber'
import Lenis from 'lenis'
import { gsap, ScrollTrigger } from './gsap'

/** Live scroll values, mutated every frame. Read them in render loops, never in React state. */
export const scroll = {
  y: 0,
  /** Lenis velocity in px per frame (signed). */
  velocity: 0,
  progress: 0,
  direction: 0 as -1 | 0 | 1,
}

/** Frame timing shared with the adaptive quality controller. */
export const frame = { time: 0, delta: 16.7 }

type Listener = (state: typeof scroll) => void
const listeners = new Set<Listener>()
let lenis: Lenis | null = null
let started = false

export const getLenis = () => lenis

export function onScroll(fn: Listener) {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

/**
 * Starts the single animation loop of the site. GSAP's ticker drives, in order:
 * Lenis (which moves the page and updates ScrollTrigger), then every React Three
 * Fiber root via `advance`. Rendering after the scroll update means the 3D views
 * that track DOM elements never lag a frame behind the page.
 */
export function startLoop({ smooth }: { smooth: boolean }) {
  if (started) return
  started = true

  if ('scrollRestoration' in history) history.scrollRestoration = 'manual'

  lenis = new Lenis({
    autoRaf: false,
    lerp: 0.085,
    smoothWheel: smooth,
    wheelMultiplier: 1,
    touchMultiplier: 1.4,
    syncTouch: false,
    anchors: false,
  })
  lenis.stop() // released when the preloader finishes

  lenis.on('scroll', (l: Lenis) => {
    scroll.y = l.scroll
    scroll.velocity = l.velocity
    scroll.progress = l.progress
    scroll.direction = l.direction
    ScrollTrigger.update()
    listeners.forEach((fn) => fn(scroll))
  })

  gsap.ticker.lagSmoothing(0)
  gsap.ticker.add((time, deltaTime) => {
    frame.time = time
    frame.delta = deltaTime
    lenis?.raf(time * 1000)
    advance(time)
  })
}

const expoInOut = (t: number) =>
  t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2

export function scrollTo(target: string | number | HTMLElement, options: { immediate?: boolean; offset?: number } = {}) {
  if (lenis) {
    lenis.scrollTo(target, { duration: 1.8, easing: expoInOut, force: true, ...options })
    return
  }
  const el = typeof target === 'string' ? document.querySelector(target) : target
  if (typeof el === 'number') window.scrollTo({ top: el })
  else el?.scrollIntoView()
}

export function setScrollLocked(locked: boolean) {
  if (!lenis) return
  if (locked) lenis.stop()
  else lenis.start()
}

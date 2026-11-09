// Smooth scrolling. Lenis owns the scroll position, GSAP's ticker drives Lenis,
// and ScrollTrigger is told about every Lenis update — so scroll-scrubbed
// animations, the WebGL camera and the page itself all move on one clock.

import Lenis from 'lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'
import { store } from './store'

gsap.registerPlugin(ScrollTrigger, SplitText)

// Scroll-scrubbed work should never "catch up" after a dropped frame.
gsap.ticker.lagSmoothing(0)
gsap.defaults({ ease: 'power3.out', duration: 1 })

let lenis: Lenis | null = null

export function getLenis() {
  return lenis
}

export function initScroll() {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  store.reducedMotion = reduced

  const instance = new Lenis({
    autoRaf: false,
    // Reduced motion: keep native, instant scrolling.
    lerp: reduced ? 1 : 0.085,
    smoothWheel: !reduced,
    wheelMultiplier: 0.95,
    touchMultiplier: 1.4,
  })
  lenis = instance

  instance.on('scroll', (l: Lenis) => {
    store.scroll = l.scroll
    store.velocity = l.velocity
    store.progress = l.progress
    ScrollTrigger.update()
  })

  const tick = (time: number) => instance.raf(time * 1000)
  gsap.ticker.add(tick)

  // The page starts locked behind the preloader.
  instance.stop()

  return () => {
    gsap.ticker.remove(tick)
    instance.destroy()
    if (lenis === instance) lenis = null
  }
}

export function scrollTo(target: string | number | HTMLElement, options: { offset?: number; duration?: number; immediate?: boolean } = {}) {
  if (!lenis) return
  lenis.scrollTo(target, {
    offset: options.offset ?? 0,
    duration: store.reducedMotion ? 0 : (options.duration ?? 1.6),
    immediate: store.reducedMotion || options.immediate,
    easing: (t: number) => 1 - Math.pow(1 - t, 4),
    force: true,
  })
}

export { gsap, ScrollTrigger, SplitText }

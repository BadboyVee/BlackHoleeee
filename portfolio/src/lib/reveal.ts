import { prefersReducedMotion } from './env'
import { gsap, SplitText } from './gsap'

/**
 * Text and element reveals. Call these inside a `useGSAP` callback so the
 * splits, tweens and ScrollTriggers are cleaned up with the component.
 */

type RevealOptions = {
  start?: string
  delay?: number
  stagger?: number
  duration?: number
}

const reduced = () => prefersReducedMotion()

/** Lines slide up from behind a mask when the element scrolls into view. */
export function revealLines(target: Element, { start = 'top 85%', delay = 0, stagger = 0.09, duration = 1.5 }: RevealOptions = {}) {
  if (reduced()) return
  return SplitText.create(target, {
    type: 'lines',
    mask: 'lines',
    linesClass: 'split-line',
    autoSplit: true,
    aria: 'auto',
    onSplit: (self) =>
      gsap.from(self.lines, {
        yPercent: 115,
        duration,
        delay,
        stagger,
        ease: 'expo.out',
        scrollTrigger: { trigger: target, start, once: true },
      }),
  })
}

/** Characters rise one after another. */
export function revealChars(target: Element, { start = 'top 85%', delay = 0, stagger = 0.025, duration = 1.3 }: RevealOptions = {}) {
  if (reduced()) return
  return SplitText.create(target, {
    type: 'chars,words',
    mask: 'words',
    aria: 'auto',
    onSplit: (self) =>
      gsap.from(self.chars, {
        yPercent: 120,
        duration,
        delay,
        stagger,
        ease: 'expo.out',
        scrollTrigger: { trigger: target, start, once: true },
      }),
  })
}

/** Words light up as the reader scrolls through a paragraph. */
export function scrubWords(target: Element, { start = 'top 80%', end = 'bottom 55%' } = {}) {
  if (reduced()) return
  return SplitText.create(target, {
    type: 'words',
    aria: 'auto',
    onSplit: (self) =>
      gsap.fromTo(
        self.words,
        { opacity: 0.14 },
        { opacity: 1, ease: 'none', stagger: 0.1, scrollTrigger: { trigger: target, start, end, scrub: true } },
      ),
  })
}

/** Simple fade and rise for groups of elements. */
export function revealUp(targets: gsap.TweenTarget, trigger: Element, { start = 'top 85%', delay = 0, stagger = 0.08, duration = 1.3 }: RevealOptions = {}) {
  if (reduced()) return
  return gsap.from(targets, {
    y: 40,
    opacity: 0,
    duration,
    delay,
    stagger,
    ease: 'expo.out',
    scrollTrigger: { trigger, start, once: true },
  })
}

/** Elements with data-speed drift at their own pace while they cross the screen. */
export function parallax(scope: Element) {
  if (reduced()) return
  scope.querySelectorAll<HTMLElement>('[data-speed]').forEach((el) => {
    const speed = parseFloat(el.dataset.speed ?? '1')
    gsap.fromTo(
      el,
      { y: () => (speed - 1) * window.innerHeight * 0.35 },
      {
        y: () => (1 - speed) * window.innerHeight * 0.35,
        ease: 'none',
        scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true, invalidateOnRefresh: true },
      },
    )
  })
}

import { useRef, type ElementType, type ReactNode } from 'react'
import { useGSAP } from '@gsap/react'
import { gsap, SplitText } from '../lib/scroll'
import { store } from '../lib/store'

interface RevealProps {
  as?: ElementType
  children: ReactNode
  className?: string
  /** Seconds to wait after the element scrolls into view. */
  delay?: number
  stagger?: number
  /** ScrollTrigger start, e.g. "top 85%". */
  start?: string
}

/**
 * Text that rises out of a mask, line by line, the first time it scrolls into
 * view. SplitText re-splits on resize and font load, so line breaks stay right.
 */
export function Reveal({ as: Tag = 'div', children, className, delay = 0, stagger = 0.09, start = 'top 88%' }: RevealProps) {
  const ref = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      const el = ref.current
      if (!el || store.reducedMotion) return
      SplitText.create(el, {
        type: 'lines',
        mask: 'lines',
        linesClass: 'split-line',
        autoSplit: true,
        onSplit: (self) =>
          gsap.from(self.lines, {
            yPercent: 115,
            duration: 1.25,
            ease: 'expo.out',
            stagger,
            delay,
            scrollTrigger: { trigger: el, start, once: true },
          }),
      })
    },
    { scope: ref },
  )

  return (
    <Tag ref={ref} className={className}>
      {children}
    </Tag>
  )
}

interface FadeProps {
  children: ReactNode
  className?: string
  delay?: number
  y?: number
  start?: string
}

/** Simple fade-and-rise for blocks that are not running text. */
export function FadeIn({ children, className, delay = 0, y = 40, start = 'top 90%' }: FadeProps) {
  const ref = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const el = ref.current
      if (!el || store.reducedMotion) return
      gsap.from(el, { y, autoAlpha: 0, duration: 1.2, ease: 'expo.out', delay, scrollTrigger: { trigger: el, start, once: true } })
    },
    { scope: ref },
  )

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  )
}

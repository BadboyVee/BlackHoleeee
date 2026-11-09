import { useRef, type ReactNode } from 'react'
import { useGSAP } from '@gsap/react'
import { gsap } from '../lib/scroll'
import { store } from '../lib/store'

interface ParallaxProps {
  children: ReactNode
  className?: string
  /**
   * How far the layer drifts against the scroll, as a fraction of the viewport
   * height. Positive values lag behind (feel further away), negative run ahead.
   */
  speed?: number
}

/** Scroll-linked vertical parallax for any block. */
export function Parallax({ children, className, speed = 0.15 }: ParallaxProps) {
  const ref = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const el = ref.current
      if (!el || store.reducedMotion) return
      gsap.fromTo(
        el,
        { y: () => speed * window.innerHeight * 0.5 },
        {
          y: () => -speed * window.innerHeight * 0.5,
          ease: 'none',
          scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true, invalidateOnRefresh: true },
        },
      )
    },
    { scope: ref },
  )

  return (
    <div ref={ref} className={className} style={{ willChange: 'transform' }}>
      {children}
    </div>
  )
}

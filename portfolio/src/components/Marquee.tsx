import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import { gsap } from '../lib/scroll'
import { store } from '../lib/store'

/**
 * An endless ticker that listens to the scroll: it speeds up with the page
 * and turns around when you scroll the other way.
 */
export function Marquee({ items }: { items: string[] }) {
  const track = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const el = track.current
      if (!el) return

      let loop = el.scrollWidth / 2
      const measure = () => {
        loop = el.scrollWidth / 2
      }
      const observer = new ResizeObserver(measure)
      observer.observe(el)

      const setX = gsap.quickSetter(el, 'x', 'px')
      const setSkew = gsap.quickSetter(el, 'skewX', 'deg')
      let x = 0
      let direction = -1
      let skew = 0

      const tick = (_time: number, deltaMs: number) => {
        const dt = Math.min(deltaMs, 100)
        const v = store.velocity
        if (Math.abs(v) > 0.4) direction = v > 0 ? -1 : 1
        const idle = store.reducedMotion ? 0 : 0.055
        x += direction * (idle * dt + Math.abs(v) * 0.9)
        if (loop > 0) x = ((x % loop) - loop) % loop
        setX(x)
        skew += (gsap.utils.clamp(-8, 8, v * 0.18) - skew) * 0.12
        setSkew(store.reducedMotion ? 0 : skew)
      }

      gsap.ticker.add(tick)
      return () => {
        gsap.ticker.remove(tick)
        observer.disconnect()
      }
    },
    { scope: track },
  )

  return (
    <div className="marquee" aria-hidden="true">
      <div ref={track} className="marquee-track">
        {[0, 1].map((copy) => (
          <div key={copy} className="marquee-group">
            {items.map((item, i) => (
              <span key={item} className="marquee-item">
                <span className={i % 2 ? 'marquee-outline' : undefined}>{item}</span>
                <span className="marquee-star">✦</span>
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

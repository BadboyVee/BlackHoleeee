import { useEffect, useRef } from 'react'
import { gsap } from '../lib/scroll'
import { store } from '../lib/store'

/** A hairline on the right edge that fills as you fall, with a % read-out. */
export function ScrollProgress() {
  const fill = useRef<HTMLDivElement>(null)
  const text = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    let shown = -1
    const tick = () => {
      if (fill.current) fill.current.style.transform = `scaleY(${store.progress.toFixed(4)})`
      const pct = Math.round(store.progress * 100)
      if (pct !== shown && text.current) {
        shown = pct
        text.current.textContent = String(pct).padStart(3, '0')
      }
    }
    gsap.ticker.add(tick)
    return () => gsap.ticker.remove(tick)
  }, [])

  return (
    <div className="progress chrome" aria-hidden="true">
      <span ref={text} className="label">
        000
      </span>
      <div className="progress-rail">
        <div ref={fill} className="progress-fill" />
      </div>
    </div>
  )
}

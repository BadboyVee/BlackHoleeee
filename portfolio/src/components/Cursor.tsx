import { useEffect, useRef, useState } from 'react'
import { gsap } from '../lib/scroll'

type CursorState = 'default' | 'link' | 'view'

/**
 * Custom cursor for devices with a real mouse: a dot that tracks the pointer
 * exactly and a ring that trails it. Any link or button swells the ring;
 * elements marked `data-cursor="view"` swap it for a labelled badge
 * (the text comes from `data-cursor-label`).
 */
export function Cursor() {
  const [enabled] = useState(() => window.matchMedia('(hover: hover) and (pointer: fine)').matches)
  const dot = useRef<HTMLDivElement>(null)
  const ring = useRef<HTMLDivElement>(null)
  const badge = useRef<HTMLDivElement>(null)
  const label = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!enabled || !dot.current || !ring.current || !badge.current) return
    const root = document.documentElement
    root.classList.add('has-cursor')

    const els = [dot.current, ring.current, badge.current]
    gsap.set(els, { xPercent: -50, yPercent: -50, autoAlpha: 0 })
    gsap.set(badge.current, { scale: 0 })

    const follow = (el: HTMLElement, duration: number) => [
      gsap.quickTo(el, 'x', { duration, ease: 'power3.out' }),
      gsap.quickTo(el, 'y', { duration, ease: 'power3.out' }),
    ]
    const movers = [follow(dot.current, 0.08), follow(ring.current, 0.42), follow(badge.current, 0.3)]

    let state: CursorState = 'default'
    let visible = false
    let pressed = false

    const apply = () => {
      const press = pressed ? 0.78 : 1
      gsap.to(dot.current, { scale: state === 'default' ? 1 : 0, duration: 0.3, overwrite: 'auto' })
      gsap.to(ring.current, {
        scale: (state === 'link' ? 1.75 : state === 'view' ? 0 : 1) * press,
        backgroundColor: state === 'link' ? 'rgba(255,255,255,1)' : 'rgba(255,255,255,0)',
        duration: 0.45,
        ease: 'expo.out',
        overwrite: 'auto',
      })
      gsap.to(badge.current, { scale: state === 'view' ? press : 0, duration: 0.5, ease: 'expo.out', overwrite: 'auto' })
    }

    const move = (e: PointerEvent) => {
      if (e.pointerType === 'touch') return
      for (const [x, y] of movers) {
        x(e.clientX)
        y(e.clientY)
      }
      if (!visible) {
        visible = true
        gsap.to(els, { autoAlpha: 1, duration: 0.3 })
      }
    }

    const over = (e: PointerEvent) => {
      const target = e.target instanceof Element ? e.target.closest<HTMLElement>('[data-cursor], a, button') : null
      const next: CursorState = !target ? 'default' : target.dataset.cursor === 'view' ? 'view' : 'link'
      if (next === 'view' && label.current) label.current.textContent = target?.dataset.cursorLabel ?? 'View'
      if (next !== state) {
        state = next
        apply()
      }
    }

    const down = () => {
      pressed = true
      apply()
    }
    const up = () => {
      pressed = false
      apply()
    }
    const leave = () => {
      visible = false
      gsap.to(els, { autoAlpha: 0, duration: 0.3 })
    }

    window.addEventListener('pointermove', move, { passive: true })
    document.addEventListener('pointerover', over, { passive: true })
    window.addEventListener('pointerdown', down)
    window.addEventListener('pointerup', up)
    root.addEventListener('pointerleave', leave)

    return () => {
      root.classList.remove('has-cursor')
      window.removeEventListener('pointermove', move)
      document.removeEventListener('pointerover', over)
      window.removeEventListener('pointerdown', down)
      window.removeEventListener('pointerup', up)
      root.removeEventListener('pointerleave', leave)
      gsap.killTweensOf(els)
    }
  }, [enabled])

  if (!enabled) return null

  return (
    <div aria-hidden="true">
      <div className="cursor-blend">
        <div ref={ring} className="cursor-ring" />
        <div ref={dot} className="cursor-dot" />
      </div>
      <div ref={badge} className="cursor-badge">
        <span ref={label} className="label">
          View
        </span>
      </div>
    </div>
  )
}

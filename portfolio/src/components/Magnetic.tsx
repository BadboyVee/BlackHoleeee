import { useRef, type ReactNode } from 'react'
import { useGSAP } from '@gsap/react'
import { gsap } from '../lib/scroll'
import { store } from '../lib/store'

interface MagneticProps {
  children: ReactNode
  className?: string
  /** 0 → 1: how strongly the element is pulled toward the pointer. */
  strength?: number
}

/** Wraps a button or link so it leans toward the pointer and springs back. */
export function Magnetic({ children, className, strength = 0.35 }: MagneticProps) {
  const ref = useRef<HTMLDivElement>(null)

  useGSAP(
    () => {
      const el = ref.current
      if (!el || store.reducedMotion || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return

      const xTo = gsap.quickTo(el, 'x', { duration: 0.9, ease: 'elastic.out(1, 0.45)' })
      const yTo = gsap.quickTo(el, 'y', { duration: 0.9, ease: 'elastic.out(1, 0.45)' })

      const move = (e: PointerEvent) => {
        const rect = el.getBoundingClientRect()
        xTo((e.clientX - (rect.left + rect.width / 2)) * strength)
        yTo((e.clientY - (rect.top + rect.height / 2)) * strength)
      }
      const leave = () => {
        xTo(0)
        yTo(0)
      }

      el.addEventListener('pointermove', move)
      el.addEventListener('pointerleave', leave)
      return () => {
        el.removeEventListener('pointermove', move)
        el.removeEventListener('pointerleave', leave)
      }
    },
    { scope: ref },
  )

  return (
    <div ref={ref} className={className} style={{ display: 'inline-block' }}>
      {children}
    </div>
  )
}

import { useRef, useState } from 'react'
import { useGSAP } from '@gsap/react'
import { debug } from '../lib/debug'
import { getLenis, gsap } from '../lib/scroll'
import { markIntroDone, on, store } from '../lib/store'

const LINES = ['Compiling shaders', 'Bending light', 'Calibrating event horizon']

/**
 * Covers the page while the 3D scene boots: a counter creeps up, waits for the
 * first real WebGL frame, then the cover opens like an iris from the exact
 * spot where the black hole sits.
 */
export function Preloader() {
  const root = useRef<HTMLDivElement>(null)
  const count = useRef<HTMLSpanElement>(null)
  const bar = useRef<HTMLDivElement>(null)
  const line = useRef<HTMLSpanElement>(null)
  const [gone, setGone] = useState(debug.noIntro)

  useGSAP(
    () => {
      const reveal = () => {
        markIntroDone()
        getLenis()?.start()
      }

      if (debug.noIntro || !root.current) {
        reveal()
        return
      }

      const progress = { value: 0 }
      const render = () => {
        const v = Math.round(progress.value)
        if (count.current) count.current.textContent = String(v).padStart(3, '0')
        if (bar.current) bar.current.style.transform = `scaleX(${progress.value / 100})`
        if (line.current) line.current.textContent = LINES[Math.min(LINES.length - 1, Math.floor((v / 100) * LINES.length))]
      }

      // Creep toward 84% while we wait for the scene…
      const creep = gsap.to(progress, { value: 84, duration: 2.6, ease: 'power2.out', onUpdate: render })

      let finished = false
      const finish = () => {
        if (finished) return
        finished = true
        creep.kill()

        // The iris opens from where the hole is drawn (see the hero pose in lib/rig.ts).
        const narrow = window.innerWidth / window.innerHeight < 0.9
        root.current!.style.setProperty('--iris-x', narrow ? '50%' : '65%')
        root.current!.style.setProperty('--iris-y', narrow ? '39%' : '47%')

        const tl = gsap.timeline({ onComplete: () => setGone(true) })
        tl.to(progress, { value: 100, duration: 0.6, ease: 'power2.inOut', onUpdate: render })
        tl.to('.preloader-item', { yPercent: -130, duration: 0.7, ease: 'power3.in', stagger: 0.05 }, '+=0.2')
        tl.add(reveal, '-=0.1')
        if (store.reducedMotion) {
          tl.to(root.current, { autoAlpha: 0, duration: 0.4 })
        } else {
          tl.fromTo(root.current, { '--iris': '0vmax' }, { '--iris': '150vmax', duration: 1.5, ease: 'expo.inOut' }, '-=0.25')
        }
      }

      // …but never flash by too quickly, and never wait forever.
      let off: (() => void) | undefined
      const hold = gsap.delayedCall(1.3, () => {
        if (store.sceneReady) finish()
        else off = on('sceneReady', finish)
      })
      const giveUp = gsap.delayedCall(10, finish)

      return () => {
        off?.()
        hold.kill()
        giveUp.kill()
      }
    },
    { scope: root },
  )

  if (gone) return null

  return (
    <div ref={root} className="preloader" role="status" aria-label="Loading">
      <div className="preloader-top gutter">
        <div className="overflow-hidden">
          <span className="preloader-item label block">Vee — Portfolio</span>
        </div>
        <div className="overflow-hidden">
          <span ref={line} className="preloader-item label block text-ash">
            {LINES[0]}
          </span>
        </div>
      </div>
      <div className="preloader-bottom gutter">
        <div className="overflow-hidden">
          <span ref={count} className="preloader-item preloader-count display block">
            000
          </span>
        </div>
        <div className="preloader-rail">
          <div ref={bar} className="preloader-bar" />
        </div>
      </div>
    </div>
  )
}

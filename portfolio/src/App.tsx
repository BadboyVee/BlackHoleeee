import { useEffect } from 'react'
import { Cursor, Grain, Header, Preloader, ScrollProgress } from './components/ui'
import { prefersReducedMotion, isSmallScreen } from './lib/env'
import { gsap, ScrollTrigger, useGSAP } from './lib/gsap'
import { startLoop } from './lib/scroll'
import { useApp } from './lib/store'
import { About, Band, Contact, Experience, Hero, Process, Toolkit, Work } from './sections/Sections'
import Backdrop from './three/backdrop/Backdrop'
import { desktopShots, mobileShots, target, type ShotName } from './three/backdrop/shots'
import { SceneCanvas } from './three/Scene'

// Start on the right framing for the screen size, before the first frame.
Object.assign(target, isSmallScreen() ? mobileShots.hero : desktopShots.hero)

/** Blends the black hole camera from shot to shot as each section scrolls in. */
function useBackdropShots(ready: boolean) {
  useGSAP(
    () => {
      if (!ready) return
      const mm = gsap.matchMedia()
      mm.add({ small: '(max-width: 767px)', large: '(min-width: 768px)' }, (ctx) => {
        const shots = ctx.conditions?.small ? mobileShots : desktopShots
        const sections = gsap.utils.toArray<HTMLElement>('[data-shot]')
        let prev = shots[sections[0].dataset.shot as ShotName]
        Object.assign(target, prev)
        sections.slice(1).forEach((el) => {
          const next = shots[el.dataset.shot as ShotName]
          gsap.fromTo(target, { ...prev }, { ...next, ease: 'none', immediateRender: false, scrollTrigger: { trigger: el, start: 'top bottom', end: 'top 25%', scrub: true } })
          prev = next
        })
      })
      // Layout settles once fonts and sticky sections are in place.
      requestAnimationFrame(() => ScrollTrigger.refresh())
      return () => mm.revert()
    },
    { dependencies: [ready] },
  )
}

export default function App() {
  const ready = useApp((s) => s.ready)

  useEffect(() => {
    startLoop({ smooth: !prefersReducedMotion() })
    console.log(
      '%c✦ Built with gravity — React Three Fiber, GSAP, Lenis and a ray-marched black hole. Curious? Say hi.',
      'color:#ff5b1f;font:600 12px/1.6 ui-monospace,monospace',
    )
  }, [])

  useBackdropShots(ready)

  return (
    <>
      <Preloader />
      <Backdrop />
      <SceneCanvas />
      <a href="#main" className="label sr-only z-[80] rounded bg-paper px-4 py-2 text-void focus:not-sr-only focus:fixed focus:left-4 focus:top-4">
        Skip to content
      </a>
      <Header />
      <main id="main">
        <Hero />
        <Band />
        <About />
        <Work />
        <Toolkit />
        <Process />
        <Experience />
        <Contact />
      </main>
      <ScrollProgress />
      <Cursor />
      <Grain />
    </>
  )
}

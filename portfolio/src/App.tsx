import { Component, lazy, Suspense, useEffect, type ReactNode } from 'react'
import { marquee } from './content'
import { Cursor } from './components/Cursor'
import { Marquee } from './components/Marquee'
import { Nav } from './components/Nav'
import { Preloader } from './components/Preloader'
import { ScrollProgress } from './components/ScrollProgress'
import { ScrollTrigger } from './lib/scroll'
import { markSceneReady, on, store } from './lib/store'
import { About } from './sections/About'
import { Approach } from './sections/Approach'
import { Contact } from './sections/Contact'
import { Hero } from './sections/Hero'
import { Stack } from './sections/Stack'
import { Work } from './sections/Work'

// three.js is the heavy part: load it in its own chunk, behind the preloader.
const Experience = lazy(() => import('./three/Experience'))

/** If WebGL is missing or the scene crashes, show a painted backdrop instead. */
class SceneBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  componentDidCatch() {
    markSceneReady()
  }
  render() {
    return this.state.failed ? <div className="scene-fallback" /> : this.props.children
  }
}

export default function App() {
  useEffect(() => {
    const move = (e: PointerEvent) => {
      store.pointer.x = (e.clientX / window.innerWidth) * 2 - 1
      store.pointer.y = -((e.clientY / window.innerHeight) * 2 - 1)
    }
    window.addEventListener('pointermove', move, { passive: true })

    // Nav and HUD fade in once the preloader has opened.
    const ready = () => document.documentElement.classList.add('is-ready')
    const off = store.introDone ? (ready(), undefined) : on('introDone', ready)

    // Web fonts change line breaks; re-measure every scroll animation after.
    document.fonts.ready.then(() => ScrollTrigger.refresh())

    return () => {
      window.removeEventListener('pointermove', move)
      off?.()
    }
  }, [])

  return (
    <>
      <a href="#work" className="skip-link label">
        Skip to work
      </a>

      <div className="scene" aria-hidden="true">
        <SceneBoundary>
          <Suspense fallback={null}>
            <Experience />
          </Suspense>
        </SceneBoundary>
      </div>

      <Nav />
      <ScrollProgress />

      <main className="relative z-10">
        <Hero />
        <Marquee items={marquee} />
        <About />
        <Work />
        <Stack />
        <Approach />
        <Contact />
      </main>

      <div className="grain" aria-hidden="true" />
      <Cursor />
      <Preloader />
    </>
  )
}

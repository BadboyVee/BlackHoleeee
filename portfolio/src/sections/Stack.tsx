import { useEffect, useRef, useState } from 'react'
import { stack } from '../content'
import { FadeIn, Reveal } from '../components/Reveal'
import { SectionLabel } from '../components/SectionLabel'
import { store } from '../lib/store'

/**
 * Capabilities. Each row is wired to one ring of the 3D orrery: hover (or tap)
 * a row and its ring lights up. Left alone, the rows take turns by themselves.
 */
export function Stack() {
  const root = useRef<HTMLElement>(null)
  const [active, setActive] = useState(-1)
  const hovering = useRef(false)

  useEffect(() => {
    store.activeSkill = active
  }, [active])

  useEffect(() => {
    const el = root.current
    if (!el) return
    let visible = false
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting
      if (!visible && !hovering.current) setActive(-1)
    }, { threshold: 0.35 })
    observer.observe(el)
    const timer = window.setInterval(() => {
      if (visible && !hovering.current) setActive((i) => (i + 1) % stack.length)
    }, 2200)
    return () => {
      observer.disconnect()
      window.clearInterval(timer)
      store.activeSkill = -1
    }
  }, [])

  return (
    <section id="stack" ref={root} className="stack gutter">
      <div className="stack-col">
        <SectionLabel index="03" title="Stack" />
        <Reveal as="h2" className="display stack-title">
          Tools in <span className="serif text-ember-soft">orbit</span>
        </Reveal>

        <ul className="stack-list" onPointerLeave={() => (hovering.current = false)}>
          {stack.map((item, i) => (
            <li key={item.title}>
              <FadeIn delay={i * 0.05} y={24}>
                <button
                  type="button"
                  className="stack-row"
                  data-active={active === i}
                  onPointerEnter={() => {
                    hovering.current = true
                    setActive(i)
                  }}
                  onFocus={() => setActive(i)}
                  onClick={() => setActive(i)}
                >
                  <span className="label stack-num">{String(i + 1).padStart(2, '0')}</span>
                  <span className="stack-name">{item.title}</span>
                  <span className="label stack-tools">{item.tools}</span>
                </button>
              </FadeIn>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

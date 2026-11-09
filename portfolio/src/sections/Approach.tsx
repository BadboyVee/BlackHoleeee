import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import { approach } from '../content'
import { Reveal } from '../components/Reveal'
import { SectionLabel } from '../components/SectionLabel'
import { gsap, ScrollTrigger } from '../lib/scroll'
import { setCanvasHidden, store } from '../lib/store'

/** A light sheet that slides over the scene; its cards stack as you scroll. */
export function Approach() {
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      // While this opaque section fills the screen the WebGL canvas can sleep.
      ScrollTrigger.create({
        trigger: root.current,
        start: 'top top',
        end: 'bottom bottom',
        onToggle: (self) => setCanvasHidden(self.isActive),
      })

      if (store.reducedMotion) return
      const cards = gsap.utils.toArray<HTMLElement>('.approach-card')
      cards.forEach((card, i) => {
        if (i === cards.length - 1) return
        // Each card shrinks back a little as the next one slides over it.
        gsap.to(card, {
          scale: 1 - (cards.length - 1 - i) * 0.035,
          ease: 'none',
          scrollTrigger: { trigger: cards[i + 1], start: 'top bottom', end: 'top 20%', scrub: true },
        })
      })
    },
    { scope: root },
  )

  return (
    <section id="approach" ref={root} className="approach gutter">
      <div className="approach-head">
        <SectionLabel index="04" title="Approach" />
        <Reveal as="h2" className="display approach-title">
          How I <span className="serif text-ember">work</span>
        </Reveal>
      </div>

      <div className="approach-cards">
        {approach.map((step, i) => (
          <article key={step.title} className="approach-card" style={{ top: `calc(14vh + ${i * 1.6}rem)` }}>
            <span className="label text-ember">Principle {String(i + 1).padStart(2, '0')}</span>
            <h3 className="display">{step.title}</h3>
            <p>{step.text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

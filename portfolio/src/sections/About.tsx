import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import { about } from '../content'
import { Parallax } from '../components/Parallax'
import { FadeIn, Reveal } from '../components/Reveal'
import { SectionLabel } from '../components/SectionLabel'
import { gsap, SplitText } from '../lib/scroll'
import { store } from '../lib/store'

export function About() {
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (store.reducedMotion) return
      // The statement lights up word by word, tied to the scroll position.
      SplitText.create('.about-statement', {
        type: 'words',
        autoSplit: true,
        onSplit: (self) =>
          gsap.fromTo(
            self.words,
            { opacity: 0.13 },
            {
              opacity: 1,
              ease: 'none',
              stagger: 0.08,
              scrollTrigger: { trigger: '.about-statement', start: 'top 82%', end: 'bottom 48%', scrub: true },
            },
          ),
      })
    },
    { scope: root },
  )

  return (
    <section id="about" ref={root} className="about gutter">
      <div className="about-col">
        <SectionLabel index="01" title="About" />
        <p className="about-statement">{about.statement}</p>

        <div className="about-body">
          {about.body.map((text) => (
            <Reveal key={text} as="p">
              {text}
            </Reveal>
          ))}
        </div>

        <Parallax speed={-0.06}>
          <ul className="about-stats">
            {about.stats.map((stat, i) => (
              <li key={stat.label}>
                <FadeIn delay={i * 0.1}>
                  <span className="display about-stat-value">{stat.value}</span>
                  <span className="label about-stat-label">{stat.label}</span>
                </FadeIn>
              </li>
            ))}
          </ul>
        </Parallax>
      </div>
    </section>
  )
}

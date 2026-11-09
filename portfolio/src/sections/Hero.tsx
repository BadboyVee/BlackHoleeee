import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import { site } from '../content'
import { gsap, scrollTo, SplitText } from '../lib/scroll'
import { on, store } from '../lib/store'

export function Hero() {
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (store.reducedMotion) return

      // Intro: letters rise out of their masks once the preloader opens.
      const split = SplitText.create('.hero-line', { type: 'chars', mask: 'chars' })
      const intro = gsap.timeline({ paused: true })
      intro.from(split.chars, { yPercent: 115, duration: 1.4, ease: 'expo.out', stagger: 0.022 }, 0.15)
      intro.from('.hero-fade', { y: 30, autoAlpha: 0, duration: 1.2, ease: 'expo.out', stagger: 0.08 }, 0.7)
      const play = () => intro.play()
      const off = store.introDone ? (play(), undefined) : on('introDone', play)

      // Scroll: the three lines slide apart sideways and the block lifts away.
      gsap.utils.toArray<HTMLElement>('.hero-line').forEach((line, i) => {
        gsap.to(line, {
          xPercent: i % 2 ? 9 : -9,
          ease: 'none',
          scrollTrigger: { trigger: root.current, start: 'top top', end: 'bottom top', scrub: true },
        })
      })
      gsap.to('.hero-inner', {
        yPercent: -22,
        autoAlpha: 0,
        ease: 'none',
        scrollTrigger: { trigger: root.current, start: '35% top', end: 'bottom top', scrub: true },
      })

      return () => off?.()
    },
    { scope: root },
  )

  return (
    <section id="hero" ref={root} className="hero gutter">
      <div className="hero-inner">
        <div className="hero-top hero-fade">
          <span className="label">Portfolio — {site.year}</span>
          <span className="label hidden text-ash sm:block">Sgr A* · 17h 45m 40s · −29° 00′ 28″</span>
        </div>

        <h1 className="hero-title display" aria-label={site.role}>
          <span className="hero-line">Creative</span>
          <span className="hero-line serif text-ember-soft">frontend</span>
          <span className="hero-line">Developer</span>
        </h1>

        <div className="hero-bottom">
          <p className="hero-fade hero-intro">
            I'm {site.name}. {site.intro}
          </p>
          <a
            href="#work"
            onClick={(e) => {
              e.preventDefault()
              scrollTo('#work')
            }}
            className="hero-fade hero-scroll label"
          >
            <span className="hero-scroll-line" />
            Scroll to fall in
          </a>
        </div>
      </div>
    </section>
  )
}

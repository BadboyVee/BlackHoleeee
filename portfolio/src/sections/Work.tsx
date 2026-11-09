import { useRef } from 'react'
import { useGSAP } from '@gsap/react'
import { projects, site } from '../content'
import { SectionLabel } from '../components/SectionLabel'
import { gsap, ScrollTrigger } from '../lib/scroll'
import { store } from '../lib/store'

/**
 * Selected work. On wide screens the section is tall and its content sticks to
 * the viewport, so vertical scrolling drives a horizontal gallery; each image
 * drifts inside its frame for parallax. On small screens it is a plain column.
 */
export function Work() {
  const root = useRef<HTMLElement>(null)
  const track = useRef<HTMLDivElement>(null)
  const fill = useRef<HTMLDivElement>(null)
  const count = useRef<HTMLSpanElement>(null)

  useGSAP(
    () => {
      const section = root.current
      const row = track.current
      if (!section || !row) return

      const mm = gsap.matchMedia()
      mm.add('(min-width: 1024px)', () => {
        const distance = () => Math.max(0, row.scrollWidth - window.innerWidth)
        const size = () => {
          section.style.height = `${window.innerHeight + distance()}px`
        }
        size()
        ScrollTrigger.addEventListener('refreshInit', size)

        const slide = gsap.to(row, {
          x: () => -distance(),
          ease: 'none',
          scrollTrigger: {
            trigger: section,
            start: 'top top',
            end: 'bottom bottom',
            scrub: true,
            invalidateOnRefresh: true,
            onUpdate: (self) => {
              if (fill.current) fill.current.style.transform = `scaleX(${self.progress})`
              const n = Math.min(projects.length, 1 + Math.floor(self.progress * projects.length * 0.999))
              if (count.current) count.current.textContent = String(n).padStart(2, '0')
            },
          },
        })

        if (!store.reducedMotion) {
          gsap.utils.toArray<HTMLElement>('.work-media-inner').forEach((media) => {
            gsap.fromTo(
              media,
              { xPercent: -9 },
              {
                xPercent: 9,
                ease: 'none',
                scrollTrigger: { trigger: media.parentElement, containerAnimation: slide, start: 'left right', end: 'right left', scrub: true },
              },
            )
          })
        }

        return () => {
          ScrollTrigger.removeEventListener('refreshInit', size)
          section.style.height = ''
        }
      })
    },
    { scope: root },
  )

  return (
    <section id="work" ref={root} className="work">
      <div className="work-sticky">
        <div className="work-head gutter">
          <SectionLabel index="02" title="Selected work" />
          <div className="work-progress label">
            <span ref={count}>01</span>
            <div className="work-rail">
              <div ref={fill} className="work-fill" />
            </div>
            <span>{String(projects.length).padStart(2, '0')}</span>
          </div>
        </div>

        <div ref={track} className="work-track gutter">
          <div className="work-intro">
            <h2 className="display work-title">
              Selected <span className="serif text-ember-soft">work</span>
            </h2>
            <p>Four worlds that run in a browser tab. Each one is live: open it, play it, read the source.</p>
          </div>

          {projects.map((project, i) => (
            <a
              key={project.title}
              href={project.href}
              target="_blank"
              rel="noreferrer"
              className="work-card"
              data-cursor="view"
              data-cursor-label="Open"
              style={{ '--tone': project.tone } as React.CSSProperties}
            >
              <div className="work-media">
                <div className="work-media-inner">
                  {project.image ? (
                    <img src={project.image} alt={`${project.title} screenshot`} loading="lazy" decoding="async" />
                  ) : (
                    <div className="work-poster" aria-hidden="true">
                      <span className="display">{project.title}</span>
                    </div>
                  )}
                </div>
                <span className="work-index label">
                  {String(i + 1).padStart(2, '0')} / {project.kind}
                </span>
              </div>
              <div className="work-info">
                <h3 className="display">{project.title}</h3>
                <p>{project.description}</p>
                <ul className="work-tags label">
                  {project.tags.map((tag) => (
                    <li key={tag}>{tag}</li>
                  ))}
                </ul>
              </div>
            </a>
          ))}

          <a href={site.github} target="_blank" rel="noreferrer" className="work-outro">
            <span className="label text-ash">More experiments</span>
            <span className="display">
              GitHub <span className="text-ember">↗</span>
            </span>
          </a>
        </div>
      </div>
    </section>
  )
}

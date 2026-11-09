import { useGSAP } from '@gsap/react'
import { useRef } from 'react'
import { contactHref, nav, site } from '../content'
import { ScrollTrigger, scrollTo } from '../lib/scroll'

/** Fixed header: slides away while you scroll down, returns when you scroll up. */
export function Nav() {
  const bar = useRef<HTMLElement>(null)

  useGSAP(() => {
    ScrollTrigger.create({
      start: 0,
      end: 'max',
      onUpdate: (self) => bar.current?.classList.toggle('nav-hidden', self.direction === 1 && self.scroll() > 320),
    })
  })

  const go = (e: React.MouseEvent, href: string) => {
    e.preventDefault()
    scrollTo(href)
  }

  return (
    <header ref={bar} className="nav chrome gutter">
      <a href="#hero" onClick={(e) => go(e, '#hero')} className="nav-logo display" aria-label={`${site.name}, back to top`}>
        {site.name}
        <span className="text-ember">.</span>
      </a>
      <nav aria-label="Sections" className="nav-links">
        {nav.map((item) => (
          <a key={item.href} href={item.href} onClick={(e) => go(e, item.href)} className="label">
            <span className="roll">
              <span>{item.label}</span>
              <span aria-hidden="true">{item.label}</span>
            </span>
          </a>
        ))}
      </nav>
      <a href={contactHref} target="_blank" rel="noreferrer" className="nav-cta label">
        Let's talk ↗
      </a>
    </header>
  )
}

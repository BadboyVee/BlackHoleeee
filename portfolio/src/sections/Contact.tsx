import { contactHref, contactLabel, site, socials } from '../content'
import { Magnetic } from '../components/Magnetic'
import { FadeIn, Reveal } from '../components/Reveal'
import { scrollTo } from '../lib/scroll'

/** The finale: the camera falls into the hole and the call to action sits in its shadow. */
export function Contact() {
  return (
    <section id="contact" className="contact">
      <div className="contact-sticky gutter">
        <FadeIn className="label contact-kicker">
          <span className="text-ember">(05)</span> Have a project with some gravity?
        </FadeIn>
        <Reveal as="h2" className="display contact-title" stagger={0.12}>
          Let's <span className="serif text-ember-soft">talk</span>
        </Reveal>
        <FadeIn delay={0.25}>
          <Magnetic strength={0.4}>
            <a href={contactHref} target="_blank" rel="noreferrer" className="contact-cta label">
              {contactLabel} ↗
            </a>
          </Magnetic>
        </FadeIn>
      </div>

      <footer className="footer gutter label">
        <span>
          © {site.year} {site.name}
        </span>
        <span className="hidden text-ash md:inline">React · Three.js · GSAP · Lenis</span>
        <span className="footer-links">
          {socials.map((social) => (
            <a key={social.href} href={social.href} target="_blank" rel="noreferrer" className="underline-draw">
              {social.label}
            </a>
          ))}
          <button type="button" className="underline-draw" onClick={() => scrollTo(0, { duration: 2.4 })}>
            Back to top ↑
          </button>
        </span>
      </footer>
    </section>
  )
}

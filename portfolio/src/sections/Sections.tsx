import { useEffect, useRef, useState } from 'react'
import { Magnetic, Marquee, RollText } from '../components/ui'
import { site } from '../content/site'
import { prefersReducedMotion } from '../lib/env'
import { gsap, ScrollTrigger, useGSAP } from '../lib/gsap'
import { parallax, revealChars, revealLines, revealUp, scrubWords } from '../lib/reveal'
import { scrollTo } from '../lib/scroll'
import { useApp } from '../lib/store'
import { LaptopView, OrbsView, SculptureView, type WorkState } from '../three/Scene'

const pad = (n: number) => String(n).padStart(2, '0')

function SectionLabel({ index, children }: { index: number; children: string }) {
  return (
    <p className="label flex items-center gap-3 text-mute">
      <span className="text-ember">({pad(index)})</span>
      <span className="h-px w-10 bg-line" />
      {children}
    </p>
  )
}

/* ------------------------------------------------------------ Hero */

export function Hero() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)

  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.set('.hero-char', { yPercent: 115 })
      gsap.set('.hero-fade', { opacity: 0, y: 30 })
      gsap.set('.hero-rule', { scaleX: 0 })
    },
    { scope: ref },
  )

  useGSAP(
    () => {
      if (!ready || prefersReducedMotion()) return
      gsap
        .timeline({ delay: 0.1 })
        .to('.hero-char', { yPercent: 0, duration: 1.8, stagger: 0.05, ease: 'expo.out' })
        .to('.hero-rule', { scaleX: 1, duration: 1.6, ease: 'expo.inOut' }, 0.2)
        .to('.hero-fade', { opacity: 1, y: 0, duration: 1.4, stagger: 0.08, ease: 'expo.out' }, 0.5)

      const out = { trigger: ref.current, start: 'top top', end: 'bottom top', scrub: true }
      gsap.to('.hero-row-1', { xPercent: -10, ease: 'none', scrollTrigger: out })
      gsap.to('.hero-row-2', { xPercent: 8, ease: 'none', scrollTrigger: out })
      gsap.to('.hero-content', { yPercent: -30, ease: 'none', scrollTrigger: out })
      gsap.to('.hero-meta', { y: -120, opacity: 0, ease: 'none', scrollTrigger: { ...out, end: '60% top' } })
    },
    { scope: ref, dependencies: [ready] },
  )

  const row = (word: string, cls: string) => (
    <span className={`${cls} block overflow-hidden whitespace-nowrap`}>
      {[...word].map((c, i) => (
        <span key={i} className="hero-char inline-block transition-[font-stretch,color] duration-500 hover:text-ember hover:[font-stretch:125%]">
          {c}
        </span>
      ))}
    </span>
  )

  return (
    <section ref={ref} id="top" data-shot="hero" className="relative flex min-h-svh flex-col justify-end overflow-hidden pb-8 pt-28 md:pb-10">
      <div className="hero-content container-x relative">
        <div className="hero-meta mb-8 flex flex-wrap items-center gap-x-8 gap-y-3 md:mb-10">
          <p className="hero-fade label flex items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-ember" style={{ animation: 'pulse-dot 2s infinite' }} />
            {site.availability}
          </p>
          <p className="hero-fade label text-mute">{site.hero.kicker}</p>
        </div>

        <h1 className="sr-only">
          {site.name}, {site.role}
        </h1>
        <div aria-hidden="true" className="select-none text-[clamp(4.2rem,15.5vw,15rem)] font-black uppercase leading-[0.8] tracking-[-0.03em] [font-stretch:112%]">
          {row(site.firstName, 'hero-row-1')}
          {row(site.lastName, 'hero-row-2 md:pl-[8vw]')}
        </div>

        <div className="hero-rule hairline mt-8 origin-left md:mt-10" />

        <div className="mt-6 grid gap-6 md:grid-cols-12 md:items-end">
          <p className="hero-fade max-w-md text-lg leading-snug text-paper/85 md:col-span-5 md:text-xl">
            {site.hero.lead.split('with gravity')[0]}
            <span className="serif-accent text-[1.2em] text-flare">with gravity</span>
            {site.hero.lead.split('with gravity')[1]}
          </p>
          <p className="hero-fade label hidden gap-6 text-mute md:col-span-5 md:col-start-7 md:flex">
            {site.hero.coordinates.map((c) => (
              <span key={c}>{c}</span>
            ))}
          </p>
          <button
            type="button"
            onClick={() => scrollTo('#about')}
            className="hero-fade label flex items-center gap-3 justify-self-start md:col-span-2 md:justify-self-end"
            data-cursor="Scroll"
          >
            Scroll
            <span className="relative block h-10 w-px overflow-hidden bg-line">
              <span className="absolute inset-0 bg-ember" style={{ animation: 'scroll-hint 2.2s var(--ease-quart) infinite' }} />
            </span>
          </button>
        </div>
      </div>
    </section>
  )
}

/* ------------------------------------------------------------ Marquee band */

export function Band() {
  return (
    <div className="relative z-10 -my-6 overflow-hidden py-16 md:py-24" aria-hidden="true">
      <Marquee
        items={site.marquee}
        className="-rotate-2 bg-ember py-4 text-[clamp(2rem,5vw,4.5rem)] font-extrabold uppercase leading-none tracking-tight text-void [font-stretch:115%] md:py-5"
      />
      <Marquee
        items={site.marquee}
        reverse
        className="absolute left-0 right-0 top-1/2 -translate-y-1/2 rotate-2 bg-night/90 py-3 text-[clamp(1.6rem,3.6vw,3.2rem)] font-extrabold uppercase leading-none text-paper/80 [font-stretch:115%] -z-10"
      />
    </div>
  )
}

/* ------------------------------------------------------------ About */

export function About() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)

  useGSAP(
    () => {
      if (!ready) return
      const el = ref.current!
      scrubWords(el.querySelector('.about-statement')!)
      el.querySelectorAll('.about-body').forEach((p) => revealLines(p))
      revealUp(el.querySelectorAll('.stat'), el.querySelector('.stats')!, { stagger: 0.1 })
      parallax(el)
      el.querySelectorAll<HTMLElement>('.stat-value').forEach((node) => {
        const end = Number(node.dataset.value)
        const obj = { v: 0 }
        gsap.to(obj, {
          v: end,
          duration: 2.2,
          ease: 'power3.out',
          scrollTrigger: { trigger: node, start: 'top 90%', once: true },
          onUpdate: () => (node.textContent = String(Math.round(obj.v))),
        })
      })
    },
    { scope: ref, dependencies: [ready] },
  )

  return (
    <section ref={ref} id="about" data-shot="about" className="container-x relative py-28 md:py-40">
      <SectionLabel index={1}>About</SectionLabel>
      <p className="about-statement mt-10 max-w-[22ch] text-[clamp(2rem,4.6vw,4.4rem)] font-medium leading-[1.06] tracking-[-0.02em] md:max-w-[26ch]">
        {site.about.statement}
      </p>

      <div className="mt-20 grid gap-12 md:grid-cols-12 md:gap-8">
        <div className="relative h-[46vh] min-h-[320px] md:col-span-6 md:h-[62vh]" data-cursor="Spin" data-speed="0.88">
          <SculptureView />
          <span className="label absolute bottom-2 left-0 text-mute">Fig. 01 — Glass, light & gravity</span>
        </div>
        <div className="flex flex-col justify-end gap-6 md:col-span-5 md:col-start-8">
          {site.about.body.map((p) => (
            <p key={p} className="about-body text-lg leading-relaxed text-paper/75">
              {p}
            </p>
          ))}
          <Magnetic className="mt-4 self-start">
            <a href="#contact" onClick={(e) => (e.preventDefault(), scrollTo('#contact'))} className="roll-host pill label">
              <RollText text="Work with me" /> <span aria-hidden="true">→</span>
            </a>
          </Magnetic>
        </div>
      </div>

      <dl className="stats mt-24 grid grid-cols-2 gap-x-6 gap-y-12 border-t border-line pt-10 md:grid-cols-4">
        {site.about.stats.map((s) => (
          <div key={s.label} className="stat">
            <dt className="label order-2 mt-3 text-mute">{s.label}</dt>
            <dd className="text-[clamp(3rem,7vw,6rem)] font-extrabold leading-none tracking-tight [font-stretch:110%]">
              <span className="stat-value tabular-nums" data-value={s.value}>
                {s.value}
              </span>
              <span className="text-ember">{s.suffix}</span>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

/* ------------------------------------------------------------ Work */

export function Work() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)
  const [active, setActive] = useState(0)
  const state = useRef<WorkState>({ progress: 0, active: 0 }).current
  const projects = site.projects
  const count = projects.length

  useGSAP(
    () => {
      ScrollTrigger.create({
        trigger: ref.current,
        start: 'top top',
        end: 'bottom bottom',
        onUpdate: (self) => {
          state.progress = self.progress
          const i = Math.min(count - 1, Math.max(0, Math.floor(((self.progress - 0.14) / 0.84) * count)))
          if (i !== state.active) {
            state.active = i
            setActive(i)
          }
        },
      })
      if (ready) revealLines(ref.current!.querySelector('.work-title')!)
    },
    { scope: ref, dependencies: [ready] },
  )

  // Animate the project copy each time the active project changes.
  useGSAP(
    () => {
      if (prefersReducedMotion()) return
      gsap.fromTo('.work-swap', { yPercent: 110 }, { yPercent: 0, duration: 1.1, stagger: 0.05, ease: 'expo.out' })
      gsap.fromTo('.work-fade', { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.9, stagger: 0.05, ease: 'expo.out' })
    },
    { scope: ref, dependencies: [active] },
  )

  const jump = (i: number) => {
    const el = ref.current!
    const top = el.offsetTop + (el.offsetHeight - window.innerHeight) * (0.14 + ((i + 0.5) / count) * 0.84)
    scrollTo(top)
  }

  const p = projects[active]
  return (
    <section ref={ref} id="work" data-shot="work" className="relative" style={{ height: `${(count + 1.4) * 100}svh` }}>
      <div className="sticky top-0 flex h-svh flex-col overflow-hidden pt-24 md:pt-28">
        <div className="container-x flex items-end justify-between gap-6">
          <div>
            <SectionLabel index={2}>Selected work</SectionLabel>
            <h2 className="work-title mt-4 text-[clamp(2.4rem,6vw,5.5rem)] font-extrabold uppercase leading-[0.9] tracking-tight [font-stretch:112%]">
              Work that <span className="serif-accent text-flare">orbits</span>
            </h2>
          </div>
          <p className="label hidden tabular-nums text-mute md:block">
            <span className="text-paper">{pad(active + 1)}</span> / {pad(count)}
          </p>
        </div>

        <div className="container-x relative grid flex-1 grid-rows-[1fr_auto] gap-4 pb-8 md:grid-cols-12 md:grid-rows-1 md:gap-8">
          <div className="relative order-1 min-h-[34vh] md:order-2 md:col-span-7 md:col-start-6" data-cursor="View">
            <LaptopView state={state} />
          </div>
          <div className="order-2 flex flex-col justify-end md:order-1 md:col-span-5 md:pb-6">
            <p className="label overflow-hidden text-ember">
              <span className="work-swap inline-block">
                {p.kind} · {p.year}
              </span>
            </p>
            <h3 className="mt-3 overflow-hidden text-[clamp(2.2rem,4.6vw,4.2rem)] font-extrabold leading-[0.95] tracking-tight [font-stretch:108%]">
              <span className="work-swap inline-block">{p.title}</span>
            </h3>
            <p className="work-fade mt-4 max-w-md leading-relaxed text-paper/75">{p.description}</p>
            <ul className="work-fade mt-5 flex flex-wrap gap-2" aria-label="Stack">
              {p.stack.map((s) => (
                <li key={s} className="label rounded-full border border-line px-3 py-1.5 text-paper/80">
                  {s}
                </li>
              ))}
            </ul>
            <p className="work-fade label mt-5 text-mute">Role · {p.role}</p>
            <div className="mt-6 flex gap-2" role="tablist" aria-label="Projects">
              {projects.map((proj, i) => (
                <button
                  key={proj.id}
                  type="button"
                  role="tab"
                  aria-selected={i === active}
                  aria-label={proj.title}
                  onClick={() => jump(i)}
                  className="group h-6 flex-1 py-2.5"
                >
                  <span className={`block h-px w-full transition-colors duration-500 ${i === active ? 'bg-ember' : 'bg-line group-hover:bg-paper/50'}`} />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ------------------------------------------------------------ Toolkit */

export function Toolkit() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)
  useGSAP(
    () => {
      if (!ready) return
      revealChars(ref.current!.querySelector('.tk-title')!)
      revealUp(ref.current!.querySelectorAll('.tk-group'), ref.current!.querySelector('.tk-groups')!, { stagger: 0.08 })
    },
    { scope: ref, dependencies: [ready] },
  )
  return (
    <section ref={ref} id="toolkit" data-shot="toolkit" className="relative py-28 md:py-36">
      <div className="container-x">
        <SectionLabel index={3}>Toolkit</SectionLabel>
        <h2 className="tk-title mt-4 max-w-4xl text-[clamp(2.4rem,6vw,5.5rem)] font-extrabold uppercase leading-[0.9] tracking-tight [font-stretch:112%]">
          Tools that <span className="serif-accent normal-case text-flare">orbit</span> my craft
        </h2>
      </div>
      <div className="relative mt-6 h-[75svh] min-h-[460px]" data-cursor="Push">
        <OrbsView />
        <p className="label pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 text-mute">
          Move through the orbs · click for a big bang
        </p>
      </div>
      <div className="tk-groups container-x mt-10 grid grid-cols-2 gap-8 border-t border-line pt-10 md:grid-cols-4">
        {site.toolkit.groups.map((g) => (
          <div key={g.title} className="tk-group">
            <h3 className="label text-ember">{g.title}</h3>
            <ul className="mt-4 space-y-2 text-lg text-paper/80">
              {g.items.map((it) => (
                <li key={it}>{it}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------ Process (stacking cards) */

const CARD_STYLES = ['bg-bone text-void', 'bg-ember text-void', 'bg-ash text-paper border border-line', 'bg-paper text-void']

export function Process() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)
  useGSAP(
    () => {
      if (!ready || prefersReducedMotion()) return
      const cards = gsap.utils.toArray<HTMLElement>('.process-card')
      cards.forEach((card, i) => {
        const next = cards[i + 1]
        if (!next) return
        const scrollTrigger = { trigger: next, start: 'top bottom', end: 'top 15%', scrub: true }
        gsap.to(card, { scale: 0.9, ease: 'none', scrollTrigger })
        gsap.to(card.querySelector('.card-shade'), { opacity: 0.5, ease: 'none', scrollTrigger })
      })
      revealChars(ref.current!.querySelector('.process-title')!)
    },
    { scope: ref, dependencies: [ready] },
  )
  return (
    <section ref={ref} id="process" data-shot="process" className="container-x relative py-28 md:py-36">
      <SectionLabel index={4}>Process</SectionLabel>
      <h2 className="process-title mt-4 text-[clamp(2.4rem,6vw,5.5rem)] font-extrabold uppercase leading-[0.9] tracking-tight [font-stretch:112%]">
        How I <span className="serif-accent normal-case text-flare">work</span>
      </h2>
      <div className="mt-14 flex flex-col gap-[8vh]">
        {site.process.map((step, i) => (
          <div key={step.title} className="sticky" style={{ top: `calc(14vh + ${i * 1.6}rem)` }}>
            <article className={`process-card relative grid min-h-[56vh] origin-top gap-8 rounded-[1.75rem] p-7 will-change-transform md:grid-cols-12 md:p-12 ${CARD_STYLES[i % CARD_STYLES.length]}`}>
              <span className="card-shade pointer-events-none absolute inset-0 rounded-[1.75rem] bg-void opacity-0" aria-hidden="true" />
              <div className="flex flex-col justify-between md:col-span-6">
                <p className="label opacity-70">
                  Step {pad(i + 1)} — {step.tagline}
                </p>
                <h3 className="mt-6 text-[clamp(3rem,9vw,8.5rem)] font-black uppercase leading-[0.85] tracking-tight [font-stretch:115%]">{step.title}</h3>
              </div>
              <div className="flex flex-col justify-between gap-8 md:col-span-5 md:col-start-8">
                <span className="text-[clamp(4rem,10vw,9rem)] font-black leading-none opacity-15 [font-stretch:125%]" aria-hidden="true">
                  {pad(i + 1)}
                </span>
                <div>
                  <p className="text-lg leading-relaxed opacity-85 md:text-xl">{step.text}</p>
                  <ul className="mt-6 flex flex-wrap gap-2">
                    {step.deliverables.map((d) => (
                      <li key={d} className="label rounded-full border border-current/25 px-3 py-1.5 opacity-80">
                        {d}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </article>
          </div>
        ))}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------ Experience */

export function Experience() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)
  useGSAP(
    () => {
      if (!ready || prefersReducedMotion()) return
      revealChars(ref.current!.querySelector('.xp-title')!)
      gsap.utils.toArray<HTMLElement>('.xp-row').forEach((row) => {
        gsap.from(row.querySelector('.xp-line'), { scaleX: 0, duration: 1.6, ease: 'expo.inOut', scrollTrigger: { trigger: row, start: 'top 90%', once: true } })
        gsap.from(row.querySelectorAll('.xp-cell'), { yPercent: 100, opacity: 0, duration: 1.2, stagger: 0.06, ease: 'expo.out', scrollTrigger: { trigger: row, start: 'top 90%', once: true } })
      })
    },
    { scope: ref, dependencies: [ready] },
  )
  return (
    <section ref={ref} id="experience" data-shot="experience" className="container-x relative py-28 md:py-36">
      <SectionLabel index={5}>Experience</SectionLabel>
      <h2 className="xp-title mt-4 text-[clamp(2.4rem,6vw,5.5rem)] font-extrabold uppercase leading-[0.9] tracking-tight [font-stretch:112%]">
        Trajectory
      </h2>
      <ul className="mt-14">
        {site.experience.map((job) => (
          <li key={job.years} className="xp-row group relative">
            <span className="xp-line hairline block origin-left" />
            <div className="relative grid grid-cols-2 gap-x-4 gap-y-2 overflow-hidden py-7 transition-colors duration-500 md:grid-cols-12 md:items-center md:py-9">
              <span className="absolute inset-0 origin-bottom scale-y-0 bg-ember transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-y-100" aria-hidden="true" />
              <span className="xp-cell label relative text-mute transition-colors group-hover:text-void md:col-span-2">{job.years}</span>
              <span className="xp-cell relative text-right text-sm text-mute transition-colors group-hover:text-void md:order-last md:col-span-2 md:text-base">{job.place}</span>
              <span className="xp-cell relative col-span-2 text-2xl font-bold tracking-tight transition-[color,font-stretch] duration-500 group-hover:text-void md:col-span-5 md:text-4xl md:group-hover:[font-stretch:118%]">
                {job.role}
              </span>
              <span className="xp-cell relative col-span-2 text-lg text-paper/70 transition-colors group-hover:text-void md:col-span-3">{job.company}</span>
            </div>
          </li>
        ))}
        <li className="hairline" />
      </ul>
    </section>
  )
}

/* ------------------------------------------------------------ Contact + footer */

export function Contact() {
  const ref = useRef<HTMLElement>(null)
  const ready = useApp((s) => s.ready)
  const [copied, setCopied] = useState(false)

  useGSAP(
    () => {
      if (!ready) return
      ref.current!.querySelectorAll('.contact-line').forEach((l, i) => revealChars(l, { delay: i * 0.12, start: 'top 90%' }))
      revealUp(ref.current!.querySelectorAll('.contact-fade'), ref.current!.querySelector('.contact-fade')!, { stagger: 0.08 })
    },
    { scope: ref, dependencies: [ready] },
  )

  useEffect(() => {
    if (!copied) return
    const id = window.setTimeout(() => setCopied(false), 2200)
    return () => window.clearTimeout(id)
  }, [copied])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(site.email)
      setCopied(true)
    } catch {
      window.location.href = `mailto:${site.email}`
    }
  }

  const [l1, l2, l3] = site.contact.headline
  return (
    <section ref={ref} id="contact" data-shot="contact" className="relative flex min-h-[110svh] flex-col justify-between pt-32">
      <div className="container-x">
        <SectionLabel index={6}>{site.contact.kicker}</SectionLabel>
        <h2 className="mt-8 text-[clamp(3rem,10vw,10rem)] font-black uppercase leading-[0.86] tracking-[-0.02em] [font-stretch:112%] [text-shadow:0_4px_40px_rgb(5_5_7/0.55)]">
          <span className="contact-line block">{l1}</span>
          <span className="contact-line block">{l2}</span>
          <span className="contact-line block serif-accent normal-case text-flare">{l3}</span>
        </h2>
        <div className="mt-12 grid gap-10 md:grid-cols-12 md:items-end">
          <p className="contact-fade max-w-sm text-lg leading-relaxed text-paper/80 md:col-span-4">{site.contact.text}</p>
          <div className="contact-fade flex flex-wrap items-center gap-4 md:col-span-8 md:justify-end">
            <Magnetic strength={0.4}>
              <a
                href={`mailto:${site.email}?subject=${encodeURIComponent('New project')}`}
                className="roll-host group relative grid h-40 w-40 place-items-center rounded-full bg-ember text-center font-bold text-void md:h-48 md:w-48"
              >
                <span className="label text-[0.8rem]">
                  <RollText text={site.contact.cta} />
                </span>
              </a>
            </Magnetic>
            <button type="button" onClick={copy} className="roll-host pill text-lg md:text-2xl" data-cursor={copied ? 'Copied' : 'Copy'}>
              <RollText text={site.email} />
              <span className="label text-ember">{copied ? 'Copied ✓' : 'Copy'}</span>
            </button>
          </div>
        </div>
      </div>

      <footer className="container-x mt-24 pb-8">
        <div className="hairline" />
        <div className="label mt-6 flex flex-col gap-6 text-mute md:flex-row md:items-center md:justify-between">
          <p>
            © {site.year} {site.name}
          </p>
          <ul className="flex flex-wrap gap-x-6 gap-y-2">
            {site.socials.map((s) => (
              <li key={s.label}>
                <a href={s.href} target="_blank" rel="noreferrer" className="roll-host text-paper">
                  <RollText text={s.label} />
                </a>
              </li>
            ))}
          </ul>
          <p>Built with React Three Fiber, GSAP & Lenis</p>
        </div>
      </footer>
    </section>
  )
}

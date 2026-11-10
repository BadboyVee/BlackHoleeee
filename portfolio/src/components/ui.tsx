import { useEffect, useRef, useState, type ReactNode } from 'react'
import { site } from '../content/site'
import { prefersReducedMotion } from '../lib/env'
import { gsap } from '../lib/gsap'
import { clamp } from '../lib/math'
import { onScroll, scroll, scrollTo, setScrollLocked } from '../lib/scroll'
import { useApp, useLoad } from '../lib/store'
import { extras } from '../three/backdrop/shots'

/* ------------------------------------------------------------ Logo */

export function Logo({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden="true" fill="none" stroke="currentColor">
      <circle cx="24" cy="24" r="9" strokeWidth="2.5" />
      <ellipse cx="24" cy="24" rx="21" ry="5.5" strokeWidth="2.5" transform="rotate(-16 24 24)" />
    </svg>
  )
}

/* ------------------------------------------------------------ Rolling text */

export function RollText({ text }: { text: string }) {
  const row = (clone: boolean) => (
    <span className={`roll__row${clone ? ' roll__row--clone' : ''}`} aria-hidden="true">
      {[...text].map((c, i) => (
        <span key={i} className="roll__char" style={{ '--i': i } as React.CSSProperties}>
          {c === ' ' ? ' ' : c}
        </span>
      ))}
    </span>
  )
  return (
    <span className="roll">
      <span className="sr-only">{text}</span>
      {row(false)}
      {row(true)}
    </span>
  )
}

/* ------------------------------------------------------------ Magnetic */

export function Magnetic({ children, strength = 0.35, className = '' }: { children: ReactNode; strength?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el || !window.matchMedia('(pointer: fine)').matches || prefersReducedMotion()) return
    const xTo = gsap.quickTo(el, 'x', { duration: 0.9, ease: 'elastic.out(1, 0.35)' })
    const yTo = gsap.quickTo(el, 'y', { duration: 0.9, ease: 'elastic.out(1, 0.35)' })
    let rect = el.getBoundingClientRect()
    const enter = () => (rect = el.getBoundingClientRect())
    const move = (e: PointerEvent) => {
      xTo((e.clientX - (rect.left + rect.width / 2)) * strength)
      yTo((e.clientY - (rect.top + rect.height / 2)) * strength)
    }
    const leave = () => {
      xTo(0)
      yTo(0)
    }
    el.addEventListener('pointerenter', enter)
    el.addEventListener('pointermove', move)
    el.addEventListener('pointerleave', leave)
    return () => {
      el.removeEventListener('pointerenter', enter)
      el.removeEventListener('pointermove', move)
      el.removeEventListener('pointerleave', leave)
    }
  }, [strength])
  return (
    <span ref={ref} className={`inline-block will-change-transform ${className}`}>
      {children}
    </span>
  )
}

/* ------------------------------------------------------------ Cursor */

export function Cursor() {
  const dot = useRef<HTMLDivElement>(null)
  const ring = useRef<HTMLDivElement>(null)
  const label = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!window.matchMedia('(pointer: fine)').matches) return
    const d = dot.current!
    const r = ring.current!
    const l = label.current!
    document.documentElement.classList.add('has-cursor')
    gsap.set([d, r, l], { xPercent: -50, yPercent: -50, x: -200, y: -200 })
    const q = (el: HTMLElement, duration: number) => [
      gsap.quickTo(el, 'x', { duration, ease: 'power3' }),
      gsap.quickTo(el, 'y', { duration, ease: 'power3' }),
    ]
    const [dx, dy] = q(d, 0.08)
    const [rx, ry] = q(r, 0.45)
    const [lx, ly] = q(l, 0.6)

    const move = (e: PointerEvent) => {
      dx(e.clientX)
      dy(e.clientY)
      rx(e.clientX)
      ry(e.clientY)
      lx(e.clientX)
      ly(e.clientY)
    }
    const over = (e: Event) => {
      const t = (e.target as Element).closest?.('[data-cursor], a, button')
      const text = t?.getAttribute('data-cursor')
      if (text) {
        l.textContent = text
        gsap.to(l, { scale: 1, duration: 0.6, ease: 'expo.out' })
        gsap.to([r, d], { scale: 0, duration: 0.4 })
      } else if (t) {
        gsap.to(l, { scale: 0, duration: 0.4 })
        gsap.to(r, { scale: 1.9, backgroundColor: 'rgba(241,236,227,1)', borderColor: 'rgba(241,236,227,0)', duration: 0.5, ease: 'expo.out' })
        gsap.to(d, { scale: 0, duration: 0.3 })
      } else {
        gsap.to(l, { scale: 0, duration: 0.4 })
        gsap.to(r, { scale: 1, backgroundColor: 'rgba(241,236,227,0)', borderColor: 'rgba(241,236,227,0.6)', duration: 0.5, ease: 'expo.out' })
        gsap.to(d, { scale: 1, duration: 0.3 })
      }
    }
    const down = () => gsap.to(r, { scale: '-=0.25', duration: 0.2 })
    const up = (e: Event) => over(e)
    window.addEventListener('pointermove', move, { passive: true })
    document.addEventListener('pointerover', over)
    window.addEventListener('pointerdown', down)
    window.addEventListener('pointerup', up)
    return () => {
      document.documentElement.classList.remove('has-cursor')
      window.removeEventListener('pointermove', move)
      document.removeEventListener('pointerover', over)
      window.removeEventListener('pointerdown', down)
      window.removeEventListener('pointerup', up)
    }
  }, [])

  return (
    <>
      <div aria-hidden="true" className="pointer-events-none fixed left-0 top-0 z-[70] mix-blend-difference">
        <div ref={ring} className="fixed left-0 top-0 h-9 w-9 rounded-full border border-paper/60" />
        <div ref={dot} className="fixed left-0 top-0 h-1.5 w-1.5 rounded-full bg-paper" />
      </div>
      <div
        ref={label}
        aria-hidden="true"
        className="label pointer-events-none fixed left-0 top-0 z-[71] grid h-24 w-24 scale-0 place-items-center rounded-full bg-ember font-semibold text-void"
      />
    </>
  )
}

/* ------------------------------------------------------------ Grain */

export function Grain() {
  const [url, setUrl] = useState('')
  useEffect(() => {
    const c = document.createElement('canvas')
    c.width = c.height = 180
    const ctx = c.getContext('2d')!
    const img = ctx.createImageData(180, 180)
    for (let i = 0; i < img.data.length; i += 4) {
      const v = Math.random() * 255
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v
      img.data[i + 3] = 255
    }
    ctx.putImageData(img, 0, 0)
    setUrl(c.toDataURL('image/png'))
  }, [])
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-[60] overflow-hidden opacity-[0.05]">
      <div
        className="absolute -inset-[180px] will-change-transform"
        style={{ backgroundImage: url ? `url(${url})` : undefined, animation: 'grain 0.9s steps(6) infinite' }}
      />
    </div>
  )
}

/* ------------------------------------------------------------ Preloader */

export function Preloader() {
  const setReady = useApp((s) => s.setReady)
  useEffect(() => {
    const root = document.getElementById('preloader')
    const count = document.getElementById('pl-count')
    const bar = document.getElementById('pl-bar')
    const status = document.getElementById('pl-status')
    const w = window as unknown as { __plTaken?: boolean; __plValue?: () => number }
    if (!root || !count || !bar || !status) {
      setReady()
      setScrollLocked(false)
      extras.intro = 1
      return
    }
    w.__plTaken = true
    let shown = w.__plValue?.() ?? 0
    let raf = 0
    let done = false
    const t0 = performance.now()
    const load = useLoad.getState()
    document.fonts.ready.then(() => load.report('fonts', 1))
    const safety = window.setTimeout(() => ['fonts', 'backdrop', 'scene'].forEach((t) => useLoad.getState().report(t, 1)), 9000)
    const messages = ['Bending light', 'Spinning up the disk', 'Calibrating gravity', 'Crossing the horizon']

    const exit = () => {
      const tl = gsap.timeline({
        onComplete: () => {
          root.remove()
          setScrollLocked(false)
        },
      })
      tl.to(root.querySelector('.pl-orbit'), { scale: 0, duration: 0.7, ease: 'expo.in' })
        .to(count, { yPercent: -40, opacity: 0, duration: 0.6, ease: 'expo.in' }, '<')
        .fromTo(root, { clipPath: 'inset(0% 0% 0% 0%)' }, { clipPath: 'inset(0% 0% 100% 0%)', duration: 1.25, ease: 'expo.inOut' }, '-=0.25')
        .add(() => {
          setReady()
          gsap.to(extras, { intro: 1, duration: prefersReducedMotion() ? 0.01 : 3.4, ease: 'power3.out' })
        }, '-=0.8')
    }

    const tick = () => {
      const tasks = Object.values(useLoad.getState().tasks)
      const loaded = (tasks.reduce((a, b) => a + b, 0) / tasks.length) * 100
      const elapsed = Math.min(1, (performance.now() - t0) / 1500)
      const goal = Math.min(loaded, 30 + elapsed * 70)
      shown += (goal - shown) * 0.09
      if (goal >= 100 && shown > 99.3) shown = 100
      count.textContent = String(Math.round(shown)).padStart(3, '0')
      bar.style.transform = `scaleX(${shown / 100})`
      status.textContent = messages[Math.min(3, Math.floor(shown / 25))]
      if (shown >= 100 && !done) {
        done = true
        exit()
        return
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      window.clearTimeout(safety)
    }
  }, [setReady])
  return null
}

/* ------------------------------------------------------------ Clock */

export function Clock({ className = '' }: { className?: string }) {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])
  const time = new Intl.DateTimeFormat('en-GB', { timeZone: site.timezone, hour: '2-digit', minute: '2-digit' }).format(now)
  const [h, m] = time.split(':')
  return (
    <span className={className}>
      {site.location.split(',')[0]} {h}
      <span className={now.getSeconds() % 2 ? 'opacity-30' : ''}>:</span>
      {m}
    </span>
  )
}

/* ------------------------------------------------------------ Header + menu */

function go(href: string, close?: () => void) {
  return (e: React.MouseEvent) => {
    e.preventDefault()
    close?.()
    scrollTo(href)
  }
}

export function Header() {
  const ref = useRef<HTMLElement>(null)
  const menuOpen = useApp((s) => s.menuOpen)
  const setMenuOpen = useApp((s) => s.setMenuOpen)
  const menu = useRef<HTMLDivElement>(null)

  useEffect(
    () =>
      onScroll((s) => {
        const hide = s.direction === 1 && s.y > 240 && !useApp.getState().menuOpen
        ref.current?.style.setProperty('transform', hide ? 'translateY(-110%)' : 'translateY(0)')
      }),
    [],
  )

  useEffect(() => {
    const el = menu.current
    if (!el) return
    setScrollLocked(menuOpen)
    if (menuOpen) {
      gsap.set(el, { visibility: 'visible' })
      gsap.fromTo(el, { clipPath: 'circle(0% at 100% 0%)' }, { clipPath: 'circle(150% at 100% 0%)', duration: 1.1, ease: 'expo.inOut' })
      gsap.fromTo(el.querySelectorAll('[data-menu-item]'), { yPercent: 120 }, { yPercent: 0, duration: 1.2, stagger: 0.06, delay: 0.35, ease: 'expo.out' })
    } else if (el.style.visibility === 'visible') {
      gsap.to(el, { clipPath: 'circle(0% at 100% 0%)', duration: 0.8, ease: 'expo.inOut', onComplete: () => gsap.set(el, { visibility: 'hidden' }) })
    }
  }, [menuOpen])

  const close = () => setMenuOpen(false)

  return (
    <>
      <header ref={ref} className="fixed inset-x-0 top-0 z-50 text-paper mix-blend-difference transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]">
        <div className="container-x flex h-20 items-center justify-between gap-6">
          <a href="#top" onClick={go('#top', close)} className="roll-host flex items-center gap-3" aria-label={`${site.name}, back to top`}>
            <Logo className="h-7 w-7 transition-transform duration-700 hover:rotate-180" />
            <span className="label hidden font-semibold xs:inline">
              <RollText text={site.name} />
            </span>
          </a>
          <nav className="label hidden items-center gap-9 md:flex" aria-label="Main">
            {site.nav.map((item) => (
              <a key={item.href} href={item.href} onClick={go(item.href)} className="roll-host">
                <RollText text={item.label} />
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-5">
            <Clock className="label hidden tabular-nums lg:inline" />
            <Magnetic className="hidden md:inline-block">
              <a href="#contact" onClick={go('#contact')} className="roll-host pill label">
                <span className="h-1.5 w-1.5 rounded-full bg-paper" />
                <RollText text="Let’s talk" />
              </a>
            </Magnetic>
            <button
              type="button"
              className="label flex items-center gap-3 md:hidden"
              aria-expanded={menuOpen}
              aria-controls="menu"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              {menuOpen ? 'Close' : 'Menu'}
              <span className="relative block h-3 w-6">
                <span className={`absolute left-0 h-px w-full bg-paper transition-transform duration-500 ${menuOpen ? 'top-1.5 rotate-45' : 'top-0.5'}`} />
                <span className={`absolute left-0 h-px w-full bg-paper transition-transform duration-500 ${menuOpen ? 'top-1.5 -rotate-45' : 'top-2.5'}`} />
              </span>
            </button>
          </div>
        </div>
      </header>

      <div ref={menu} id="menu" className="invisible fixed inset-0 z-40 flex flex-col justify-between bg-ash px-6 pb-10 pt-28" aria-hidden={!menuOpen}>
        <nav className="flex flex-col gap-1" aria-label="Mobile">
          {site.nav.map((item, i) => (
            <a key={item.href} href={item.href} onClick={go(item.href, close)} className="overflow-hidden text-[15vw] font-extrabold uppercase leading-[0.95] tracking-tight [font-stretch:112%]">
              <span data-menu-item className="flex items-baseline gap-3">
                <span className="label text-ember">0{i + 1}</span>
                {item.label}
              </span>
            </a>
          ))}
        </nav>
        <div className="label flex flex-col gap-4 text-mute">
          <a href={`mailto:${site.email}`} className="text-paper">{site.email}</a>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            {site.socials.map((s) => (
              <a key={s.label} href={s.href} target="_blank" rel="noreferrer">{s.label}</a>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

/* ------------------------------------------------------------ Marquee */

export function Marquee({ items, reverse = false, className = '' }: { items: string[]; reverse?: boolean; className?: string }) {
  const track = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = track.current
    if (!el || prefersReducedMotion()) return
    let x = 0
    const dir = reverse ? 1 : -1
    const tick = (_time: number, delta: number) => {
      const half = el.scrollWidth / 2
      if (!half) return
      const v = scroll.velocity
      const sign = v < -0.4 ? -1 : 1
      x += dir * sign * (1.1 + Math.min(Math.abs(v) * 0.35, 16)) * (delta / 16.7)
      if (x <= -half) x += half
      if (x > 0) x -= half
      el.style.transform = `translate3d(${x}px,0,0) skewX(${clamp(-v * 0.3, -9, 9)}deg)`
    }
    gsap.ticker.add(tick)
    return () => gsap.ticker.remove(tick)
  }, [reverse])
  return (
    <div className={`overflow-hidden whitespace-nowrap ${className}`}>
      <div ref={track} className="inline-flex will-change-transform">
        {[0, 1].map((copy) => (
          <div key={copy} aria-hidden={copy === 1 || undefined} className="flex shrink-0 items-center">
            {items.map((t, i) => (
              <span key={i} className="flex items-center">
                {t}
                <span className="mx-[0.45em] text-[0.45em]">✦</span>
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------ Scroll progress */

export function ScrollProgress() {
  const ring = useRef<SVGCircleElement>(null)
  const wrap = useRef<HTMLButtonElement>(null)
  useEffect(
    () =>
      onScroll((s) => {
        ring.current?.style.setProperty('stroke-dashoffset', String(113.1 * (1 - s.progress)))
        const show = s.y > window.innerHeight * 0.6
        wrap.current?.style.setProperty('opacity', show ? '1' : '0')
        wrap.current?.style.setProperty('transform', show ? 'scale(1)' : 'scale(0.6)')
      }),
    [],
  )
  return (
    <button
      ref={wrap}
      type="button"
      onClick={() => scrollTo(0)}
      aria-label="Back to top"
      className="fixed bottom-5 right-5 z-50 grid h-12 w-12 place-items-center rounded-full bg-void/80 text-paper opacity-0 transition-[opacity,transform] duration-500 md:bottom-8 md:right-8"
    >
      <svg viewBox="0 0 40 40" className="absolute inset-0 -rotate-90" aria-hidden="true">
        <circle cx="20" cy="20" r="18" fill="none" stroke="rgb(241 236 227 / 0.15)" strokeWidth="1.5" />
        <circle ref={ring} cx="20" cy="20" r="18" fill="none" stroke="#ff5b1f" strokeWidth="1.5" strokeDasharray="113.1" strokeDashoffset="113.1" strokeLinecap="round" />
      </svg>
      <span aria-hidden="true">↑</span>
    </button>
  )
}

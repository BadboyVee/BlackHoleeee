import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { RenaissanceStage } from "./renaissance-stage";

const POSITION: [number, number] = [0.64, 0.42];

/** The index down the left edge, like the contents page of an edition. */
const index = [
  { href: "#services", label: "Launch campaigns" },
  { href: "#services", label: "Always-on posting" },
  { href: "#services", label: "Founder content" },
  { href: "#proof", label: "Proof" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#creators", label: "For creators" },
  { href: "/campaigns", label: "Open campaigns" },
  { href: "#faq", label: "FAQ" },
];

const NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

function Line({ children, delay }: { children: React.ReactNode; delay: number }) {
  return (
    <span className="block overflow-hidden pb-[0.08em]">
      <span className="block animate-line" style={{ animationDelay: `${delay}ms` }}>
        {children}
      </span>
    </span>
  );
}

/**
 * Renaissance hero, after Shopify Editions: a full-bleed old master with the
 * type set small, bold and white over it. A short title top left, the index
 * of the page bottom left, a credit for the painting bottom right.
 */
function RenaissanceHero() {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative isolate min-h-[100svh] overflow-hidden bg-[#1f2a1b] text-white"
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- matched by a preload with the same srcset */}
      <img
        src="/art/orion-1600.webp"
        srcSet="/art/orion-1600.webp 1600w, /art/orion-2400.webp 2400w"
        sizes="(max-aspect-ratio: 1535/1000) 154vh, 100vw"
        alt=""
        loading="lazy"
        decoding="async"
        className="absolute inset-0 size-full scale-[1.0152] object-cover object-[64%_42%] animate-fade-in"
      />
      <RenaissanceStage position={POSITION} />

      {/* Legibility: darker at the left and the bottom, where the type sits. */}
      <div aria-hidden className="absolute inset-0 bg-linear-to-r from-black/45 via-black/5 to-transparent" />
      <div aria-hidden className="absolute inset-x-0 bottom-0 h-3/5 bg-linear-to-t from-black/55 via-black/15 to-transparent" />

      <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-[90rem] flex-col px-4 pt-24 pb-5 sm:px-6 sm:pb-6 lg:px-8 lg:pt-28">
        <h1
          id="hero-title"
          className="max-w-[14ch] text-[clamp(2.5rem,1.4rem+3.6vw,4.75rem)] leading-[0.9] font-bold tracking-[-0.05em] [text-shadow:0_1px_24px_rgb(0_0_0/0.25)]"
        >
          <Line delay={500}>Make your</Line>
          <Line delay={590}>launch</Line>
          <Line delay={680}>legendary.</Line>
        </h1>
        <p
          className="mt-5 max-w-[21rem] animate-rise text-[15px] leading-snug font-medium text-white/88 [text-shadow:0_1px_12px_rgb(0_0_0/0.4)]"
          style={{ animationDelay: "820ms" }}
        >
          We brief the creators your users already follow. They post on X, and your launch travels.
        </p>
        <div className="mt-6 flex animate-rise flex-wrap gap-2.5" style={{ animationDelay: "900ms" }}>
          <Link
            href="/book"
            className="pressable group inline-flex h-11 items-center gap-2 rounded-full bg-white px-5 text-[14px] font-semibold text-[#141210] shadow-[0_8px_30px_rgb(0_0_0/0.25)] transition-[background-color,box-shadow] duration-300 ease-snap hover:bg-brand hover:shadow-[0_8px_40px_rgb(255_46_138/0.45)]"
          >
            Book a campaign
            <ArrowRight className="size-4 transition-transform duration-300 ease-snap group-hover:translate-x-0.5" />
          </Link>
          <Link
            href="/apply"
            className="pressable inline-flex h-11 items-center rounded-full px-5 text-[14px] font-semibold text-white ring-1 ring-white/55 backdrop-blur-sm transition-colors duration-300 ease-snap ring-inset hover:bg-white/15"
          >
            Apply as a creator
          </Link>
        </div>

        <div className="mt-auto flex items-end justify-between gap-6 pt-12">
          <nav aria-label="On this page">
            <ol className="grid w-[13.5rem] gap-0.5 sm:w-[15rem]">
              {index.map((item, i) => (
                <li key={item.label} className={i > 5 ? "hidden sm:block" : undefined}>
                  <Link
                    href={item.href}
                    className="group flex animate-rise items-baseline justify-between gap-3 py-[1px] text-[clamp(0.95rem,0.85rem+0.25vw,1.0625rem)] leading-[1.05] font-bold tracking-[-0.03em]"
                    style={{ animationDelay: `${1000 + i * 45}ms` }}
                  >
                    <span className="relative transition-transform duration-300 ease-snap group-hover:translate-x-1.5">
                      <span
                        aria-hidden
                        className="absolute top-1/2 -left-3 size-1.5 -translate-y-1/2 scale-0 rounded-full bg-brand transition-transform duration-300 ease-snap group-hover:scale-100"
                      />
                      {item.label}
                    </span>
                    <span className="text-[10px] font-semibold tracking-[0.04em] text-white/55">
                      {NUMERALS[i]}
                    </span>
                  </Link>
                </li>
              ))}
            </ol>
            <p className="mt-4 flex gap-3 text-[11px] font-medium text-white/60">
              <Link href="/terms" className="hover:text-white">
                Terms
              </Link>
              <Link href="/privacy" className="hover:text-white">
                Privacy
              </Link>
            </p>
          </nav>
          <p className="hidden max-w-[17rem] animate-fade-in text-right text-[11px] leading-snug text-white/70 [animation-delay:1.4s] md:block">
            Nicolas Poussin, <em>Blind Orion Searching for the Rising Sun</em>, 1658. The Metropolitan
            Museum of Art, public domain.
          </p>
        </div>
      </div>
      <div data-hero-end aria-hidden className="absolute bottom-0 left-0 h-px w-px" />
    </section>
  );
}

export { RenaissanceHero };

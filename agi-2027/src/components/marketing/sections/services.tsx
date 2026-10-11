import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Check, Megaphone, Repeat, UserRound } from "lucide-react";

import { RevealGroup, RevealItem } from "@/components/motion/reveal";
import { services } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";
import { EchoSays, SectionShell, SectionTitle } from "./shared";

const ART = ["/art/detail-clouds.webp", "/art/detail-trees.webp", "/art/detail-river.webp"];
const ART_ALT = [
  "Clouds and the goddess Diana, a detail from Poussin's Blind Orion",
  "Tall trees in morning light, a detail from Claude Lorrain's Sunrise",
  "A river bend in sunlight, a detail from Thomas Cole's The Oxbow",
];
const ICONS = [Megaphone, Repeat, UserRound];
const DROP_ICONS = ["bolt", "bars", "bubble"];

/**
 * What we sell, as a bento of three. Renaissance hangs a painting detail in
 * each tile, Agent uses red, ink and blush panels, Drop gives each a juicy
 * color and a glossy icon.
 */
function ServicesSection() {
  return (
    <SectionShell id="services" label="Services">
      <EchoSays>Three ways I can help, depending on what you&apos;re shipping.</EchoSays>
      <SectionTitle
        title="What we do."
        lead="Launch days, a steady drumbeat, or your founder's voice. Each one is planned around your dates."
      />
      <RevealGroup className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-[1.25fr_1fr] lg:grid-rows-2">
        {services.map((service, index) => {
          const Icon = ICONS[index];
          return (
            <RevealItem
              key={service.title}
              className={cn(index === 0 && "md:col-span-2 lg:col-span-1 lg:row-span-2")}
            >
              <article
                className={cn(
                  "group relative isolate flex h-full min-h-[22rem] flex-col justify-end overflow-hidden rounded-[var(--radius-xl)] p-6 sm:p-8",
                  "transition-[transform,box-shadow] duration-300 ease-snap hover:-translate-y-1 hover:shadow-float",
                  // Renaissance: painting with a dark scrim; text in white.
                  "renaissance:text-white",
                  // Agent: red, ink, blush.
                  index === 0 && "agent:bg-block-1 agent:text-white",
                  index === 1 && "agent:bg-block-2 agent:text-white",
                  index === 2 && "agent:bg-block-3 agent:text-foreground",
                  // Drop: juicy blocks.
                  index === 0 && "drop:bg-block-1 drop:text-white",
                  index === 1 && "drop:bg-block-3 drop:text-white",
                  index === 2 && "drop:bg-block-4 drop:text-white",
                  index === 0 && "lg:min-h-[34rem]",
                  "drop:pt-28",
                )}
              >
                <div className="look-renaissance">
                  <div className="absolute inset-0 -z-10 overflow-hidden">
                    <Image
                      src={ART[index]}
                      alt={ART_ALT[index]}
                      fill
                      sizes="(min-width: 1024px) 45vw, (min-width: 768px) 50vw, 100vw"
                      className="object-cover transition-transform duration-[1.4s] ease-snap group-hover:scale-105"
                    />
                    <span aria-hidden className="absolute inset-0 bg-linear-to-t from-black/75 via-black/25 to-black/5" />
                  </div>
                </div>
                <div className="look-agent">
                  <span className="absolute top-6 left-6 flex size-12 items-center justify-center rounded-full bg-white/15 ring-1 ring-white/25 transition-transform duration-500 ease-spring-snappy group-hover:-rotate-12 sm:top-8 sm:left-8">
                    <Icon className="size-5" aria-hidden />
                  </span>
                </div>
                <div className="look-drop">
                  {/* eslint-disable-next-line @next/next/no-img-element -- small decorative sprite */}
                  <img
                    src={`/art/icons/${DROP_ICONS[index]}.webp`}
                    alt=""
                    aria-hidden
                    className={cn(
                      "absolute top-5 right-5 drop-shadow-[0_16px_20px_rgb(0_0_0/0.25)] transition-transform duration-700 ease-spring-snappy group-hover:-translate-y-2 group-hover:rotate-12",
                      index === 0 ? "w-28 sm:w-40" : "w-20 sm:w-24",
                    )}
                  />
                </div>

                <h3 className="max-w-[16ch] text-[clamp(1.75rem,1.2rem+1.8vw,2.75rem)] leading-[0.95] font-bold tracking-[-0.045em] agent:font-medium drop:font-[family-name:var(--font-anton)] drop:text-[clamp(2.25rem,1.5rem+2.6vw,3.75rem)] drop:font-normal drop:tracking-[0.01em] drop:uppercase">
                  {service.title}
                </h3>
                <p className="mt-3 max-w-md text-[15.5px] leading-relaxed opacity-90">{service.description}</p>
                <ul className="mt-5 flex flex-wrap gap-2">
                  {service.points.map((point) => (
                    <li
                      key={point}
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-[13px] font-medium ring-1 ring-white/25 backdrop-blur-sm",
                        index === 2 && "agent:bg-foreground/5 agent:ring-foreground/15",
                      )}
                    >
                      <Check className="size-3.5" aria-hidden />
                      {point}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/book"
                  className="absolute top-6 right-6 inline-flex size-11 items-center justify-center rounded-full bg-white text-[#16120f] opacity-0 shadow-soft transition-[opacity,transform] duration-300 ease-snap group-hover:opacity-100 group-hover:rotate-45 focus-visible:opacity-100 sm:top-8 sm:right-8 drop:hidden"
                  aria-label={`Book ${service.title.toLowerCase()}`}
                >
                  <ArrowUpRight className="size-5" />
                </Link>
              </article>
            </RevealItem>
          );
        })}
      </RevealGroup>
    </SectionShell>
  );
}

export { ServicesSection };

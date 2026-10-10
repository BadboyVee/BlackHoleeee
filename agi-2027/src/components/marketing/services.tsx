import { Check } from "lucide-react";

import { services } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";
import { Section, SectionHeader } from "./section";

/** Post volume over a week, spiking inside the launch window. */
function LaunchWave() {
  const bars = Array.from({ length: 44 }, (_, i) => {
    const inWindow = i >= 18 && i <= 27;
    const base = 6 + ((i * 37) % 11);
    const peak = inWindow ? 26 + Math.round(Math.sin(((i - 18) / 9) * Math.PI) * 58) : 0;
    return { height: base + peak, inWindow };
  });
  return (
    <div className="relative mt-8 h-36">
      <div className="absolute inset-y-0 left-[38%] w-[22%] rounded-lg border border-dashed border-border-strong" />
      <p className="absolute top-2 left-[38%] w-[22%] text-center text-label text-subtle-foreground">Launch window</p>
      <div className="absolute inset-x-0 bottom-0 flex h-28 items-end gap-[3px]">
        {bars.map((bar, i) => (
          <span
            key={i}
            className={cn("flex-1 rounded-[2px]", bar.inWindow ? "bg-foreground" : "bg-foreground/12")}
            style={{ height: `${bar.height}%` }}
          />
        ))}
      </div>
    </div>
  );
}

/** A month of posting days. */
function PostingCalendar() {
  const active = new Set([1, 4, 8, 9, 11, 15, 18, 22, 23, 25]);
  const highlight = new Set([9, 23]);
  return (
    <div className="mt-8 grid grid-cols-7 gap-1.5">
      {Array.from({ length: 28 }, (_, day) => (
        <span
          key={day}
          className={cn(
            "aspect-square rounded-[5px]",
            highlight.has(day) ? "bg-foreground" : active.has(day) ? "bg-foreground/30" : "bg-foreground/7",
          )}
        />
      ))}
    </div>
  );
}

/** A founder thread, sketched. */
function ThreadSketch() {
  return (
    <div className="mt-8 space-y-4">
      {[0.92, 0.7, 0.82].map((width, i) => (
        <div key={i} className="flex gap-3">
          <div className="flex flex-col items-center">
            <span className={cn("size-7 rounded-full", i === 0 ? "bg-foreground/35" : "bg-foreground/15")} />
            {i < 2 ? <span className="mt-1.5 w-px flex-1 bg-border-strong" /> : null}
          </div>
          <div className="flex-1 space-y-2 pt-1">
            <span className="block h-2 rounded-full bg-foreground/20" style={{ width: `${width * 100}%` }} />
            <span className="block h-2 rounded-full bg-foreground/10" style={{ width: `${width * 70}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

const visuals = [<LaunchWave key="wave" />, <PostingCalendar key="calendar" />, <ThreadSketch key="thread" />];

function Services() {
  return (
    <Section id="services">
      <SectionHeader kicker="What we do" title="Three ways to *own* the conversation." />
      <div className="mt-14 grid gap-4 lg:grid-cols-3">
        {services.map((service, index) => (
          <article
            key={service.title}
            className={cn(
              "relative flex flex-col rounded-2xl border bg-surface p-6 shadow-soft sm:p-8",
              index === 0 && "lg:col-span-2",
              index === 2 && "lg:col-span-3 lg:grid lg:grid-cols-2 lg:items-center lg:gap-12",
            )}
          >
            <div>
              <h3 className="text-xl font-semibold tracking-[-0.025em]">{service.title}</h3>
              <p className="mt-2.5 max-w-md text-[15px] text-pretty text-muted-foreground">{service.description}</p>
              <ul className="mt-5 space-y-2">
                {service.points.map((point) => (
                  <li key={point} className="flex items-center gap-2.5 text-sm text-muted-foreground">
                    <Check className="size-3.5 shrink-0 text-brand-text" aria-hidden />
                    {point}
                  </li>
                ))}
              </ul>
            </div>
            <div aria-hidden className={cn(index === 2 && "lg:-mt-8")}>
              {visuals[index]}
            </div>
          </article>
        ))}
      </div>
    </Section>
  );
}

export { Services };

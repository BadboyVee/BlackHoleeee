import { RevealGroup, RevealItem } from "@/components/motion/reveal";
import { CountUp } from "@/components/ui/count-up";
import { stats } from "@/lib/marketing-content";
import { formatUtcDateSpan } from "@/lib/time";
import { EchoSays } from "./shared";

/**
 * The network in four real numbers, counting up as they arrive. Each one is
 * worked out from the data (src/lib/marketing-content.ts), and a number taken
 * from X says which day it's from. Renaissance sets them like a museum
 * banner, Agent in a red panel Echo introduces, Drop in a juicy color block.
 * On those colors the small text stays full white, so it's easy to read. From
 * lg to xl the four numbers share a row, so they grow more slowly there and
 * never run into each other.
 */
function StatsSection() {
  return (
    <section aria-label="AGI 2027 in numbers" className="relative px-3 pt-16 pb-6 sm:px-5 sm:pt-24">
      <div className="mx-auto max-w-[84rem] px-2 sm:px-3 lg:px-5">
        <EchoSays>Some numbers, since you asked.</EchoSays>
      </div>
      <div className="mx-auto max-w-[84rem] renaissance:border-y renaissance:border-border-strong renaissance:px-2 renaissance:py-10 renaissance:sm:px-3 renaissance:lg:px-5 agent:rounded-[2.5rem] agent:bg-block-1 agent:px-6 agent:py-12 agent:text-white agent:sm:px-10 agent:sm:py-14 drop:rounded-[2.25rem] drop:bg-block-2 drop:px-6 drop:py-12 drop:text-white drop:sm:px-10 drop:sm:py-16">
        <RevealGroup className="grid grid-cols-2 gap-x-6 gap-y-10 lg:grid-cols-4">
          {stats.map((stat) => (
            <RevealItem key={stat.label}>
              <CountUp
                value={stat.value}
                format={stat.format}
                suffix={stat.suffix}
                className="block text-[clamp(2.75rem,1.5rem+4.6vw,5.75rem)] leading-[0.9] font-bold tracking-[-0.055em] tabular-nums lg:max-xl:text-[length:calc(7.4vw_-_11.6px)] agent:font-medium drop:font-[family-name:var(--font-anton)] drop:text-[clamp(3.25rem,1.8rem+5.4vw,7rem)] drop:font-normal drop:tracking-[0.01em] drop:lg:max-xl:text-[length:calc(9.3vw_-_21px)]"
              />
              <p className="mt-3 text-[15px] leading-snug text-balance text-muted-foreground agent:text-white drop:text-white">
                {stat.label}
              </p>
              {stat.asOf ? (
                <p className="mt-1 text-xs text-subtle-foreground agent:text-white drop:text-white">
                  From X, {formatUtcDateSpan(stat.asOf.from, stat.asOf.to)}
                </p>
              ) : null}
            </RevealItem>
          ))}
        </RevealGroup>
      </div>
    </section>
  );
}

export { StatsSection };

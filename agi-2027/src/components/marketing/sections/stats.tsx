import { RevealGroup, RevealItem } from "@/components/motion/reveal";
import { CountUp } from "@/components/ui/count-up";
import { stats } from "@/lib/marketing-content";
import { EchoSays } from "./shared";

/**
 * The network in four numbers, counting up as they arrive. Renaissance sets
 * them like a museum banner, Agent in a red panel Echo introduces, Drop in a
 * juicy color block.
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
                className="block text-[clamp(2.75rem,1.5rem+4.6vw,5.75rem)] leading-[0.9] font-bold tracking-[-0.055em] tabular-nums agent:font-medium drop:font-[family-name:var(--font-anton)] drop:text-[clamp(3.25rem,1.8rem+5.4vw,7rem)] drop:font-normal drop:tracking-[0.01em]"
              />
              <p className="mt-3 text-[15px] leading-snug text-muted-foreground agent:text-white/85 drop:text-white/90">
                {stat.label}
              </p>
            </RevealItem>
          ))}
        </RevealGroup>
      </div>
    </section>
  );
}

export { StatsSection };

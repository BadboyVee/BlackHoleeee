import Image from "next/image";

import { RevealGroup, RevealItem, RuleDraw } from "@/components/motion/reveal";
import { steps } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";
import { EchoSays, SectionShell, SectionTitle } from "./shared";

const DROP_BLOCKS = ["drop:bg-block-1", "drop:bg-block-2", "drop:bg-block-3", "drop:bg-block-4", "drop:bg-block-5"];

/**
 * The process in five steps. Renaissance draws a hairline over each step as
 * it arrives, Agent has Echo explain it as a chat, Drop lines up five juicy
 * cards you can swipe through on a phone.
 */
function HowItWorksSection() {
  return (
    <SectionShell id="how-it-works" label="How it works">
      <SectionTitle
        title="How a campaign runs."
        lead="From your brief to a report you can forward to investors, usually inside a week."
      />
      <EchoSays className="mt-10 mb-0">Here&apos;s how I run it, step by step.</EchoSays>
      <RevealGroup
        as="ol"
        className={cn(
          "mt-12 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-5",
          "agent:mt-4 agent:flex agent:max-w-2xl agent:flex-col agent:gap-3 agent:pl-[3.75rem]",
          "drop:-mx-5 drop:flex drop:snap-x drop:snap-mandatory drop:gap-3 drop:overflow-x-auto drop:px-5 drop:pb-4 drop:[scrollbar-width:none] drop:lg:mx-0 drop:lg:grid drop:lg:overflow-visible drop:lg:px-0",
        )}
      >
        {steps.map((step, index) => (
          <RevealItem
            as="li"
            key={step.title}
            className={cn(
              "relative",
              "renaissance:pt-6",
              "agent:w-fit agent:max-w-full agent:rounded-[1.4rem] agent:bg-surface agent:px-5 agent:py-4 agent:shadow-soft agent:ring-1 agent:ring-border",
              index === 0 && "agent:rounded-tl-md",
              "drop:flex drop:min-h-[19rem] drop:w-[78%] drop:shrink-0 drop:snap-center drop:flex-col drop:justify-between drop:rounded-[1.75rem] drop:p-6 drop:text-white drop:sm:w-[46%] drop:lg:w-auto",
              DROP_BLOCKS[index],
            )}
          >
            <span className="look-renaissance">
              <RuleDraw className="absolute inset-x-0 top-0 block h-px bg-foreground" />
            </span>
            <p className="text-[13px] font-semibold text-muted-foreground tabular-nums agent:hidden drop:font-[family-name:var(--font-anton)] drop:text-[64px] drop:leading-none drop:font-normal drop:text-white/35">
              {String(index + 1).padStart(2, "0")}
            </p>
            <div>
              <h3 className="mt-3 text-[clamp(1.75rem,1.3rem+1.4vw,2.5rem)] leading-none font-bold tracking-[-0.045em] agent:mt-0 agent:text-[17px] agent:leading-snug agent:font-semibold agent:tracking-[-0.015em] drop:font-[family-name:var(--font-anton)] drop:text-[44px] drop:font-normal drop:tracking-[0.01em] drop:uppercase">
                {step.title}
                <span className="look-agent">.</span>
              </h3>
              <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground agent:mt-1 agent:text-foreground/80 drop:text-white/90">
                {step.description}
              </p>
            </div>
          </RevealItem>
        ))}
      </RevealGroup>
      <div className="look-agent">
        <div aria-hidden className="mt-3 flex max-w-2xl items-center gap-3">
          <Image src="/art/echo-avatar.webp" alt="" width={48} height={48} className="size-12 rounded-full bg-[#d92e24] ring-2 ring-surface" />
          <span className="flex gap-1 rounded-full bg-surface px-4 py-3 shadow-soft ring-1 ring-border">
            {[0, 1, 2].map((dot) => (
              <span
                key={dot}
                className="size-1.5 animate-pulse rounded-full bg-muted-foreground"
                style={{ animationDelay: `${dot * 180}ms` }}
              />
            ))}
          </span>
        </div>
      </div>
    </SectionShell>
  );
}

export { HowItWorksSection };

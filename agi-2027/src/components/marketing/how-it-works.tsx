import { steps } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";
import { Section, SectionHeader } from "./section";

function HowItWorks() {
  return (
    <Section id="how-it-works">
      <SectionHeader kicker="How it works" title="From brief to report, in *five* steps." />
      <ol className="mt-14 grid gap-px overflow-hidden rounded-2xl border bg-border shadow-soft sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((step, index) => (
          <li
            key={step.title}
            className={cn(
              "flex flex-col bg-surface p-6 sm:p-7",
              index === steps.length - 1 && "sm:col-span-2 lg:col-span-1",
            )}
          >
            <span className="font-mono text-sm text-subtle-foreground tabular">0{index + 1}</span>
            <h3 className="mt-10 text-h3">{step.title}</h3>
            <p className="mt-2 text-sm text-pretty text-muted-foreground">{step.description}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}

export { HowItWorks };

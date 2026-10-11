import Image from "next/image";

import { Reveal, WordReveal } from "@/components/motion/reveal";
import { cn } from "@/lib/utils";

/** A home page section: consistent widths and spacing in every look. */
function SectionShell({
  id,
  label,
  className,
  innerClassName,
  children,
}: {
  id?: string;
  label?: string;
  className?: string;
  innerClassName?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} aria-label={label} className={cn("relative scroll-mt-20 py-20 sm:py-28", className)}>
      <div className={cn("mx-auto max-w-[84rem] px-5 sm:px-8 lg:px-10", innerClassName)}>{children}</div>
    </section>
  );
}

/**
 * A section heading in the active look's voice: bold grotesk (Renaissance),
 * soft and medium (Agent), or giant condensed capitals (Drop).
 */
function SectionTitle({
  title,
  lead,
  className,
  align = "left",
}: {
  title: string;
  lead?: string;
  className?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={cn("max-w-3xl", align === "center" && "mx-auto text-center", className)}>
      <WordReveal text={title} className="text-h2 text-balance" />
      {lead ? (
        <Reveal as="p" delay={0.12} className="mt-5 max-w-[34rem] text-lead text-pretty text-muted-foreground">
          {lead}
        </Reveal>
      ) : null}
    </div>
  );
}

/** Agent look: Echo introduces a section in a speech bubble. */
function EchoSays({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className="look-agent">
      <Reveal className={cn("mb-8 flex items-end gap-3", className)}>
        <Image
          src="/art/echo-avatar.webp"
          alt=""
          width={48}
          height={48}
          className="size-12 shrink-0 rounded-full bg-[#d92e24] ring-2 ring-surface"
        />
        <p className="relative max-w-sm rounded-[1.4rem] rounded-bl-md bg-surface px-4 py-3 text-[15px] leading-snug shadow-soft ring-1 ring-border">
          {children}
        </p>
      </Reveal>
    </div>
  );
}

export { EchoSays, SectionShell, SectionTitle };

import type { Metadata } from "next";
import Image from "next/image";
import { Mail } from "lucide-react";

import { MarketingMain } from "@/components/layout/marketing-main";
import { BookForm } from "@/components/marketing/book-form";
import { siteConfig } from "@/lib/site";
import { cn } from "@/lib/utils";

const DESCRIPTION = "Tell us what you're launching and when. We'll come back with a plan and the right creators.";

export const metadata: Metadata = {
  title: "Book a campaign",
  description: DESCRIPTION,
  alternates: { canonical: "/book" },
};

const NEXT_STEPS = [
  {
    title: "We reply within one working day",
    body: "Your brief goes straight to the team. A person reads it and writes back.",
  },
  {
    title: "A short call",
    body: "We talk through the launch, who it's for and the date that matters.",
  },
  {
    title: "A plan with the right creators",
    body: "Who posts, what they say and when, with a clear budget before anything goes live.",
  },
];

/**
 * Book a campaign: the form, with what happens next beside it on wide
 * screens and under it on phones. Renaissance hangs a painting detail over
 * the steps, Agent has Echo walk through them, Drop puts them on a color block.
 */
export default function BookPage() {
  const email = siteConfig.contactEmail;
  return (
    <MarketingMain>
      <div className="mx-auto max-w-6xl px-4 pt-12 pb-16 sm:px-6 sm:pt-20 sm:pb-24 lg:px-8">
        <header className="max-w-3xl">
          <div className="look-agent">
            <div className="mb-6 flex animate-rise items-end gap-3">
              <Image
                src="/art/echo-avatar.webp"
                alt=""
                width={56}
                height={56}
                className="size-14 shrink-0 rounded-full bg-[#d92e24] ring-2 ring-surface"
              />
              <p className="max-w-xs rounded-[1.4rem] rounded-bl-md bg-surface px-4 py-3 text-[15px] leading-snug shadow-soft ring-1 ring-border">
                Tell me about the launch. I&apos;ll pass it to the team.
              </p>
            </div>
          </div>
          {/* CSS rises, not JS reveals: the heading and intro paint before the page hydrates. */}
          <h1 className="animate-rise text-h1 text-balance">Book a campaign</h1>
          <p className="mt-5 max-w-[36rem] animate-rise text-lead text-pretty text-muted-foreground [animation-delay:80ms]">
            {DESCRIPTION}
          </p>
        </header>

        <div className="mt-10 grid items-start gap-6 sm:mt-14 lg:grid-cols-[minmax(0,1fr)_20rem] lg:gap-10 xl:grid-cols-[minmax(0,1fr)_23rem] xl:gap-14">
          <div className="edge-highlight relative animate-rise rounded-[var(--radius-xl)] border bg-surface p-5 shadow-soft [animation-delay:120ms] sm:p-8">
            <BookForm source="book_page" variant="page" />
          </div>

          <aside aria-labelledby="book-next-heading" className="animate-rise [animation-delay:220ms] lg:sticky lg:top-28">
            <div className="look-agent">
              <div className="mb-3 flex items-end gap-3">
                <Image
                  src="/art/echo-avatar.webp"
                  alt=""
                  width={40}
                  height={40}
                  className="size-10 shrink-0 rounded-full bg-[#d92e24] ring-2 ring-surface"
                />
                <p className="rounded-[1.4rem] rounded-bl-md bg-surface px-4 py-3 text-[15px] leading-snug shadow-soft ring-1 ring-border">
                  Here&apos;s what happens after you send it.
                </p>
              </div>
            </div>

            <div
              className={cn(
                "overflow-hidden rounded-[var(--radius-xl)]",
                "renaissance:bg-block-1 renaissance:text-block-ink",
                "agent:pl-[3.25rem]",
                "drop:bg-block-4 drop:text-white",
              )}
            >
              <div className="look-renaissance">
                <div className="relative aspect-[16/9]">
                  <Image
                    src="/art/detail-river.webp"
                    alt="A river bend in sunlight, a detail from Thomas Cole's The Oxbow"
                    fill
                    sizes="(min-width: 1280px) 23rem, (min-width: 1024px) 20rem, 100vw"
                    className="object-cover"
                  />
                </div>
              </div>

              <div className="renaissance:p-6 drop:p-6 drop:sm:p-8">
                <h2
                  id="book-next-heading"
                  className={cn(
                    "text-[1.375rem] leading-tight font-semibold tracking-[-0.03em]",
                    "renaissance:font-bold",
                    "agent:sr-only",
                    "drop:font-[family-name:var(--font-anton)] drop:text-[2.5rem] drop:leading-[0.95] drop:font-normal drop:tracking-[0.005em] drop:uppercase",
                  )}
                >
                  What happens next
                </h2>
                <ol className="mt-5 grid gap-5 agent:mt-0 agent:gap-3">
                  {NEXT_STEPS.map((step, index) => (
                    <li
                      key={step.title}
                      className={cn(
                        "flex items-start gap-4",
                        "renaissance:border-t renaissance:border-block-ink/20 renaissance:pt-4",
                        "agent:w-fit agent:max-w-full agent:rounded-[1.4rem] agent:bg-surface agent:px-5 agent:py-4 agent:shadow-soft agent:ring-1 agent:ring-border",
                        index === 0 && "agent:rounded-tl-md",
                      )}
                    >
                      <span
                        aria-hidden
                        className={cn(
                          "shrink-0 text-[15px] font-semibold tabular-nums",
                          "renaissance:w-6 renaissance:text-block-ink/70",
                          "agent:hidden",
                          "drop:-mt-1 drop:w-8 drop:font-[family-name:var(--font-anton)] drop:text-[2.25rem] drop:leading-none drop:font-normal drop:text-white/45",
                        )}
                      >
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <div className="min-w-0">
                        <p className="text-[15px] leading-snug font-semibold">{step.title}</p>
                        <p
                          className={cn(
                            "mt-1 text-sm leading-relaxed text-pretty",
                            "renaissance:text-block-ink/80 agent:text-muted-foreground drop:text-white/85",
                          )}
                        >
                          {step.body}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>

                {email ? (
                  <p
                    className={cn(
                      "mt-6 flex flex-wrap items-center gap-x-1.5 text-sm",
                      "renaissance:border-t renaissance:border-block-ink/20 renaissance:pt-4",
                      "agent:mt-4 agent:w-fit agent:rounded-[1.4rem] agent:bg-surface agent:px-5 agent:py-4 agent:shadow-soft agent:ring-1 agent:ring-border",
                      "drop:border-t drop:border-white/25 drop:pt-5",
                    )}
                  >
                    <span className="renaissance:text-block-ink/80 agent:text-muted-foreground drop:text-white/85">Rather write?</span>
                    <a
                      href={`mailto:${email}`}
                      className="inline-flex min-h-11 items-center gap-1.5 font-semibold break-all underline underline-offset-4 hover:decoration-2"
                    >
                      <Mail className="size-4 shrink-0" aria-hidden />
                      {email}
                    </a>
                  </p>
                ) : null}

                <p className="look-renaissance">
                  <span className="mt-6 block text-[11px] leading-snug text-block-ink/70">
                    Thomas Cole, The Oxbow (detail), 1836. The Met, public domain.
                  </span>
                </p>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </MarketingMain>
  );
}

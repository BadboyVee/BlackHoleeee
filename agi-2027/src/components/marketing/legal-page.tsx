import { EmailUs } from "@/components/layout/email-us";
import { MarketingMain } from "@/components/layout/marketing-main";
import { siteConfig } from "@/lib/site";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";

export type LegalSection = { id: string; title: string; body: React.ReactNode };

/** A paragraph of a legal page. */
function LegalText({ children }: { children: React.ReactNode }) {
  return <p className="mt-4 text-[16px] leading-relaxed text-pretty first:mt-0">{children}</p>;
}

/** A bulleted list of a legal page. */
function LegalList({ items, markerClassName }: { items: React.ReactNode[]; markerClassName?: string }) {
  return (
    <ul className="mt-4 grid gap-3 first:mt-0">
      {items.map((item, index) => (
        <li key={index} className="flex gap-3 text-[16px] leading-relaxed text-pretty">
          <span aria-hidden className={cn("mt-[0.7em] size-1.5 shrink-0 rounded-full bg-brand", markerClassName)} />
          <span className="min-w-0">{item}</span>
        </li>
      ))}
    </ul>
  );
}

/** The agency's contact address as a link, for use inside legal text. */
function ContactLink() {
  const email = siteConfig.contactEmail.trim();
  if (!email) return <>the email address on our home page</>;
  return (
    <a href={`mailto:${email}`} className="font-medium break-words underline underline-offset-4 hover:text-brand-text">
      {email}
    </a>
  );
}

/**
 * Privacy and Terms: the short version first, then numbered sections with an
 * index beside them on wide screens. Renaissance sets the summary on its dark
 * green block, Agent on a plain card, Drop on a blue color block.
 */
function LegalPage({
  title,
  lead,
  updated,
  summary,
  sections,
  emailSubject,
}: {
  title: string;
  lead: string;
  /** YYYY-MM-DD, the day the text last changed. */
  updated: string;
  summary: React.ReactNode[];
  sections: LegalSection[];
  emailSubject: string;
}) {
  return (
    <MarketingMain>
      <div className="mx-auto max-w-6xl px-4 pt-12 pb-16 sm:px-6 sm:pt-20 sm:pb-24 lg:px-8">
        <header className="max-w-3xl">
          {/* CSS rises, not JS reveals: the heading and intro paint before the page hydrates. */}
          <p className="animate-rise text-label text-muted-foreground">
            Last updated <time dateTime={updated}>{formatUtcDate(updated)}</time>
          </p>
          <h1 className="mt-4 animate-rise text-h1 text-balance">{title}</h1>
          <p className="mt-5 max-w-[36rem] animate-rise text-lead text-pretty text-muted-foreground [animation-delay:80ms]">
            {lead}
          </p>
        </header>

        <div className="mt-10 grid items-start gap-10 sm:mt-14 lg:grid-cols-[13rem_minmax(0,42rem)] lg:gap-16 xl:gap-24">
          <nav aria-label={`${title} sections`} className="hidden animate-rise [animation-delay:160ms] lg:sticky lg:top-28 lg:block">
            <p className="text-label text-muted-foreground">On this page</p>
            <ol className="mt-4 grid gap-0.5 border-l border-border">
              {sections.map((section, index) => (
                <li key={section.id}>
                  <a
                    href={`#${section.id}`}
                    className="-ml-px flex gap-2.5 border-l border-transparent py-1.5 pl-4 text-sm text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                  >
                    <span className="font-mono text-xs leading-5 text-subtle-foreground tabular-nums">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    {section.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          <div className="min-w-0">
            <section
              aria-labelledby="legal-summary"
              className={cn(
                "animate-rise rounded-[var(--radius-xl)] p-6 [animation-delay:120ms] sm:p-8",
                "renaissance:bg-block-1 renaissance:text-block-ink",
                "agent:bg-surface agent:shadow-soft agent:ring-1 agent:ring-border",
                "drop:bg-block-5 drop:text-white",
              )}
            >
              <h2
                id="legal-summary"
                className={cn(
                  "text-[1.375rem] leading-tight font-semibold tracking-[-0.03em]",
                  "renaissance:font-bold",
                  "drop:font-[family-name:var(--font-anton)] drop:text-[2rem] drop:leading-[0.95] drop:font-normal drop:tracking-[0.005em] drop:uppercase",
                )}
              >
                The short version
              </h2>
              <LegalList items={summary} markerClassName="renaissance:bg-current drop:bg-current" />
            </section>

            {sections.map((section, index) => (
              <section
                key={section.id}
                id={section.id}
                aria-labelledby={`${section.id}-title`}
                className="mt-12 scroll-mt-28 border-t border-border pt-8"
              >
                <h2
                  id={`${section.id}-title`}
                  className={cn(
                    "flex items-baseline gap-3 text-[1.375rem] leading-tight font-semibold tracking-[-0.03em] text-balance",
                    "renaissance:font-bold",
                    "drop:font-[family-name:var(--font-anton)] drop:text-[1.75rem] drop:leading-none drop:font-normal drop:tracking-[0.005em] drop:uppercase",
                  )}
                >
                  <span className="font-mono text-xs font-medium tracking-normal text-brand-text normal-case tabular-nums">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {section.title}
                </h2>
                <div className="mt-4">{section.body}</div>
              </section>
            ))}

            <div className="mt-14 flex flex-col items-start gap-4 rounded-[var(--radius-xl)] bg-surface-2 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
              <p className="text-[16px] leading-relaxed text-pretty">Questions about any of this? Write to us.</p>
              <EmailUs label="Email us" subject={emailSubject} />
            </div>
          </div>
        </div>
      </div>
    </MarketingMain>
  );
}

export { ContactLink, LegalList, LegalPage, LegalText };

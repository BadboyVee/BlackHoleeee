import { useId } from "react";
import { ArrowUpRight, Clock, MapPin, Ticket, UserPlus } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LocalDateTime } from "@/components/ui/local-time";
import { initialsFor } from "@/lib/auth/account-display";
import { countryName } from "@/lib/creators/countries";
import { formatCount, otherSocials, shortLink, xProfileUrl } from "@/lib/creators/display";
import { nicheLabel } from "@/lib/creators/options";
import type { ApplicationRow } from "@/lib/creators/queries";
import { cn } from "@/lib/utils";

import { PlatformIcon } from "../platform-icon";
import { ReviewPanel } from "./review-panel";

/*
 * One application: who they are, what they answered, and the review form or
 * its outcome. Everything people typed wraps, so nothing runs off a phone.
 */

/** Only web links become links. The forms already insist on https, this is a second lock. */
function isWebLink(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

const linkRow =
  "-mx-2 flex min-h-11 min-w-0 items-center gap-2.5 rounded-md px-2 text-sm text-foreground outline-none transition-colors hover:bg-surface-2 focus-visible:ring-4 focus-visible:ring-ring/20";

function OutLink({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
  if (!isWebLink(href)) {
    return <span className={cn("text-sm wrap-anywhere text-muted-foreground", className)}>{shortLink(href)}</span>;
  }
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={cn(linkRow, className)}>
      {children}
      <ArrowUpRight className="ml-auto size-4 shrink-0 text-subtle-foreground" aria-hidden />
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="min-w-0">
      <h3 className="text-label text-subtle-foreground">{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="min-w-0 rounded-md border bg-surface-2/40 px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={value === null ? "mt-0.5 text-sm text-subtle-foreground" : "mt-0.5 text-figure text-xl"}>
        {formatCount(value)}
      </dd>
    </div>
  );
}

function Chip({ icon: Icon, children }: { icon: React.ComponentType<{ className?: string }>; children: React.ReactNode }) {
  return (
    <span className="inline-flex max-w-full items-start gap-1.5 rounded-full border bg-surface-2/60 px-2.5 py-0.5 text-xs leading-5 font-medium text-muted-foreground">
      <Icon className="mt-[3px] size-3.5 shrink-0" aria-hidden />
      <span className="min-w-0 break-words">{children}</span>
    </span>
  );
}

function Answers({ row }: { row: ApplicationRow }) {
  if (row.invited) {
    return (
      <p className="px-4 py-4 text-sm text-pretty text-muted-foreground sm:px-5">
        Joined through an invite link, so there are no answers to review.
      </p>
    );
  }

  const { applicant } = row;
  const socials = otherSocials(applicant);
  const posts = row.bestPosts ?? [];
  const why = row.why?.trim();

  return (
    <div className="grid grid-cols-1 gap-5 px-4 py-4 sm:px-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-8">
      <div className="grid min-w-0 grid-cols-1 content-start gap-5">
        <dl className="grid grid-cols-2 gap-2.5">
          <Stat label="Followers on X" value={applicant.followers} />
          <Stat label="Average views" value={applicant.avgViews} />
        </dl>

        <Section title="Posts about">
          {applicant.niches.length > 0 ? (
            <ul className="flex flex-wrap gap-1.5">
              {applicant.niches.map((niche) => (
                <li
                  key={niche}
                  className="inline-flex h-7 items-center rounded-full border border-border-strong px-2.5 text-[13px] text-foreground"
                >
                  {nicheLabel(niche)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-subtle-foreground">Not given</p>
          )}
        </Section>

        <Section title="Other socials">
          {socials.length > 0 ? (
            <ul className="grid grid-cols-1">
              {socials.map((social) => (
                <li key={social.platform} className="min-w-0">
                  <OutLink href={social.url}>
                    <PlatformIcon platform={social.platform} className="text-muted-foreground" />
                    <span className="sr-only">{social.label}: </span>
                    <span className="min-w-0 wrap-anywhere">{shortLink(social.url)}</span>
                  </OutLink>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-subtle-foreground">None given</p>
          )}
        </Section>
      </div>

      <div className="grid min-w-0 grid-cols-1 content-start gap-5">
        <Section title="Why they want to join">
          {why ? (
            <blockquote className="border-l-2 border-border-strong pl-3.5 text-[15px] leading-relaxed break-words whitespace-pre-line text-pretty text-foreground">
              {why}
            </blockquote>
          ) : (
            <p className="text-sm text-subtle-foreground">Not given</p>
          )}
        </Section>

        <Section title="Best posts">
          {posts.length > 0 ? (
            <ol className="grid grid-cols-1">
              {posts.map((post, index) => (
                <li key={`${index}-${post}`} className="min-w-0">
                  <OutLink href={post}>
                    <span
                      aria-hidden
                      className="flex size-5 shrink-0 items-center justify-center rounded-full bg-surface-3 font-mono text-[11px] text-muted-foreground"
                    >
                      {index + 1}
                    </span>
                    <span className="min-w-0 wrap-anywhere">{shortLink(post)}</span>
                  </OutLink>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-subtle-foreground">Not given</p>
          )}
        </Section>
      </div>
    </div>
  );
}

export function ApplicationCard({
  row,
  preview,
  onReviewStart,
}: {
  row: ApplicationRow;
  preview: boolean;
  onReviewStart: (id: string) => void;
}) {
  const headingId = useId();
  const { applicant, referrer } = row;
  const country = countryName(applicant.country);

  return (
    <article
      aria-labelledby={headingId}
      className="min-w-0 overflow-hidden rounded-lg border bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)]"
    >
      <header className="flex items-start gap-3 px-4 pt-4 sm:px-5 sm:pt-5">
        <Avatar className="size-10">
          {applicant.avatarUrl ? <AvatarImage src={applicant.avatarUrl} alt="" /> : null}
          <AvatarFallback className="text-[11px]">{initialsFor(applicant.displayName)}</AvatarFallback>
        </Avatar>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1.5">
            <h2 id={headingId} className="min-w-0 pt-0.5 text-[15px] leading-snug font-semibold tracking-[-0.01em] break-words">
              {applicant.displayName}
            </h2>
            <StatusBadge kind="application" status={row.status} />
          </div>

          <ul className="mt-1 flex flex-wrap items-center gap-x-3.5 gap-y-1 text-[13px] text-muted-foreground">
            {applicant.xHandle ? (
              <li className="min-w-0">
                <a
                  href={xProfileUrl(applicant.xHandle)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex max-w-full items-center gap-1.5 rounded-sm font-medium text-foreground underline-offset-4 outline-none hover:underline focus-visible:ring-4 focus-visible:ring-ring/20"
                >
                  <PlatformIcon platform="x" className="size-3" />
                  <span className="min-w-0 wrap-anywhere">@{applicant.xHandle}</span>
                  <span className="sr-only"> on X (opens in a new tab)</span>
                </a>
              </li>
            ) : null}
            {country ? (
              <li className="inline-flex min-w-0 items-center gap-1.5">
                <MapPin className="size-3.5 shrink-0" aria-hidden />
                <span className="sr-only">Lives in </span>
                {country}
              </li>
            ) : null}
            <li className="inline-flex min-w-0 items-center gap-1.5">
              <Clock className="size-3.5 shrink-0" aria-hidden />
              <span>
                {row.invited ? "Joined" : "Applied"} <LocalDateTime value={row.createdAt} />
              </span>
            </li>
          </ul>

          {referrer || row.invited ? (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {referrer ? (
                <Chip icon={UserPlus}>
                  Referred by {referrer.displayName}
                  {referrer.xHandle ? ` (@${referrer.xHandle})` : null}
                </Chip>
              ) : null}
              {row.invited ? <Chip icon={Ticket}>Joined by invite</Chip> : null}
            </div>
          ) : null}
        </div>
      </header>

      <Answers row={row} />
      <ReviewPanel row={row} preview={preview} onReviewStart={onReviewStart} />
    </article>
  );
}

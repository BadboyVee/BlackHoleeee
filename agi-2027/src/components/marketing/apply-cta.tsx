"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { parseReferralCode } from "@/lib/creators/display";
import { cn } from "@/lib/utils";

/*
 * The /apply page's calls to action. Both go through sign up or sign in and
 * land on the application form. A creator's referral link (/apply?ref=CODE)
 * rides along in ?next=, which survives sign up and the confirmation email,
 * and the application page fills the code in from there.
 */

type Surface = "hero" | "block";

function applicationPath(referral: string | null): string {
  return referral ? `/application?ref=${referral}` : "/application";
}

/**
 * The links themselves, with no hooks, so the page can prerender them as the
 * fallback while the address is read.
 *
 * - hero: on the page background (on Drop, on the hero's color block).
 * - block: on the closing color block (bg-block-1, bg-block-5 on Drop).
 */
function ApplyCtaLinks({
  referral = null,
  surface = "hero",
  className,
}: {
  referral?: string | null;
  surface?: Surface;
  className?: string;
}) {
  const next = encodeURIComponent(applicationPath(referral));
  const applyHref = `/signup?next=${next}`;
  const signInHref = `/login?next=${next}`;

  if (surface === "block") {
    return (
      <div className={cn("flex flex-col items-stretch gap-2 sm:items-start", className)}>
        <Button
          asChild
          variant="brand"
          size="xl"
          className="group w-full sm:w-auto agent:bg-block-ink agent:text-block-1 agent:hover:bg-block-ink/90 drop:bg-block-ink drop:text-block-5 drop:hover:bg-block-ink/90"
        >
          <Link href={applyHref}>
            Apply now
            <ArrowRight className="transition-transform duration-200 ease-snap group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </Button>
        <Link
          href={signInHref}
          className="inline-flex min-h-11 items-center justify-center text-[15px] font-medium text-block-ink/85 underline decoration-block-ink/40 underline-offset-4 transition-colors hover:text-block-ink hover:decoration-block-ink sm:justify-start"
        >
          Already applied? Sign in
        </Link>
        {referral ? <ReferralNote code={referral} className="text-block-ink/80" /> : null}
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Button
          asChild
          variant="brand"
          size="xl"
          className="group w-full sm:w-auto drop:bg-block-ink drop:text-block-1 drop:hover:bg-block-ink/90"
        >
          <Link href={applyHref}>
            Apply now
            <ArrowRight className="transition-transform duration-200 ease-snap group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </Button>
        <Button
          asChild
          variant="secondary"
          size="xl"
          className="w-full sm:w-auto drop:border-block-ink/60 drop:bg-transparent drop:text-block-ink drop:shadow-none drop:hover:bg-block-ink/10"
        >
          <Link href={signInHref}>Already applied? Sign in</Link>
        </Button>
      </div>
      {referral ? <ReferralNote code={referral} className="mt-3 text-muted-foreground drop:text-block-ink/85" /> : null}
    </div>
  );
}

function ReferralNote({ code, className }: { code: string; className?: string }) {
  return (
    <p className={cn("text-center text-[13px] leading-snug sm:text-left", className)}>
      Referral code <span className="font-mono font-medium">{code}</span> is filled in for you.
    </p>
  );
}

function ApplyCtaWithReferral(props: { surface?: Surface; className?: string }) {
  const referral = parseReferralCode(useSearchParams().get("ref"));
  return <ApplyCtaLinks {...props} referral={referral} />;
}

/**
 * The calls to action, carrying ?ref= when the visitor came from a referral
 * link. Reading the address needs a Suspense boundary for the page to stay
 * prerendered; until it's read, the same links show without a code.
 */
export function ApplyCta(props: { surface?: Surface; className?: string }) {
  return (
    <Suspense fallback={<ApplyCtaLinks {...props} />}>
      <ApplyCtaWithReferral {...props} />
    </Suspense>
  );
}

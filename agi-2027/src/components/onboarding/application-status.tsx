import Link from "next/link";
import { ArrowRight, Check, Clock, Mail, PartyPopper, Ticket } from "lucide-react";

import { AuthHeading } from "@/components/auth/parts";
import { EmailUs } from "@/components/layout/email-us";
import { Button } from "@/components/ui/button";
import type { ApplicationStatus } from "@/lib/creators/queries";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";

/*
 * What an applicant sees once they've applied. The page reads the status on
 * every visit, so it's up to date when they come back from our email.
 */

export function ApplicationStatusView({
  status,
  createdAt,
  firstName,
  email,
}: {
  status: ApplicationStatus;
  createdAt: string;
  firstName: string;
  email: string;
}) {
  if (status === "approved") {
    return (
      <div className="grid gap-6">
        <StatusIcon tone="green">
          <PartyPopper className="size-6" />
        </StatusIcon>
        <AuthHeading
          eyebrow="Your application"
          title="You're in"
          lead={`Welcome to AGI 2027, ${firstName}. Your creator dashboard is ready.`}
        />
        <Button asChild size="xl" variant="brand" className="w-full">
          <Link href="/dashboard">
            Open your dashboard
            <ArrowRight aria-hidden />
          </Link>
        </Button>
      </div>
    );
  }

  if (status === "rejected") {
    return (
      <div className="grid gap-6">
        <AuthHeading
          eyebrow="Your application"
          title="Not this time"
          lead={`Thanks for applying, ${firstName}. We can't take you on right now.`}
        />
        <p className="text-center text-[15px] leading-relaxed text-pretty text-muted-foreground">
          Audiences change. If yours grows, or moves toward AI and tech launches, email us and we&apos;ll take another look.
        </p>
        <div className="flex justify-center">
          <EmailUs label="Email us" subject="My creator application" />
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-7">
      <StatusIcon tone="green">
        <Check className="size-6" strokeWidth={2.5} />
      </StatusIcon>
      <AuthHeading
        eyebrow="Your application"
        title="Application received"
        lead={
          <>
            Thanks, {firstName}. We review every application by hand, usually within a few days, and email{" "}
            <span className="font-medium break-words text-foreground">{email}</span> with the answer.
          </>
        }
      />

      <ol aria-label="Where your application is" className="grid gap-0 rounded-2xl border bg-surface px-4 py-2 sm:px-5">
        <Step state="done" title="Received" detail={formatUtcDate(createdAt)} icon={<Check className="size-3.5" strokeWidth={3} />} />
        <Step state="current" title="In review" detail="Our team is reading it" icon={<Clock className="size-3.5" />} />
        <Step state="next" title="Our answer" detail="By email, and on this page" icon={<Mail className="size-3.5" />} last />
      </ol>

      <div className="flex items-start gap-3.5 rounded-2xl border border-dashed border-border-strong px-4 py-4 sm:px-5">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-muted-foreground" aria-hidden>
          <Ticket className="size-4" />
        </span>
        <div className="min-w-0 text-sm leading-relaxed">
          <p className="font-medium text-foreground">Got an invite link?</p>
          <p className="mt-0.5 text-pretty text-muted-foreground">Open it while you&apos;re signed in and you&apos;re in straight away.</p>
        </div>
      </div>
    </div>
  );
}

function StatusIcon({ tone, children }: { tone: "green"; children: React.ReactNode }) {
  return (
    <span
      data-tone={tone}
      aria-hidden
      className="mx-auto flex size-14 items-center justify-center rounded-full bg-(--tone-fg)/12 text-(--tone-fg)"
    >
      {children}
    </span>
  );
}

function Step({
  state,
  title,
  detail,
  icon,
  last = false,
}: {
  state: "done" | "current" | "next";
  title: string;
  detail: string;
  icon: React.ReactNode;
  last?: boolean;
}) {
  return (
    <li
      aria-current={state === "current" ? "step" : undefined}
      className={cn("flex items-center gap-3.5 py-3", !last && "border-b")}
    >
      <span
        data-tone={state === "done" ? "green" : state === "current" ? "amber" : undefined}
        aria-hidden
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded-full",
          state === "next" ? "border border-border-strong text-subtle-foreground" : "bg-(--tone-fg)/14 text-(--tone-fg)",
        )}
      >
        {icon}
      </span>
      <span className="min-w-0 flex-1">
        <span className={cn("block text-[15px] font-medium", state === "next" && "text-muted-foreground")}>{title}</span>
        <span className="block text-[13px] text-muted-foreground">{detail}</span>
      </span>
      {state === "current" ? (
        <span data-tone="amber" className="relative flex size-2 text-(--tone-fg)" aria-hidden>
          <span className="absolute inset-0 animate-pulse-ring rounded-full bg-current" />
          <span className="relative size-full rounded-full bg-current" />
        </span>
      ) : null}
      <span className="sr-only">{state === "done" ? "Done" : state === "current" ? "Now" : "Next"}</span>
    </li>
  );
}

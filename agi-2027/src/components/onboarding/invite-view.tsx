import Link from "next/link";
import { ArrowRight, Check, RotateCw, Ticket, TicketX } from "lucide-react";

import { AuthHeading, NoteBanner } from "@/components/auth/parts";
import { SignOutButton } from "@/components/auth/sign-out";
import { EmailUs } from "@/components/layout/email-us";
import { Button } from "@/components/ui/button";
import { accountUnavailableMessage } from "@/lib/auth/messages";
import { roleHome } from "@/lib/auth/routes";
import { inviteStateMessage, type InviteState } from "@/lib/creators/messages";
import { siteConfig } from "@/lib/site";
import { cn } from "@/lib/utils";

import { AcceptInvite } from "./accept-invite";

/*
 * What the invite page shows, one view per case. The page works out which
 * case it is; these only lay it out. Each takes an optional note (the preview
 * notice, for one) that sits under the heading.
 */

type Note = { note?: React.ReactNode };

/** Where the invite link sends people, so sign up and sign in come back to it. */
function invitePath(code: string): string {
  return `/invite/${code}`;
}

/** Signed out, with a link that works: create an account or sign in, then accept. */
export function InviteWelcome({ code, note }: { code: string } & Note) {
  const next = encodeURIComponent(invitePath(code));
  return (
    <Frame
      icon={<Ticket className="size-6" />}
      tone="brand"
      title="You're invited"
      lead="AGI 2027 pays creators to post on X about new AI and tech launches. This link skips the application."
      note={note}
    >
      <div className="grid gap-3">
        <Button asChild variant="brand" size="xl" className="w-full">
          <Link href={`/signup?next=${next}`}>
            Create your account
            <ArrowRight aria-hidden />
          </Link>
        </Button>
        <Button asChild variant="secondary" size="xl" className="w-full">
          <Link href={`/login?next=${next}`}>I already have an account</Link>
        </Button>
      </div>
      <NextSteps />
    </Frame>
  );
}

const NEXT_STEPS = [
  { title: "Create your account", detail: "Use the email you'd like us to reach you on." },
  { title: "Confirm your email", detail: "Open the link we send you. It brings you back here." },
  { title: "You're in", detail: "Accept the invite, then claim campaigns from your dashboard." },
];

function NextSteps() {
  return (
    <section aria-labelledby="invite-next-steps" className="rounded-2xl border bg-surface px-4 py-4 sm:px-5">
      <h2 id="invite-next-steps" className="text-label text-muted-foreground">
        What happens next
      </h2>
      <ol className="mt-3.5 grid gap-4">
        {NEXT_STEPS.map((step, index) => {
          const last = index === NEXT_STEPS.length - 1;
          return (
            <li key={step.title} className="flex items-start gap-3.5">
              <span
                aria-hidden
                data-tone={last ? "green" : undefined}
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full text-[13px] font-semibold tabular-nums",
                  last ? "bg-(--tone-fg)/14 text-(--tone-fg)" : "border border-border-strong text-muted-foreground",
                )}
              >
                {last ? <Check className="size-3.5" strokeWidth={3} /> : index + 1}
              </span>
              <span className="min-w-0 pt-0.5">
                <span className="block text-[15px] leading-snug font-medium">{step.title}</span>
                <span className="mt-0.5 block text-[13px] leading-snug text-pretty text-muted-foreground">{step.detail}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

/** Signed in as an applicant: one button and they're a creator. */
export function InviteAccept({ code, firstName, email, note }: { code: string; firstName: string; email: string } & Note) {
  return (
    <Frame
      icon={<Ticket className="size-6" />}
      tone="brand"
      title={`You're invited, ${firstName}`}
      lead={
        <>
          You&apos;re signed in as <Email address={email} />. Accept to skip the queue and open your creator dashboard.
        </>
      }
      note={note}
    >
      <AcceptInvite code={code} />
      <NotYou code={code} />
    </Frame>
  );
}

/** Signed in as a creator or staff: nothing to accept. */
export function InviteAlreadyIn({ role, email, note }: { role: "creator" | "admin" | "team"; email: string } & Note) {
  const staff = role !== "creator";
  return (
    <Frame
      icon={<Check className="size-6" strokeWidth={2.5} />}
      tone="green"
      title="You're already in"
      lead={
        staff ? (
          <>
            You&apos;re signed in as <Email address={email} />, a staff account.
          </>
        ) : (
          <>
            You&apos;re signed in as <Email address={email} />, and this account is already a creator.
          </>
        )
      }
      note={note}
    >
      <Button asChild variant="brand" size="xl" className="w-full">
        <Link href={roleHome(role)}>
          {staff ? "Open the admin" : "Open your dashboard"}
          <ArrowRight aria-hidden />
        </Link>
      </Button>
      {staff ? (
        <p className="text-center text-[13px] leading-relaxed text-pretty text-muted-foreground">
          Invite links are for new creators. To see what they see, open this link in a private window.
        </p>
      ) : null}
    </Frame>
  );
}

/** Signed in with an account that isn't active: the invite can't help, but we can. */
export function InviteAccountInactive({ code, email, note }: { code: string; email: string } & Note) {
  return (
    <Frame
      title="We can't open this invite"
      lead={
        <>
          You&apos;re signed in as <Email address={email} />.
        </>
      }
      note={note}
    >
      <NoteBanner note={{ tone: "error", text: accountUnavailableMessage(siteConfig.contactEmail) }} />
      <NotYou code={code} />
    </Frame>
  );
}

const UNUSABLE_TITLES: Record<Exclude<InviteState, "valid">, string> = {
  revoked: "This invite is switched off",
  expired: "This invite has expired",
  used_up: "This invite is used up",
  unknown: "We don't recognise this invite",
};

/** A link that can't be used. `applyHref` is the application form for applicants, the pitch for everyone else. */
export function InviteUnusable({
  state,
  applyHref = "/apply",
  note,
}: { state: Exclude<InviteState, "valid">; applyHref?: string } & Note) {
  const email = siteConfig.contactEmail.trim();
  return (
    <Frame
      icon={<TicketX className="size-6" />}
      tone="gray"
      title={UNUSABLE_TITLES[state]}
      lead={inviteStateMessage(state)}
      note={note}
    >
      <Button asChild variant="secondary" size="xl" className="w-full">
        <Link href={applyHref}>Apply instead</Link>
      </Button>
      {email ? (
        <div className="grid justify-items-center gap-2 text-center">
          <p className="text-[13px] text-muted-foreground">Think the link should work?</p>
          <EmailUs label="Email us" subject="My invite link" />
        </div>
      ) : null}
    </Frame>
  );
}

/** The check itself failed: say so plainly and offer a fresh load. */
export function InviteCheckFailed({ code, note }: { code: string } & Note) {
  return (
    <Frame
      title="Hold on a moment"
      lead="We couldn't check this invite just now. Refresh the page to try again."
      note={note}
    >
      <Button asChild variant="secondary" size="xl" className="w-full">
        {/* A full load, so the check runs again from scratch. */}
        <a href={invitePath(code)}>
          <RotateCw aria-hidden />
          Refresh the page
        </a>
      </Button>
    </Frame>
  );
}

function Frame({
  icon,
  tone,
  title,
  lead,
  note,
  children,
}: {
  icon?: React.ReactNode;
  tone?: "brand" | "green" | "gray";
  title: string;
  lead: React.ReactNode;
  note?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-7">
      <div className="grid gap-5">
        {icon ? (
          <span
            data-tone={tone}
            aria-hidden
            className="mx-auto flex size-14 items-center justify-center rounded-full bg-(--tone-fg)/12 text-(--tone-fg)"
          >
            {icon}
          </span>
        ) : null}
        <AuthHeading eyebrow="Invite" title={title} lead={lead} />
      </div>
      {note}
      {children}
    </div>
  );
}

function Email({ address }: { address: string }) {
  return <span className="font-medium break-words text-foreground">{address}</span>;
}

/** Log out, and come back to this invite after signing in as someone else. */
function NotYou({ code }: { code: string }) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-x-1 text-sm text-muted-foreground">
      <span>Not you?</span>
      <SignOutButton next={invitePath(code)} />
    </div>
  );
}

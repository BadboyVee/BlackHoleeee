"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { useFormStatus } from "react-dom";
import type { FieldValues, Path, UseFormReturn } from "react-hook-form";
import { CircleAlert, CircleCheck, Eye, EyeOff, Info, MailCheck } from "lucide-react";

import { resendConfirmation, signInWithGoogle } from "@/app/(auth)/actions";
import { GoogleLogo } from "@/components/brand/social-icons";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { PageNote } from "@/lib/auth/messages";
import type { AuthFormState } from "@/lib/auth/schemas";
import type { CreatorFormState } from "@/lib/creators/schemas";
import { siteConfig } from "@/lib/site";
import { cn } from "@/lib/utils";

/*
 * Pieces every sign-in page shares. The forms themselves live beside this file.
 */

export const IDLE: AuthFormState = { status: "idle" };

/** Keeps a field's label in view (under the sticky header) when it gets focus. */
export const SCROLL_MARGIN = "scroll-mt-24";

export function AuthHeading({ eyebrow, title, lead }: { eyebrow: string; title: string; lead: React.ReactNode }) {
  return (
    <div className="text-center">
      <p className="text-label text-brand-text">{eyebrow}</p>
      <h1 className="mt-3 text-h2 text-balance">{title}</h1>
      <p className="mx-auto mt-2.5 max-w-sm text-pretty text-muted-foreground">{lead}</p>
    </div>
  );
}

const NOTE_TONES = { info: "gray", success: "green", error: "red" } as const;
const NOTE_ICONS = { info: Info, success: CircleCheck, error: CircleAlert } as const;

/** A note above the form, such as "You're signed out" after a redirect. */
export function NoteBanner({ note, className }: { note: PageNote; className?: string }) {
  const Icon = NOTE_ICONS[note.tone];
  return (
    <div
      data-tone={NOTE_TONES[note.tone]}
      role={note.tone === "error" ? "alert" : "status"}
      className={cn(
        "flex items-start gap-3 rounded-xl border border-(--tone-fg)/30 bg-(--tone-fg)/8 px-4 py-3.5 text-sm leading-relaxed text-foreground",
        className,
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0 text-(--tone-fg)" aria-hidden />
      <p className="min-w-0 text-pretty">
        <WithEmailLink text={note.text} />
      </p>
    </div>
  );
}

/** The contact address as a link when the text mentions it. */
export function WithEmailLink({ text }: { text: string }) {
  const email = siteConfig.contactEmail.trim();
  const at = email ? text.indexOf(email) : -1;
  if (at < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, at)}
      <a href={`mailto:${email}`} className="font-medium break-words underline underline-offset-4 hover:decoration-2">
        {email}
      </a>
      {text.slice(at + email.length)}
    </>
  );
}

/**
 * Puts the server's field errors on the fields and moves focus to the first
 * problem, or to the alert when the problem isn't a single field.
 */
export function useServerErrors<T extends FieldValues>(
  state: AuthFormState | CreatorFormState,
  form: UseFormReturn<T, unknown, unknown>,
  fields: readonly Path<T>[],
  alertRef: React.RefObject<HTMLDivElement | null>,
) {
  const handled = useRef(state);
  useEffect(() => {
    if (state === handled.current) return;
    handled.current = state;
    if (state.status !== "error") return;
    let first: Path<T> | undefined;
    for (const name of fields) {
      const message = state.fieldErrors?.[name];
      if (!message) continue;
      form.setError(name, { type: "server", message });
      first ??= name;
    }
    if (first) form.setFocus(first);
    else alertRef.current?.focus();
  }, [state, form, fields, alertRef]);
}

/** The server's message for the whole form, read out and focusable. Shared by the creator forms too. */
export function ServerAlert({
  message,
  children,
  ref,
}: {
  message: string;
  children?: React.ReactNode;
  ref?: React.Ref<HTMLDivElement>;
}) {
  return (
    <div
      ref={ref}
      role="alert"
      tabIndex={-1}
      data-tone="red"
      className={cn(
        "rounded-xl border border-(--tone-fg)/30 bg-(--tone-fg)/8 px-4 py-3.5 text-sm leading-relaxed text-foreground outline-none",
        "focus-visible:ring-4 focus-visible:ring-(--tone-fg)/20",
        SCROLL_MARGIN,
      )}
    >
      <div className="flex items-start gap-3">
        <CircleAlert className="mt-0.5 size-4 shrink-0 text-(--tone-fg)" aria-hidden />
        <p className="min-w-0 text-pretty">
          <WithEmailLink text={message} />
        </p>
      </div>
      {children}
    </div>
  );
}

/** A password field with a show/hide button. */
export function PasswordInput({ className, ref, ...props }: React.ComponentProps<typeof Input>) {
  const [shown, setShown] = useState(false);
  return (
    <div className="relative">
      <Input
        ref={ref}
        type={shown ? "text" : "password"}
        autoCapitalize="none"
        spellCheck={false}
        className={cn(SCROLL_MARGIN, "pr-12", className)}
        {...props}
      />
      <button
        type="button"
        onClick={() => setShown((value) => !value)}
        aria-label={shown ? "Hide password" : "Show password"}
        aria-pressed={shown}
        className="absolute inset-y-0 right-0 flex w-11 cursor-pointer items-center justify-center rounded-r-xl text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/20"
      >
        {shown ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
      </button>
    </div>
  );
}

function GoogleSubmit({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" variant="secondary" size="xl" loading={pending} className="w-full">
      {pending ? null : <GoogleLogo className="size-[18px]" />}
      {label}
    </Button>
  );
}

/** Continue with Google: a plain form, so it works before the page's JavaScript loads. */
export function GoogleButton({ next, label = "Continue with Google" }: { next: string | null; label?: string }) {
  return (
    <form action={signInWithGoogle}>
      <input type="hidden" name="next" value={next ?? ""} />
      <GoogleSubmit label={label} />
    </form>
  );
}

export function OrDivider() {
  return (
    <div className="flex items-center gap-3 text-xs text-subtle-foreground" aria-hidden>
      <span className="h-px flex-1 bg-border" />
      or with email
      <span className="h-px flex-1 bg-border" />
    </div>
  );
}

/** "Send it again" for the sign-up confirmation email, with its own small answer. */
export function ResendConfirmation({ email, next, className }: { email: string; next: string | null; className?: string }) {
  const [state, dispatch, pending] = useActionState(resendConfirmation, IDLE);
  return (
    <form action={dispatch} className={cn("flex flex-wrap items-center gap-x-3 gap-y-1", className)}>
      <input type="hidden" name="email" value={email} />
      <input type="hidden" name="next" value={next ?? ""} />
      <Button type="submit" variant="link" size="sm" loading={pending} className="text-[13px] font-semibold">
        Send the link again
      </Button>
      <span aria-live="polite" className="text-[13px] text-muted-foreground">
        {state.status === "sent" ? "Sent. Check your inbox." : state.status === "error" ? state.message : null}
      </span>
    </form>
  );
}

/** What a form shows once its email is on the way. */
export function CheckInbox({
  email,
  title,
  body,
  footer,
}: {
  email: string;
  title: string;
  body: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);
  return (
    <div className="text-center">
      <span
        data-tone="green"
        className="mx-auto flex size-14 items-center justify-center rounded-full bg-(--tone-fg)/12 text-(--tone-fg)"
        aria-hidden
      >
        <MailCheck className="size-6" />
      </span>
      <h1 ref={headingRef} tabIndex={-1} className="mt-5 text-h2 text-balance outline-none">
        {title}
      </h1>
      <p className="mx-auto mt-2.5 max-w-sm text-pretty text-muted-foreground">
        {body} <span className="font-medium break-words text-foreground">{email}</span>.
      </p>
      {footer ? <div className="mt-6 grid justify-items-center gap-2">{footer}</div> : null}
    </div>
  );
}

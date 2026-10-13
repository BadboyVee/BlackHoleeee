"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

import { requestPasswordReset, updatePassword } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { PageNote } from "@/lib/auth/messages";
import {
  emailSchema,
  newPasswordSchema,
  PASSWORD_MIN,
  type AuthFormState,
  type EmailValues,
  type NewPasswordValues,
} from "@/lib/auth/schemas";

import { AuthHeading, CheckInbox, IDLE, NoteBanner, PasswordInput, SCROLL_MARGIN, ServerAlert, useServerErrors } from "./parts";

const EMAIL_FIELDS = ["email"] as const;
const PASSWORD_FIELDS = ["password", "confirm"] as const;

/** Ask for a reset link. The answer never says whether the address has an account. */
export function ForgotPasswordForm({ note }: { note: PageNote | null }) {
  const uid = useId();
  const [state, dispatch, pending] = useActionState(requestPasswordReset, IDLE);
  const [dismissed, setDismissed] = useState<AuthFormState | null>(null);
  const form = useForm<EmailValues, unknown, z.output<typeof emailSchema>>({
    resolver: zodResolver(emailSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: { email: "" },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, EMAIL_FIELDS, alertRef);

  if (state.status === "sent") {
    return (
      <CheckInbox
        email={state.email}
        title="Check your inbox"
        body="If there's an account for that address, a link to set a new password is on its way to"
        footer={
          <Link href="/login" className="inline-flex min-h-11 items-center text-sm font-semibold underline-offset-4 hover:underline">
            Back to sign in
          </Link>
        }
      />
    );
  }

  const failure = state.status === "error" && dismissed !== state ? state : null;

  return (
    <div className="grid gap-6">
      <AuthHeading eyebrow="Locked out?" title="Reset your password" lead="Enter your email and we'll send you a link to set a new one." />
      {note && !failure ? <NoteBanner note={note} /> : null}
      {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      <form
        action={dispatch}
        onSubmit={(event) => {
          const element = event.currentTarget;
          setDismissed(state);
          void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
        }}
        noValidate
        aria-label="Reset your password"
        className="grid gap-5"
      >
        <Field id={`${uid}-email`} label="Email" error={errors.email?.message}>
          <Input
            id={`${uid}-email`}
            type="email"
            inputMode="email"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            required
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={fieldDescribedBy(`${uid}-email`, { error: errors.email })}
            className={SCROLL_MARGIN}
            {...form.register("email")}
          />
        </Field>
        <Button type="submit" size="xl" variant="brand" loading={pending} className="w-full">
          {pending ? "Sending" : "Send the link"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Remembered it?{" "}
        <Link href="/login" className="font-semibold text-foreground underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

const NEW_PASSWORD_HINT = `At least ${PASSWORD_MIN} characters.`;

/** Set a new password. The reset link signed them in for exactly this; the proxy sends anyone else away. */
export function ResetPasswordForm() {
  const uid = useId();
  const [state, dispatch, pending] = useActionState(updatePassword, IDLE);
  const [dismissed, setDismissed] = useState<AuthFormState | null>(null);
  const form = useForm<NewPasswordValues, unknown, z.output<typeof newPasswordSchema>>({
    resolver: zodResolver(newPasswordSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: { password: "", confirm: "" },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, PASSWORD_FIELDS, alertRef);

  const failure = state.status === "error" && dismissed !== state ? state : null;

  return (
    <div className="grid gap-6">
      <AuthHeading eyebrow="Almost there" title="Pick a new password" lead="You'll stay signed in on this device." />
      {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      <form
        action={dispatch}
        onSubmit={(event) => {
          const element = event.currentTarget;
          setDismissed(state);
          void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
        }}
        noValidate
        aria-label="Set a new password"
        className="grid gap-5"
      >
        <Field id={`${uid}-password`} label="New password" hint={NEW_PASSWORD_HINT} error={errors.password?.message}>
          <PasswordInput
            id={`${uid}-password`}
            autoComplete="new-password"
            required
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={fieldDescribedBy(`${uid}-password`, { hint: NEW_PASSWORD_HINT, error: errors.password })}
            {...form.register("password")}
          />
        </Field>
        <Field id={`${uid}-confirm`} label="Type it again" error={errors.confirm?.message}>
          <PasswordInput
            id={`${uid}-confirm`}
            autoComplete="new-password"
            required
            aria-invalid={errors.confirm ? true : undefined}
            aria-describedby={fieldDescribedBy(`${uid}-confirm`, { error: errors.confirm })}
            {...form.register("confirm")}
          />
        </Field>
        <Button type="submit" size="xl" variant="brand" loading={pending} className="w-full">
          {pending ? "Saving" : "Save new password"}
        </Button>
      </form>
    </div>
  );
}

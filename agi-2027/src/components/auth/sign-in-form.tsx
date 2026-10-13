"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

import { signIn } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { PageNote } from "@/lib/auth/messages";
import { signInSchema, type AuthFormState, type SignInValues } from "@/lib/auth/schemas";

import {
  AuthHeading,
  GoogleButton,
  IDLE,
  NoteBanner,
  OrDivider,
  PasswordInput,
  ResendConfirmation,
  SCROLL_MARGIN,
  ServerAlert,
  useServerErrors,
} from "./parts";

const FIELDS = ["email", "password"] as const;

/**
 * Sign in with Google or email. `next` is where to go afterwards (already
 * checked to be on this site) and `note` explains a redirect, such as
 * "You're signed out". The page reads both from the URL on the server.
 */
export function SignInForm({ googleEnabled, next, note }: { googleEnabled: boolean; next: string | null; note: PageNote | null }) {
  const uid = useId();
  const [state, dispatch, pending] = useActionState(signIn, IDLE);
  // The answer the visitor has moved past by sending again.
  const [dismissed, setDismissed] = useState<AuthFormState | null>(null);
  const form = useForm<SignInValues, unknown, z.output<typeof signInSchema>>({
    resolver: zodResolver(signInSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: { email: "", password: "" },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  const failure = state.status === "error" && dismissed !== state ? state : null;
  const signupHref = next ? `/signup?next=${encodeURIComponent(next)}` : "/signup";

  return (
    <div className="grid gap-6">
      <AuthHeading eyebrow="Welcome back" title="Sign in" lead="Pick up where you left off: campaigns, claims and earnings." />
      {note && !failure ? <NoteBanner note={note} /> : null}

      {googleEnabled ? (
        <>
          <GoogleButton next={next} />
          <OrDivider />
        </>
      ) : null}

      {failure && !failure.fieldErrors ? (
        <ServerAlert ref={alertRef} message={failure.message}>
          {failure.offer === "resend_confirmation" && failure.email ? (
            <ResendConfirmation email={failure.email} next={next} className="mt-2 pl-7" />
          ) : null}
        </ServerAlert>
      ) : null}

      <form
        action={dispatch}
        onSubmit={(event) => {
          // Check in the browser first. Only a clean form goes to the server, which checks again.
          const element = event.currentTarget;
          setDismissed(state);
          void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
        }}
        noValidate
        aria-label="Sign in with email"
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
        <div className="grid gap-2">
          <Field id={`${uid}-password`} label="Password" error={errors.password?.message}>
            <PasswordInput
              id={`${uid}-password`}
              autoComplete="current-password"
              required
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={fieldDescribedBy(`${uid}-password`, { error: errors.password })}
              {...form.register("password")}
            />
          </Field>
          <Link
            href="/forgot-password"
            className="-my-2.5 inline-flex min-h-11 items-center justify-self-end text-[13px] font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            Forgot your password?
          </Link>
        </div>
        <input type="hidden" name="next" value={next ?? ""} />
        <Button type="submit" size="xl" variant="brand" loading={pending} className="w-full">
          {pending ? "Signing in" : "Sign in"}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        New here?{" "}
        <Link href={signupHref} className="font-semibold text-foreground underline-offset-4 hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}

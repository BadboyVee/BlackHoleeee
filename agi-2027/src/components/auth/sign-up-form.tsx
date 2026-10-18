"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

import { signUp } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { PageNote } from "@/lib/auth/messages";
import { NAME_MAX, PASSWORD_MIN, signUpSchema, type AuthFormState, type SignUpValues } from "@/lib/auth/schemas";

import {
  AuthHeading,
  CheckInbox,
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

const FIELDS = ["name", "email", "password"] as const;
const PASSWORD_HINT = `At least ${PASSWORD_MIN} characters. A few words together works well.`;

/** Create an account with Google or email. New accounts start as applicants. */
export function SignUpForm({ googleEnabled, next, note }: { googleEnabled: boolean; next: string | null; note: PageNote | null }) {
  const [round, setRound] = useState(0);
  return (
    <SignUpBody key={round} googleEnabled={googleEnabled} next={next} note={note} onStartOver={() => setRound((value) => value + 1)} />
  );
}

function SignUpBody({
  googleEnabled,
  next,
  note,
  onStartOver,
}: {
  googleEnabled: boolean;
  next: string | null;
  note: PageNote | null;
  onStartOver: () => void;
}) {
  const uid = useId();
  const [state, dispatch, pending] = useActionState(signUp, IDLE);
  const [dismissed, setDismissed] = useState<AuthFormState | null>(null);
  const form = useForm<SignUpValues, unknown, z.output<typeof signUpSchema>>({
    resolver: zodResolver(signUpSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: { name: "", email: "", password: "" },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  if (state.status === "sent") {
    return (
      <CheckInbox
        email={state.email}
        title="Check your inbox"
        body="To finish, open the link we just sent to"
        footer={
          <>
            <p className="text-[13px] text-muted-foreground">Nothing yet? Check spam, or:</p>
            <ResendConfirmation email={state.email} next={next} className="justify-center" />
            <Button type="button" variant="ghost" size="sm" onClick={onStartOver}>
              Use a different email
            </Button>
          </>
        }
      />
    );
  }

  const failure = state.status === "error" && dismissed !== state ? state : null;
  const loginHref = next ? `/login?next=${encodeURIComponent(next)}` : "/login";

  return (
    <div className="grid gap-6">
      <AuthHeading
        eyebrow="Join AGI 2027"
        title="Create your account"
        lead="Then tell us about your audience. We review every creator before the first campaign."
      />
      {note && !failure ? <NoteBanner note={note} /> : null}

      {googleEnabled ? (
        <>
          <GoogleButton next={next} label="Sign up with Google" />
          <OrDivider />
        </>
      ) : null}

      {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      <form
        action={dispatch}
        onSubmit={(event) => {
          const element = event.currentTarget;
          setDismissed(state);
          void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
        }}
        noValidate
        aria-label="Sign up with email"
        className="grid gap-5"
      >
        <Field id={`${uid}-name`} label="Your name" error={errors.name?.message}>
          <Input
            id={`${uid}-name`}
            type="text"
            autoComplete="name"
            maxLength={NAME_MAX}
            required
            aria-invalid={errors.name ? true : undefined}
            aria-describedby={fieldDescribedBy(`${uid}-name`, { error: errors.name })}
            className={SCROLL_MARGIN}
            {...form.register("name")}
          />
        </Field>
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
        <Field id={`${uid}-password`} label="Password" hint={PASSWORD_HINT} error={errors.password?.message}>
          <PasswordInput
            id={`${uid}-password`}
            autoComplete="new-password"
            required
            aria-invalid={errors.password ? true : undefined}
            aria-describedby={fieldDescribedBy(`${uid}-password`, { hint: PASSWORD_HINT, error: errors.password })}
            {...form.register("password")}
          />
        </Field>
        <input type="hidden" name="next" value={next ?? ""} />
        <Button type="submit" size="xl" variant="brand" loading={pending} className="w-full">
          {pending ? "Creating your account" : "Create account"}
        </Button>
        <p className="text-center text-[13px] leading-relaxed text-pretty text-muted-foreground">
          By creating an account you agree to our{" "}
          <Link href="/terms" className="underline underline-offset-4 hover:text-foreground">
            Terms
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="underline underline-offset-4 hover:text-foreground">
            Privacy
          </Link>
          .
        </p>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href={loginHref} className="font-semibold text-foreground underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight } from "lucide-react";

import { submitApplication } from "@/app/(auth)/application/actions";
import { SCROLL_MARGIN, ServerAlert, useServerErrors } from "@/components/auth/parts";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { applicationSchema, LIMITS, type Application, type ApplicationInput, type CreatorFormState } from "@/lib/creators/schemas";

import { CharactersLeft, CountrySelect, FormSection, HandleInput, IDLE, NichePicker } from "./form-kit";

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = [
  "displayName",
  "xHandle",
  "country",
  "followers",
  "avgViews",
  "niches",
  "tiktok",
  "youtube",
  "instagram",
  "linkedin",
  "bestPosts.0",
  "bestPosts.1",
  "bestPosts.2",
  "bestPosts",
  "why",
  "referralCode",
] as const;

const SOCIALS = [
  { name: "tiktok", label: "TikTok", placeholder: "tiktok.com/@you" },
  { name: "youtube", label: "YouTube", placeholder: "youtube.com/@you" },
  { name: "instagram", label: "Instagram", placeholder: "instagram.com/you" },
  { name: "linkedin", label: "LinkedIn", placeholder: "linkedin.com/in/you" },
] as const;

const HINTS = {
  xHandle: "The account you'd post from.",
  followers: "Roughly is fine, like 18,400 or 18.4k.",
  avgViews: "A typical post, not your best one.",
  why: "What you post about, who listens, and what you'd like from us.",
  referralCode: "From the creator who sent you, if anyone did.",
};

/**
 * The creator application. One page, four short sections, and it works
 * before the page's JavaScript loads. On success the server refreshes the
 * page, which then shows the application's status instead.
 */
export function ApplicationForm({
  defaultName,
  referralCode,
  previewOnly = false,
}: {
  defaultName: string;
  referralCode: string;
  /** Supabase isn't connected: the form can be tried, and says nothing is saved. */
  previewOnly?: boolean;
}) {
  const uid = useId();
  const id = (name: string) => `${uid}-${name.replace(".", "-")}`;
  const [state, dispatch, pending] = useActionState(submitApplication, IDLE);
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);
  const form = useForm<ApplicationInput, unknown, Application>({
    resolver: zodResolver(applicationSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: {
      displayName: defaultName,
      xHandle: "",
      tiktok: "",
      youtube: "",
      instagram: "",
      linkedin: "",
      niches: [],
      followers: "",
      avgViews: "",
      country: "",
      bestPosts: ["", "", ""],
      why: "",
      referralCode,
    },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  const niches = useWatch({ control: form.control, name: "niches" }) ?? [];
  const why = useWatch({ control: form.control, name: "why" }) ?? "";
  const failure = state.status === "error" && dismissed !== state ? state : null;
  const postErrors = errors.bestPosts;

  const describe = (name: string, hint?: string, error?: unknown) => ({
    id: id(name),
    "aria-invalid": error ? true : undefined,
    "aria-describedby": fieldDescribedBy(id(name), { hint, error }),
    className: SCROLL_MARGIN,
  });

  return (
    <form
      action={dispatch}
      onSubmit={(event) => {
        const element = event.currentTarget;
        setDismissed(state);
        void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
      }}
      noValidate
      aria-label="Creator application"
      className="grid gap-9"
    >
      {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      <FormSection title="About you">
        <Field id={id("displayName")} label="Name you post under" error={errors.displayName?.message}>
          <Input
            {...describe("displayName", undefined, errors.displayName)}
            type="text"
            autoComplete="name"
            maxLength={LIMITS.name}
            required
            // In the server's HTML too, so it's filled in before the page's JavaScript loads.
            defaultValue={defaultName}
            {...form.register("displayName")}
          />
        </Field>
        <Field id={id("xHandle")} label="X handle" hint={HINTS.xHandle} error={errors.xHandle?.message}>
          <HandleInput
            id={id("xHandle")}
            hint={HINTS.xHandle}
            error={errors.xHandle?.message}
            placeholder="yourname"
            required
            register={form.register("xHandle")}
          />
        </Field>
        <Field id={id("country")} label="Country you live in" error={errors.country?.message}>
          <CountrySelect id={id("country")} error={errors.country?.message} register={form.register("country")} />
        </Field>
      </FormSection>

      <FormSection title="Your audience" description="Self reported for now. We check them against your profile.">
        <div className="grid gap-5 sm:grid-cols-2 sm:gap-4">
          <Field id={id("followers")} label="Followers on X" hint={HINTS.followers} error={errors.followers?.message}>
            <Input
              {...describe("followers", HINTS.followers, errors.followers)}
              type="text"
              inputMode="numeric"
              autoComplete="off"
              placeholder="18,400"
              maxLength={20}
              required
              {...form.register("followers")}
            />
          </Field>
          <Field id={id("avgViews")} label="Average views per post" hint={HINTS.avgViews} error={errors.avgViews?.message}>
            <Input
              {...describe("avgViews", HINTS.avgViews, errors.avgViews)}
              type="text"
              inputMode="numeric"
              autoComplete="off"
              placeholder="6,200"
              maxLength={20}
              required
              {...form.register("avgViews")}
            />
          </Field>
        </div>
        <NichePicker id={id("niches")} selected={niches} error={errors.niches?.message} register={form.register("niches")} />
        <fieldset className="min-w-0">
          <legend className="mb-3 text-sm font-medium">
            Other socials <span className="font-normal text-subtle-foreground">(optional)</span>
          </legend>
          <div className="grid gap-4 sm:grid-cols-2">
            {SOCIALS.map((social) => (
              <Field key={social.name} id={id(social.name)} label={social.label} error={errors[social.name]?.message}>
                <Input
                  {...describe(social.name, undefined, errors[social.name])}
                  type="text"
                  inputMode="url"
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  placeholder={social.placeholder}
                  maxLength={2048}
                  {...form.register(social.name)}
                />
              </Field>
            ))}
          </div>
        </fieldset>
      </FormSection>

      <FormSection title="Your best work" description="Links to three posts you're proud of, on any platform.">
        {([0, 1, 2] as const).map((index) => {
          const name = `bestPosts.${index}` as const;
          const error = postErrors?.[index]?.message;
          return (
            <Field key={name} id={id(name)} label={`Post ${index + 1}`} error={error}>
              <Input
                {...describe(name, undefined, error)}
                type="text"
                inputMode="url"
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="x.com/you/status/123"
                maxLength={2048}
                required
                {...form.register(name)}
              />
            </Field>
          );
        })}
        {postErrors?.root?.message || postErrors?.message ? (
          <p role="alert" className="-mt-2 text-[13px] text-destructive-text">
            {postErrors.root?.message ?? postErrors.message}
          </p>
        ) : null}
        <Field id={id("why")} label="Why do you want to join?" hint={HINTS.why} error={errors.why?.message}>
          <Textarea
            {...describe("why", HINTS.why, errors.why)}
            rows={4}
            maxLength={LIMITS.why}
            required
            {...form.register("why")}
          />
          <CharactersLeft value={why} limit={LIMITS.why} />
        </Field>
      </FormSection>

      <Field
        id={id("referralCode")}
        label="Referral code"
        optional
        hint={HINTS.referralCode}
        error={errors.referralCode?.message}
      >
        <Input
          {...describe("referralCode", HINTS.referralCode, errors.referralCode)}
          type="text"
          autoComplete="off"
          autoCapitalize="none"
          spellCheck={false}
          placeholder="8 letters and numbers"
          maxLength={8}
          className={`${SCROLL_MARGIN} font-mono`}
          defaultValue={referralCode}
          {...form.register("referralCode")}
        />
      </Field>

      <div className="grid gap-3 border-t pt-6">
        <Button type="submit" size="xl" variant="brand" loading={pending} className="w-full">
          {pending ? "Sending your application" : "Send application"}
          {pending ? null : <ArrowRight aria-hidden />}
        </Button>
        <p className="text-center text-[13px] leading-relaxed text-pretty text-muted-foreground">
          {previewOnly
            ? "This is a preview. Accounts aren't connected yet, so nothing is sent."
            : "We review every application by hand and email you the answer."}
        </p>
      </div>
    </form>
  );
}

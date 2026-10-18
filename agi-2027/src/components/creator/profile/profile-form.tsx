"use client";

import { startTransition, useActionState, useId, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Lock } from "lucide-react";

import { updateProfile } from "@/app/dashboard/profile/actions";
import { SCROLL_MARGIN, ServerAlert, useServerErrors } from "@/components/auth/parts";
import { CharactersLeft, CountrySelect, FormSection, IDLE, NichePicker, SavedNote } from "@/components/onboarding/form-kit";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { CURRENCIES, type Currency } from "@/lib/campaigns/options";
import { NICHE_VALUES, type Niche } from "@/lib/creators/options";
import type { CreatorProfile } from "@/lib/creators/queries";
import { LIMITS, profileSchema, type CreatorFormState, type ProfileInput, type ProfileValues } from "@/lib/creators/schemas";
import { siteConfig } from "@/lib/site";

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = [
  "displayName",
  "country",
  "bio",
  "followers",
  "avgViews",
  "niches",
  "tiktok",
  "youtube",
  "instagram",
  "linkedin",
  "ratePerPost",
  "rateCurrency",
] as const;

const SOCIALS = [
  { name: "tiktok", label: "TikTok", placeholder: "tiktok.com/@you" },
  { name: "youtube", label: "YouTube", placeholder: "youtube.com/@you" },
  { name: "instagram", label: "Instagram", placeholder: "instagram.com/you" },
  { name: "linkedin", label: "LinkedIn", placeholder: "linkedin.com/in/you" },
] as const;

const HINTS = {
  followers: "Roughly is fine, like 18,400 or 18.4k.",
  avgViews: "A typical post, not your best one.",
  bio: "A line or two on what you post and who follows you.",
  ratePerPost: "What you usually charge for one post.",
};

export type ProfileFormProfile = Pick<
  CreatorProfile,
  | "displayName"
  | "xHandle"
  | "tiktokUrl"
  | "youtubeUrl"
  | "instagramUrl"
  | "linkedinUrl"
  | "niches"
  | "followers"
  | "avgViews"
  | "country"
  | "bio"
  | "ratePerPost"
  | "rateCurrency"
>;

/** 48200 as "48,200". Plain string work, so the server and browser agree. */
function withCommas(value: number | null): string {
  return value === null ? "" : String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function isNiche(value: string): value is Niche {
  return (NICHE_VALUES as readonly string[]).includes(value);
}

function isCurrency(value: string | null): value is Currency {
  return value !== null && (CURRENCIES as readonly string[]).includes(value);
}

function defaultsFrom(profile: ProfileFormProfile): ProfileInput {
  return {
    displayName: profile.displayName,
    tiktok: profile.tiktokUrl ?? "",
    youtube: profile.youtubeUrl ?? "",
    instagram: profile.instagramUrl ?? "",
    linkedin: profile.linkedinUrl ?? "",
    niches: profile.niches.filter(isNiche),
    followers: withCommas(profile.followers),
    avgViews: withCommas(profile.avgViews),
    country: profile.country ?? "",
    bio: profile.bio,
    ratePerPost: profile.ratePerPost ?? "",
    rateCurrency: isCurrency(profile.rateCurrency) ? profile.rateCurrency : undefined,
  };
}

/** "Email us" as a link when there's an address to write to. */
function EmailUsLink({ subject, children }: { subject: string; children: React.ReactNode }) {
  const email = siteConfig.contactEmail.trim();
  if (!email) return <>{children}</>;
  return (
    <a
      href={`mailto:${email}?subject=${encodeURIComponent(subject)}`}
      className="font-medium text-foreground underline decoration-border-strong underline-offset-4 hover:decoration-foreground"
    >
      {children}
    </a>
  );
}

/**
 * The creator's own profile: name, audience, niches, other socials, bio and
 * rate. Checked as they type with the same schema the server uses. The X
 * handle is shown but can't be changed here.
 */
export function ProfileForm({
  profile,
  locked = false,
  previewOnly = false,
}: {
  profile: ProfileFormProfile;
  /** Staff looking at the creator app: everything shows, nothing can be changed. */
  locked?: boolean;
  /** Supabase isn't connected: the form can be tried, and says nothing is saved. */
  previewOnly?: boolean;
}) {
  const uid = useId();
  const id = (name: string) => `${uid}-${name}`;
  const [state, dispatch, pending] = useActionState(updateProfile, IDLE);
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);
  // Fixed at first render. Each field also gets its default as a prop, so the
  // server's HTML shows the saved profile before the page's JavaScript runs.
  const [defaults] = useState(() => defaultsFrom(profile));
  const form = useForm<ProfileInput, unknown, ProfileValues>({
    resolver: zodResolver(profileSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: defaults,
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  const niches = useWatch({ control: form.control, name: "niches" }) ?? [];
  const bio = useWatch({ control: form.control, name: "bio" }) ?? "";
  const shown = dismissed === state ? IDLE : state;
  const failure = shown.status === "error" ? shown : null;

  const describe = (name: string, hint?: string, error?: unknown) => ({
    id: id(name),
    "aria-invalid": error ? true : undefined,
    "aria-describedby": fieldDescribedBy(id(name), { hint, error }),
    className: SCROLL_MARGIN,
  });

  const handleHint = profile.xHandle ? (
    <>
      Your X handle was checked when you joined. <EmailUsLink subject="Change my X handle">Email us</EmailUsLink> to change it.
    </>
  ) : (
    <>
      <EmailUsLink subject="Add my X handle">Email us</EmailUsLink> to add the X account you post from.
    </>
  );

  return (
    <form
      action={dispatch}
      onSubmit={(event) => {
        const element = event.currentTarget;
        setDismissed(state);
        void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
      }}
      // Editing again after a save takes the "Saved" note away.
      onChange={() => {
        if (state.status === "saved" && dismissed !== state) setDismissed(state);
      }}
      noValidate
      aria-label="Your profile"
    >
      <fieldset disabled={locked} className="grid min-w-0 gap-9">
        <FormSection title="About you">
          <Field id={id("displayName")} label="Name you post under" error={errors.displayName?.message}>
            <Input
              {...describe("displayName", undefined, errors.displayName)}
              type="text"
              autoComplete="name"
              maxLength={LIMITS.name}
              required
              defaultValue={defaults.displayName}
              {...form.register("displayName")}
            />
          </Field>
          <Field id={id("xHandle")} label="X handle" hint={handleHint}>
            <div className="relative">
              <Input
                id={id("xHandle")}
                type="text"
                readOnly
                value={profile.xHandle ? `@${profile.xHandle}` : "Not added yet"}
                aria-describedby={`${id("xHandle")}-hint`}
                className="truncate border-dashed bg-surface-2/60 pr-11 text-muted-foreground hover:border-input focus-visible:border-input"
              />
              <Lock aria-hidden className="pointer-events-none absolute top-1/2 right-3.5 size-4 -translate-y-1/2 text-subtle-foreground" />
            </div>
          </Field>
          <Field id={id("country")} label="Country you live in" error={errors.country?.message}>
            <CountrySelect
              id={id("country")}
              error={errors.country?.message}
              defaultValue={defaults.country}
              register={form.register("country")}
            />
          </Field>
          <Field id={id("bio")} label="Short bio" optional hint={HINTS.bio} error={errors.bio?.message}>
            <Textarea
              {...describe("bio", HINTS.bio, errors.bio)}
              rows={3}
              maxLength={LIMITS.bio}
              className={`${SCROLL_MARGIN} min-h-24`}
              defaultValue={defaults.bio}
              {...form.register("bio")}
            />
            <CharactersLeft value={bio} limit={LIMITS.bio} />
          </Field>
        </FormSection>

        <FormSection title="Your audience" description="Self reported for now. Keep them roughly up to date.">
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
                defaultValue={defaults.followers}
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
                defaultValue={defaults.avgViews}
                {...form.register("avgViews")}
              />
            </Field>
          </div>
          <NichePicker id={id("niches")} selected={niches} error={errors.niches?.message} register={form.register("niches")} />
        </FormSection>

        <FormSection title="Other socials" description="Optional. Links to your profiles elsewhere.">
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
                  defaultValue={defaults[social.name]}
                  {...form.register(social.name)}
                />
              </Field>
            ))}
          </div>
        </FormSection>

        <FormSection title="Your rate" description="Optional. Leave it empty if it depends on the campaign.">
          <div className="grid grid-cols-[minmax(0,1fr)_8.5rem] items-start gap-3 sm:max-w-md">
            <Field id={id("ratePerPost")} label="Rate per post" hint={HINTS.ratePerPost} error={errors.ratePerPost?.message}>
              <Input
                {...describe("ratePerPost", HINTS.ratePerPost, errors.ratePerPost)}
                type="text"
                inputMode="decimal"
                autoComplete="off"
                placeholder="150"
                maxLength={14}
                className={`${SCROLL_MARGIN} tabular-nums`}
                defaultValue={defaults.ratePerPost}
                {...form.register("ratePerPost")}
              />
            </Field>
            <Field id={id("rateCurrency")} label="Currency" error={errors.rateCurrency?.message}>
              <NativeSelect
                {...describe("rateCurrency", undefined, errors.rateCurrency)}
                defaultValue={defaults.rateCurrency ?? ""}
                {...form.register("rateCurrency", { setValueAs: (value: string) => value || undefined })}
              >
                <option value="">Pick one</option>
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>
                    {currency}
                  </option>
                ))}
              </NativeSelect>
            </Field>
          </div>
        </FormSection>

        <div className="grid gap-4 border-t pt-6">
          {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Button type="submit" size="lg" loading={pending} className="w-full sm:w-auto">
              {pending ? "Saving" : "Save profile"}
            </Button>
            <SavedNote state={shown} />
          </div>
          {previewOnly ? (
            <p className="text-[13px] text-pretty text-muted-foreground">
              This is a preview. Accounts aren&apos;t connected yet, so nothing is saved.
            </p>
          ) : null}
        </div>
      </fieldset>
    </form>
  );
}

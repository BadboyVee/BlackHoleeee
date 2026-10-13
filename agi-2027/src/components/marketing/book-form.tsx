"use client";

import { startTransition, useActionState, useEffect, useId, useRef, useState } from "react";
import { useForm, useWatch, type UseFormRegisterReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, Check, CircleAlert } from "lucide-react";

import { submitBooking } from "@/app/(marketing)/book/actions";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  BUDGET_RANGES,
  bookingSchema,
  HONEYPOT_FIELD,
  LIMITS,
  STARTED_AT_FIELD,
  type Booking,
  type BookingFormValues,
  type BookingState,
  type LeadSource,
} from "@/lib/leads/booking";
import { siteConfig } from "@/lib/site";
import { cn } from "@/lib/utils";

/*
 * The "Book a campaign" form, on /book and in the home page's final call to
 * action. The browser checks each field with the shared schema as people go
 * (on blur, then as they fix it), and the server action has the last word:
 * its field errors land on the matching fields and its message shows on top.
 */

type Variant = "page" | "compact";
type FieldName = keyof BookingFormValues;

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = [
  "name",
  "email",
  "company",
  "website",
  "xHandle",
  "launching",
  "launchDate",
  "budget",
  "message",
] as const satisfies readonly FieldName[];

const IDLE: BookingState = { status: "idle" };

/** Every text field starts empty; no budget is picked until someone picks one. */
const EMPTY: Partial<BookingFormValues> = {
  name: "",
  email: "",
  company: "",
  website: "",
  xHandle: "",
  launching: "",
  launchDate: "",
  message: "",
};

/** Keeps the field label in view (under the sticky header) when a field gets focus. */
const SCROLL_MARGIN = "scroll-mt-28";

const arrive = { type: "spring", stiffness: 400, damping: 30 } as const;

/** Values the server sent back, as form values. Unknown budgets are dropped. */
function refillValues(values: Partial<Record<FieldName, string>> | undefined): Partial<BookingFormValues> {
  if (!values) return {};
  const { budget, ...rest } = values;
  const known = BUDGET_RANGES.find((range) => range.value === budget)?.value;
  return { ...rest, ...(known ? { budget: known } : {}) };
}

/**
 * The booking form. Sending another after a success remounts the inner form,
 * so the action state, the fields and the fill timer all start fresh.
 */
function BookForm({
  source,
  variant = "page",
  title,
  intro,
  className,
}: {
  source: LeadSource;
  variant?: Variant;
  /** A heading over the form, hidden once it's sent (the thank-you has its own). */
  title?: string;
  intro?: string;
  className?: string;
}) {
  const [round, setRound] = useState(0);
  return (
    <div className={cn("@container", className)}>
      <BookFormBody
        key={round}
        source={source}
        variant={variant}
        title={title}
        intro={intro}
        focusFirst={round > 0}
        onReset={() => setRound((value) => value + 1)}
      />
    </div>
  );
}

function BookFormBody({
  source,
  variant,
  title,
  intro,
  focusFirst,
  onReset,
}: {
  source: LeadSource;
  variant: Variant;
  title?: string;
  intro?: string;
  focusFirst: boolean;
  onReset: () => void;
}) {
  const uid = useId();
  const id = (name: string) => `${uid}-${name}`;
  const compact = variant === "compact";
  const Heading = compact ? "h3" : "h2";
  const reduce = useReducedMotion();

  const [state, dispatch, pending] = useActionState(submitBooking, IDLE);
  // The state whose top message the visitor has moved past by sending again.
  const [dismissed, setDismissed] = useState<BookingState | null>(null);

  // Without JavaScript the form posts natively and the page comes back with the server's
  // answer, so the fields start from the values it sent back. With JavaScript nothing resets them.
  const [initial] = useState<Partial<BookingFormValues>>(() => ({
    ...EMPTY,
    ...(state.status === "error" ? refillValues(state.values) : {}),
  }));
  const form = useForm<BookingFormValues, unknown, Booking>({
    resolver: zodResolver(bookingSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: initial,
  });
  const errors = form.formState.errors;

  const alertRef = useRef<HTMLDivElement>(null);
  const startedAtRef = useRef<HTMLInputElement>(null);
  const handledState = useRef<BookingState>(state);

  // Stamp when the form appeared, in the browser only. Kept if the page is hidden and shown again.
  useEffect(() => {
    const input = startedAtRef.current;
    if (input && !input.value) input.value = String(Date.now());
  }, []);

  useEffect(() => {
    if (focusFirst) form.setFocus("name");
  }, [focusFirst, form]);

  // The server answered: put its field errors on the fields and move focus to the first problem.
  // The fields keep what was typed (nothing resets them), so there's nothing to refill here.
  useEffect(() => {
    if (state === handledState.current) return;
    handledState.current = state;
    if (state.status !== "error") return;

    // Restart the spam timer, so a form left open for over a day can still be sent.
    if (startedAtRef.current) startedAtRef.current.value = String(Date.now());

    let first: FieldName | undefined;
    for (const name of FIELDS) {
      const message = state.fieldErrors?.[name];
      if (!message) continue;
      form.setError(name, { type: "server", message });
      first ??= name;
    }
    if (first) form.setFocus(first);
    else alertRef.current?.focus();
  }, [state, form]);

  const launching = useWatch({ control: form.control, name: "launching" }) ?? "";
  const message = useWatch({ control: form.control, name: "message" }) ?? "";

  const serverMessage = state.status === "error" && dismissed !== state ? state.message : null;
  const xHandle = form.register("xHandle");

  const controlProps = (name: Exclude<FieldName, "budget">, hint?: string) => ({
    id: id(name),
    "aria-invalid": errors[name] ? true : undefined,
    "aria-describedby": fieldDescribedBy(id(name), { hint, error: errors[name] }),
    defaultValue: initial[name],
    className: SCROLL_MARGIN,
  });

  const hints = {
    website: "Your site or the product page.",
    xHandle: "The company account, if there is one.",
    launching: "The product, who it's for and what's new.",
    launchDate: "Roughly is fine.",
    message: "Links, goals, creators you like.",
  };

  return (
    <AnimatePresence mode="wait" initial={false}>
      {state.status === "success" ? (
        <BookingSuccess
          key="success"
          name={state.name}
          email={state.email}
          headingLevel={Heading}
          reduce={Boolean(reduce)}
          onReset={onReset}
        />
      ) : (
        <motion.div
          key="form"
          exit={{ opacity: 0, transition: { duration: 0.15 } }}
        >
          {title ? (
            <div className="mb-6">
              <Heading className="text-h3 text-balance">{title}</Heading>
              {intro ? <p className="mt-1 text-sm text-pretty text-muted-foreground">{intro}</p> : null}
            </div>
          ) : null}
          <form
            action={dispatch}
            onSubmit={(event) => {
              // Check in the browser first. Only a clean form goes to the server, which checks again.
              const element = event.currentTarget;
              setDismissed(state);
              void form.handleSubmit(() => {
                startTransition(() => dispatch(new FormData(element)));
              })(event);
            }}
            noValidate
            aria-label="Book a campaign"
            className={cn("relative grid gap-5 @md:grid-cols-2 @md:gap-x-4", compact ? "gap-y-4" : "@md:gap-y-6")}
          >
            {serverMessage ? (
              <div
                ref={alertRef}
                role="alert"
                tabIndex={-1}
                className={cn(
                  "flex items-start gap-3 rounded-xl border border-destructive-text/35 bg-destructive/8 px-4 py-3.5 text-sm leading-relaxed text-foreground outline-none @md:col-span-2",
                  "focus-visible:ring-4 focus-visible:ring-destructive-text/20",
                  SCROLL_MARGIN,
                )}
              >
                <CircleAlert className="mt-0.5 size-4 shrink-0 text-destructive-text" aria-hidden />
                <p className="min-w-0 text-pretty">
                  <WithEmailLink text={serverMessage} />
                </p>
              </div>
            ) : null}

            <Field id={id("name")} label="Your name" error={errors.name?.message}>
              <Input
                {...controlProps("name")}
                type="text"
                autoComplete="name"
                maxLength={LIMITS.name}
                required
                {...form.register("name")}
              />
            </Field>

            <Field id={id("email")} label="Work email" error={errors.email?.message}>
              <Input
                {...controlProps("email")}
                type="email"
                inputMode="email"
                autoComplete="email"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="you@company.com"
                maxLength={LIMITS.email}
                required
                {...form.register("email")}
              />
            </Field>

            <Field id={id("company")} label="Company" error={errors.company?.message} className="@md:col-span-2">
              <Input
                {...controlProps("company")}
                type="text"
                autoComplete="organization"
                maxLength={LIMITS.company}
                required
                {...form.register("company")}
              />
            </Field>

            <Field id={id("website")} label="Website" optional hint={hints.website} error={errors.website?.message}>
              <Input
                {...controlProps("website", hints.website)}
                type="text"
                inputMode="url"
                autoComplete="url"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="yourcompany.com"
                maxLength={LIMITS.website}
                {...form.register("website")}
              />
            </Field>

            <Field id={id("xHandle")} label="X handle" optional hint={hints.xHandle} error={errors.xHandle?.message}>
              <div className="relative">
                <span
                  aria-hidden
                  className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center text-base text-muted-foreground sm:text-[15px]"
                >
                  @
                </span>
                <Input
                  {...controlProps("xHandle", hints.xHandle)}
                  type="text"
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  placeholder="yourcompany"
                  maxLength={64}
                  {...xHandle}
                  className={cn(SCROLL_MARGIN, "pl-8")}
                  onChange={(event) => {
                    // The @ is already shown, so a typed one would read as "@@".
                    const value = event.target.value;
                    if (value.startsWith("@")) event.target.value = value.replace(/^@+/, "");
                    return xHandle.onChange(event);
                  }}
                />
              </div>
            </Field>

            <Field
              id={id("launching")}
              label="What are you launching?"
              hint={hints.launching}
              error={errors.launching?.message}
              className="@md:col-span-2"
            >
              <Textarea
                {...controlProps("launching", hints.launching)}
                rows={compact ? 3 : 4}
                maxLength={LIMITS.launching}
                required
                className={cn(SCROLL_MARGIN, compact ? "min-h-24" : "min-h-28")}
                {...form.register("launching")}
              />
              <CharactersLeft value={launching} limit={LIMITS.launching} />
            </Field>

            <Field id={id("launchDate")} label="Launch date" optional hint={hints.launchDate} error={errors.launchDate?.message}>
              <Input
                {...controlProps("launchDate", hints.launchDate)}
                type="date"
                className={cn(
                  SCROLL_MARGIN,
                  "appearance-none [&::-webkit-date-and-time-value]:min-h-[1.5em] [&::-webkit-date-and-time-value]:text-left",
                )}
                {...form.register("launchDate")}
              />
            </Field>

            <BudgetChips
              id={id("budget")}
              compact={compact}
              error={errors.budget?.message}
              defaultValue={initial.budget}
              register={form.register("budget")}
              className="@md:col-span-2"
            />

            <Field id={id("message")} label="Anything else?" optional hint={hints.message} error={errors.message?.message} className="@md:col-span-2">
              <Textarea
                {...controlProps("message", hints.message)}
                rows={compact ? 2 : 3}
                maxLength={LIMITS.message}
                className={cn(SCROLL_MARGIN, compact ? "min-h-20" : "min-h-24")}
                {...form.register("message")}
              />
              <CharactersLeft value={message} limit={LIMITS.message} />
            </Field>

            {/* Spam traps. People never see the first one; bots fill it. The second is stamped on load. */}
            <div aria-hidden className="pointer-events-none absolute top-0 -left-[10000px] size-px overflow-hidden opacity-0">
              <label htmlFor={id("hp")}>Leave this field empty</label>
              <input id={id("hp")} type="text" name={HONEYPOT_FIELD} tabIndex={-1} autoComplete="off" />
            </div>
            {/* No value prop: React would put the empty default back on every render. */}
            <input ref={startedAtRef} type="hidden" name={STARTED_AT_FIELD} />
            <input type="hidden" name="source" value={source} />

            <div
              className={cn(
                "flex flex-col gap-3 pt-1 @md:col-span-2 @md:flex-row-reverse @md:items-center @md:justify-between",
                compact ? "" : "border-t pt-6",
              )}
            >
              <Button
                type="submit"
                size="xl"
                variant={compact ? "default" : "brand"}
                loading={pending}
                className="w-full @md:w-auto"
              >
                {pending ? "Sending" : "Send request"}
                {pending ? null : <ArrowRight aria-hidden />}
              </Button>
              <p className="text-center text-[13px] text-muted-foreground @md:text-left">
                We reply within one working day.
              </p>
            </div>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Radio chips for the budget range. Arrow keys move between them, like any radio group. */
function BudgetChips({
  id,
  compact,
  error,
  defaultValue,
  register,
  className,
}: {
  id: string;
  compact: boolean;
  error?: string;
  defaultValue?: string;
  register: UseFormRegisterReturn<"budget">;
  className?: string;
}) {
  return (
    <fieldset
      role="radiogroup"
      aria-labelledby={`${id}-legend`}
      aria-describedby={error ? `${id}-error` : undefined}
      aria-invalid={error ? true : undefined}
      aria-required
      className={cn("group/budget min-w-0", className)}
    >
      <legend id={`${id}-legend`} className="mb-2 text-sm leading-none font-medium">
        Budget
      </legend>
      <div className="flex flex-wrap gap-2">
        {BUDGET_RANGES.map((range) => (
          <label key={range.value} className="relative cursor-pointer">
            <input
              type="radio"
              value={range.value}
              defaultChecked={range.value === defaultValue}
              className={cn("peer sr-only", SCROLL_MARGIN)}
              {...register}
            />
            <span
              className={cn(
                "inline-flex h-11 items-center rounded-full border border-border-strong bg-surface font-medium text-foreground select-none",
                compact ? "px-3 text-sm" : "px-4 text-[15px]",
                "transition-[background-color,border-color,color,box-shadow] duration-150 ease-snap",
                "hover:border-foreground/40 hover:bg-surface-2",
                "group-aria-invalid/budget:border-destructive-text",
                "peer-checked:border-foreground peer-checked:bg-foreground peer-checked:text-background",
                "peer-focus-visible:ring-4 peer-focus-visible:ring-ring/25",
              )}
            >
              {range.label}
            </span>
          </label>
        ))}
      </div>
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-2 flex items-start gap-1.5 text-[13px] leading-snug text-destructive-text">
          <CircleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}

/** A quiet count that appears near the limit. */
function CharactersLeft({ value, limit }: { value: string; limit: number }) {
  const left = limit - value.length;
  if (left > 100) return null;
  return (
    <p aria-live="polite" className={cn("text-right text-xs tabular-nums", left <= 20 ? "text-destructive-text" : "text-muted-foreground")}>
      {left === 1 ? "1 character left" : `${left} characters left`}
    </p>
  );
}

/** The server's message, with the contact address as a link when it's in there. */
function WithEmailLink({ text }: { text: string }) {
  const email = siteConfig.contactEmail.trim();
  const at = email ? text.indexOf(email) : -1;
  if (at < 0) return <>{text}</>;
  return (
    <>
      {text.slice(0, at)}
      <a href={`mailto:${email}`} className="font-medium underline underline-offset-4 hover:decoration-2">
        {email}
      </a>
      {text.slice(at + email.length)}
    </>
  );
}

const NEXT_STEPS = [
  "We read your brief and check which creators fit.",
  "A short call to talk through the launch and the date.",
  "A plan with the right creators, ready to go.",
];

function BookingSuccess({
  name,
  email,
  headingLevel,
  reduce,
  onReset,
}: {
  name: string;
  email: string;
  headingLevel: "h2" | "h3";
  reduce: boolean;
  onReset: () => void;
}) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  const Heading = headingLevel;

  // Bring the thank-you into view and give it focus, so it's seen and read out.
  useEffect(() => {
    const heading = headingRef.current;
    if (!heading) return;
    heading.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
    heading.focus({ preventScroll: true });
  }, [reduce]);

  const rise = (delay: number) =>
    reduce
      ? { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.3, delay } }
      : {
          initial: { opacity: 0, y: 14, filter: "blur(6px)" },
          animate: { opacity: 1, y: 0, filter: "blur(0px)" },
          transition: { ...arrive, delay, opacity: { duration: 0.4, delay }, filter: { duration: 0.45, delay } },
        };

  return (
    <motion.div key="success" className="py-2">
      <motion.div
        aria-hidden
        className="flex size-12 items-center justify-center rounded-full bg-foreground text-background"
        initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.6 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={reduce ? { duration: 0.3 } : { type: "spring", stiffness: 500, damping: 18 }}
      >
        <Check className="size-6" strokeWidth={2.5} />
      </motion.div>
      <motion.div {...rise(0.08)}>
        <Heading
          ref={headingRef}
          tabIndex={-1}
          className="mt-5 scroll-mt-28 text-[clamp(1.5rem,1.3rem+0.8vw,2rem)] leading-tight font-semibold tracking-[-0.03em] text-balance outline-none"
        >
          Thanks, {name}.
        </Heading>
        <p className="mt-2 text-[15px] leading-relaxed text-pretty text-muted-foreground">
          We&apos;ll reply to <span className="font-medium break-all text-foreground">{email}</span> within one working day.
        </p>
      </motion.div>
      <motion.div {...rise(0.16)} className="mt-6 border-t pt-5">
        <p className="text-label text-muted-foreground">What happens next</p>
        <ol className="mt-3 grid gap-3">
          {NEXT_STEPS.map((step, index) => (
            <li key={step} className="flex items-start gap-3 text-[15px] leading-snug">
              <span
                aria-hidden
                className="mt-px flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-2 text-xs font-semibold tabular-nums"
              >
                {index + 1}
              </span>
              <span className="text-pretty">{step}</span>
            </li>
          ))}
        </ol>
      </motion.div>
      <motion.div {...rise(0.24)} className="mt-6">
        <Button type="button" variant="ghost" className="-ml-3 h-11" onClick={onReset}>
          Send another
        </Button>
      </motion.div>
    </motion.div>
  );
}

export { BookForm };

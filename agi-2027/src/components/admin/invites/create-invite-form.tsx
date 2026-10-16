"use client";

import { startTransition, useActionState, useEffect, useId, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";

import { createInvite } from "@/app/admin/invites/actions";
import { SCROLL_MARGIN, ServerAlert, useServerErrors } from "@/components/auth/parts";
import { chipClass, GroupError, IDLE, SavedNote } from "@/components/onboarding/form-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { INVITE_EXPIRY, inviteSchema, LIMITS, type CreatorFormState } from "@/lib/creators/schemas";
import { cn } from "@/lib/utils";

import { CharCount, describedBy, FormField } from "../form-field";

type InviteInput = z.input<typeof inviteSchema>;
type InviteValues = z.output<typeof inviteSchema>;

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = ["label", "maxUses", "expiresIn"] as const;

const DEFAULTS: InviteInput = { label: "", maxUses: "", expiresIn: "never" };

const HINTS = {
  label: "Only you see this, like Telegram group, November.",
  maxUses: "Leave it empty for no limit.",
};

/**
 * Makes a new invite link. The schema checks in the browser first and the
 * server action has the last word. The expiry chips are native radios with
 * "Never" checked in the HTML, so the form posts before JavaScript loads.
 * On success the server refreshes the list and the fields clear for the next.
 */
export function CreateInviteForm() {
  const uid = useId();
  const labelId = `${uid}-label`;
  const usesId = `${uid}-uses`;
  const expiryId = `${uid}-expiry`;
  const [state, dispatch, pending] = useActionState(createInvite, IDLE);
  // The answer to the last try, hidden once the next one is on its way.
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);

  const form = useForm<InviteInput, unknown, InviteValues>({
    resolver: zodResolver(inviteSchema),
    mode: "onTouched",
    reValidateMode: "onChange",
    defaultValues: DEFAULTS,
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  // A new link is made: clear the fields for the next one and keep focus near the answer.
  const savedRef = useRef<HTMLDivElement>(null);
  const handled = useRef(state);
  useEffect(() => {
    if (state === handled.current) return;
    handled.current = state;
    if (state.status !== "saved") return;
    form.reset(DEFAULTS);
    savedRef.current?.focus();
  }, [state, form]);

  const label = useWatch({ control: form.control, name: "label" }) ?? "";
  const shown = dismissed === state ? IDLE : state;
  const failure = shown.status === "error" ? shown : null;
  const expiryError = errors.expiresIn ? "Pick when the link stops working." : undefined;

  return (
    <form
      action={dispatch}
      onSubmit={(event) => {
        const element = event.currentTarget;
        setDismissed(state);
        void form.handleSubmit(() => startTransition(() => dispatch(new FormData(element))))(event);
      }}
      noValidate
      aria-label="New invite link"
      className="grid grid-cols-1 gap-5"
    >
      {failure && !failure.fieldErrors ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      <FormField
        id={labelId}
        label="Who's it for?"
        optional
        hint={HINTS.label}
        error={errors.label?.message}
        aside={label.length > LIMITS.label - 20 ? <CharCount value={label} max={LIMITS.label} /> : null}
      >
        <Input
          id={labelId}
          type="text"
          autoComplete="off"
          maxLength={LIMITS.label}
          aria-invalid={errors.label ? true : undefined}
          aria-describedby={describedBy(labelId, { hint: HINTS.label, error: errors.label })}
          className={SCROLL_MARGIN}
          {...form.register("label")}
        />
      </FormField>

      <FormField id={usesId} label="Use limit" optional hint={HINTS.maxUses} error={errors.maxUses?.message}>
        <Input
          id={usesId}
          type="text"
          inputMode="numeric"
          autoComplete="off"
          placeholder="No limit"
          maxLength={6}
          aria-invalid={errors.maxUses ? true : undefined}
          aria-describedby={describedBy(usesId, { hint: HINTS.maxUses, error: errors.maxUses })}
          className={cn(SCROLL_MARGIN, "tabular sm:max-w-48")}
          {...form.register("maxUses")}
        />
      </FormField>

      <fieldset
        aria-describedby={expiryError ? `${expiryId}-error` : undefined}
        aria-invalid={expiryError ? true : undefined}
        className="group/expiry min-w-0"
      >
        <legend className="mb-2.5 text-sm leading-5 font-medium text-foreground">Stops working</legend>
        <div className="flex flex-wrap gap-2">
          {INVITE_EXPIRY.map((option) => (
            <label key={option.value} className="relative cursor-pointer">
              <input
                type="radio"
                value={option.value}
                defaultChecked={option.value === DEFAULTS.expiresIn}
                className={cn("peer sr-only", SCROLL_MARGIN)}
                {...form.register("expiresIn")}
              />
              <span className={cn(chipClass, "group-aria-invalid/expiry:border-destructive-text")}>{option.label}</span>
            </label>
          ))}
        </div>
        <GroupError id={`${expiryId}-error`} message={expiryError} />
      </fieldset>

      <div className="grid grid-cols-1 gap-3 border-t pt-5">
        <Button type="submit" variant="brand" size="lg" loading={pending} className="w-full">
          {pending ? "Creating link" : "Create link"}
        </Button>
        <div ref={savedRef} tabIndex={-1} className="outline-none empty:hidden">
          <SavedNote state={shown} />
        </div>
      </div>
    </form>
  );
}

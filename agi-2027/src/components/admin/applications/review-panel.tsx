import { startTransition, useActionState, useEffect, useId, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";
import { Check, CircleCheck, CircleX, X } from "lucide-react";

import { reviewApplication } from "@/app/admin/applications/actions";
import { SCROLL_MARGIN, ServerAlert, useServerErrors } from "@/components/auth/parts";
import { CharactersLeft, chipClass, GroupError, IDLE, SavedNote } from "@/components/onboarding/form-kit";
import { Button } from "@/components/ui/button";
import { Field, fieldDescribedBy } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { NOT_CONNECTED } from "@/lib/creators/messages";
import type { ApplicationRow } from "@/lib/creators/queries";
import { LIMITS, reviewSchema, type CreatorFormState } from "@/lib/creators/schemas";
import { applicationStatusMeta } from "@/lib/statuses";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";

/*
 * The bottom of an application card: the approve or reject form while it
 * waits, then who decided and the team's note. The action refreshes the
 * page, so the card picks up its new status from the server and the answer
 * shows where the form was.
 */

type ReviewInput = z.input<typeof reviewSchema>;
type ReviewValues = z.output<typeof reviewSchema>;

/** The fields in the order the form shows them, so focus goes to the first problem. */
const FIELDS = ["decision", "note"] as const;

const NOTE_HINT = "Private. Only the team sees it, never the creator.";

const DECISIONS = [
  { value: "approve", label: "Approve", icon: Check },
  { value: "reject", label: "Reject", icon: X },
] as const;

function submitLabel(decision: ReviewInput["decision"] | undefined, pending: boolean): string {
  if (!decision) return "Pick approve or reject";
  if (pending) return decision === "approve" ? "Approving" : "Rejecting";
  return decision === "approve" ? "Approve and email them" : "Reject and email them";
}

export function ReviewPanel({
  row,
  preview,
  onReviewStart,
}: {
  row: ApplicationRow;
  /** Supabase isn't connected: the form can be tried, and says nothing is saved. */
  preview: boolean;
  /** Called as the decision is sent, so the list keeps this card in view to show the answer. */
  onReviewStart: (id: string) => void;
}) {
  const uid = useId();
  const noteId = `${uid}-note`;
  const decisionErrorId = `${uid}-decision-error`;
  const [serverState, dispatch, pending] = useActionState(reviewApplication, IDLE);
  // A preview has no accounts to save to, so it answers here instead of asking the server.
  const [previewState, setPreviewState] = useState<CreatorFormState | null>(null);
  const state = previewState ?? serverState;
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);

  const form = useForm<ReviewInput, unknown, ReviewValues>({
    resolver: zodResolver(reviewSchema),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: { note: "" },
  });
  const errors = form.formState.errors;
  const alertRef = useRef<HTMLDivElement>(null);
  useServerErrors(state, form, FIELDS, alertRef);

  // The form goes away once it's decided, so focus moves to the answer instead of being lost.
  const savedRef = useRef<HTMLDivElement>(null);
  const announced = useRef(state);
  useEffect(() => {
    if (state === announced.current) return;
    announced.current = state;
    if (state.status === "saved") savedRef.current?.focus();
  }, [state]);

  const decision = useWatch({ control: form.control, name: "decision" });
  const note = useWatch({ control: form.control, name: "note" }) ?? "";
  const failure = state.status === "error" && dismissed !== state ? state : null;
  const onField = Boolean(failure?.fieldErrors?.decision || failure?.fieldErrors?.note);
  // Any problem with the decision itself can only mean nothing was picked.
  const decisionError = errors.decision ? "Pick approve or reject." : undefined;
  const open = row.status === "submitted" && state.status !== "saved";

  return (
    <div className="grid grid-cols-1 gap-4 border-t bg-surface-2/35 px-4 py-4 sm:px-5">
      {failure && !onField ? <ServerAlert ref={alertRef} message={failure.message} /> : null}

      {open ? (
        <form
          action={dispatch}
          onSubmit={(event) => {
            const element = event.currentTarget;
            setDismissed(state);
            void form.handleSubmit(() => {
              if (preview) {
                setPreviewState({ status: "error", message: NOT_CONNECTED });
                return;
              }
              onReviewStart(row.id);
              startTransition(() => dispatch(new FormData(element)));
            })(event);
          }}
          noValidate
          aria-label={`Review ${row.applicant.displayName}`}
          className="grid grid-cols-1 gap-4"
        >
          <input type="hidden" name="id" value={row.id} />

          <fieldset
            aria-describedby={decisionError ? decisionErrorId : undefined}
            aria-invalid={decisionError ? true : undefined}
            className="group/decision min-w-0"
          >
            <legend className="mb-2.5 text-sm leading-none font-medium">Your decision</legend>
            <div className="flex flex-wrap gap-2">
              {DECISIONS.map((choice) => {
                const Icon = choice.icon;
                return (
                  <label key={choice.value} className="relative cursor-pointer">
                    <input
                      type="radio"
                      value={choice.value}
                      className={cn("peer sr-only", SCROLL_MARGIN)}
                      {...form.register("decision")}
                    />
                    <span className={cn(chipClass, "gap-2 group-aria-invalid/decision:border-destructive-text")}>
                      <Icon className="size-4" aria-hidden />
                      {choice.label}
                    </span>
                  </label>
                );
              })}
            </div>
            <GroupError id={decisionErrorId} message={decisionError} />
          </fieldset>

          <Field id={noteId} label="Team note" optional hint={NOTE_HINT} error={errors.note?.message}>
            <Textarea
              id={noteId}
              rows={2}
              maxLength={LIMITS.note}
              aria-invalid={errors.note ? true : undefined}
              aria-describedby={fieldDescribedBy(noteId, { hint: NOTE_HINT, error: errors.note })}
              className={cn(SCROLL_MARGIN, "min-h-20")}
              {...form.register("note")}
            />
            <CharactersLeft value={note} limit={LIMITS.note} />
          </Field>

          <div className="flex sm:justify-end">
            <Button
              type="submit"
              size="lg"
              variant={decision === "approve" ? "brand" : "default"}
              disabled={!decision}
              loading={pending}
              className="w-full sm:w-auto"
            >
              {submitLabel(decision, pending)}
            </Button>
          </div>
        </form>
      ) : (
        <Outcome row={row} />
      )}

      <div ref={savedRef} tabIndex={-1} className="outline-none empty:hidden">
        <SavedNote state={state} />
      </div>
    </div>
  );
}

/** "Approved by Theo on 3 Nov 2026", and the team's note when there is one. */
function Outcome({ row }: { row: ApplicationRow }) {
  if (row.status === "submitted") return null;
  const meta = applicationStatusMeta[row.status];
  const Icon = row.status === "approved" ? CircleCheck : CircleX;
  const verb = row.status === "approved" ? "Approved" : "Rejected";
  const on = row.reviewedAt ? ` on ${formatUtcDate(row.reviewedAt)}` : "";
  const line =
    row.invited && row.status === "approved"
      ? `Approved through an invite link${on}`
      : row.reviewer
        ? `${verb} by ${row.reviewer.displayName}${on}`
        : `${verb}${on}`;
  const teamNote = row.reviewNote?.trim();

  return (
    <div className="grid grid-cols-1 gap-3">
      <p data-tone={meta.tone} className="flex items-start gap-2 text-sm font-medium text-foreground">
        <Icon className="mt-0.5 size-4 shrink-0 text-(--tone-fg)" aria-hidden />
        <span className="min-w-0 break-words">{line}</span>
      </p>
      {teamNote ? (
        <div className="min-w-0 rounded-md border bg-surface px-3.5 py-3">
          <p className="text-label text-subtle-foreground">Team note</p>
          <p className="mt-1.5 text-sm leading-relaxed break-words whitespace-pre-line text-pretty text-foreground">
            {teamNote}
          </p>
        </div>
      ) : null}
    </div>
  );
}

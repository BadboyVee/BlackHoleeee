"use client";

import { useActionState, useEffect, useId, useRef, useState } from "react";
import { PowerOff } from "lucide-react";

import { revokeInvite } from "@/app/admin/invites/actions";
import { GroupError, IDLE, SavedNote } from "@/components/onboarding/form-kit";
import { Button } from "@/components/ui/button";
import type { CreatorFormState } from "@/lib/creators/schemas";
import type { InviteStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";

/** Small buttons in the row, a full 44px tall on touch screens. */
const touch = "pointer-coarse:h-11 pointer-coarse:px-4 pointer-coarse:text-sm";

/**
 * Switches an active link off, after a second tap to make sure. The action
 * refreshes the page, so the row picks up its new status from the server
 * and the answer shows where the buttons were.
 */
export function SwitchOff({
  id,
  status,
  describedBy,
  className,
}: {
  id: string;
  status: InviteStatus;
  /** Ids of the row's name and date, so the buttons say which link they act on. */
  describedBy?: string;
  className?: string;
}) {
  const uid = useId();
  const errorId = `${uid}-error`;
  const questionId = `${uid}-question`;
  const [state, dispatch, pending] = useActionState(revokeInvite, IDLE);
  const [confirming, setConfirming] = useState(false);
  // The answer to the last try, hidden once they cancel or try again.
  const [dismissed, setDismissed] = useState<CreatorFormState | null>(null);

  const startRef = useRef<HTMLButtonElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const savedRef = useRef<HTMLDivElement>(null);

  // Focus follows the buttons as they swap, so it's never dropped on the page.
  const step = useRef(confirming);
  useEffect(() => {
    if (step.current === confirming) return;
    step.current = confirming;
    (confirming ? cancelRef : startRef).current?.focus();
  }, [confirming]);

  const handled = useRef(state);
  useEffect(() => {
    if (state === handled.current) return;
    handled.current = state;
    if (state.status === "saved") savedRef.current?.focus();
    else if (state.status === "error") confirmRef.current?.focus();
  }, [state]);

  if (state.status === "saved") {
    return (
      <div ref={savedRef} tabIndex={-1} className={cn("outline-none", className)}>
        <SavedNote state={state} />
      </div>
    );
  }
  if (status !== "valid") return null;

  const error = state.status === "error" && dismissed !== state ? state.message : undefined;

  function cancel() {
    setDismissed(state);
    setConfirming(false);
  }

  return (
    <div className={cn("min-w-0", className)}>
      {confirming ? (
        <form
          action={dispatch}
          aria-labelledby={questionId}
          onSubmit={() => setDismissed(state)}
          onKeyDown={(event) => {
            if (event.key === "Escape" && !pending) {
              event.preventDefault();
              cancel();
            }
          }}
          className="flex flex-wrap items-center gap-x-3 gap-y-2"
        >
          <input type="hidden" name="id" value={id} />
          <p id={questionId} className="text-[13px] font-medium text-foreground">Switch off for good?</p>
          <div className="flex items-center gap-2">
            <Button
              ref={confirmRef}
              type="submit"
              variant="destructive"
              size="sm"
              loading={pending}
              aria-describedby={[describedBy, error ? errorId : null].filter(Boolean).join(" ") || undefined}
              className={touch}
            >
              {pending ? "Switching off" : "Yes, switch it off"}
            </Button>
            <Button ref={cancelRef} type="button" variant="ghost" size="sm" disabled={pending} onClick={cancel} className={touch}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button
          ref={startRef}
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setConfirming(true)}
          aria-describedby={describedBy}
          className={cn(touch, "text-muted-foreground hover:text-foreground")}
        >
          <PowerOff className="size-3.5" aria-hidden />
          Switch off
        </Button>
      )}
      <GroupError id={errorId} message={error} />
    </div>
  );
}

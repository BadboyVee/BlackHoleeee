"use client";

import { useActionState, useEffect, useRef } from "react";
import { ArrowRight } from "lucide-react";

import { redeemInvite } from "@/app/(auth)/application/actions";
import { ServerAlert } from "@/components/auth/parts";
import { Button } from "@/components/ui/button";

import { IDLE } from "./form-kit";

/**
 * Accepts an invite for the signed-in applicant. A plain form, so it works
 * before the page's JavaScript loads. On success the action moves them on to
 * the creator dashboard; otherwise its answer shows above the button.
 */
export function AcceptInvite({ code }: { code: string }) {
  const [state, dispatch, pending] = useActionState(redeemInvite, IDLE);
  const alertRef = useRef<HTMLDivElement>(null);

  // A new answer gets focus, so it's seen and read out.
  useEffect(() => {
    if (state.status === "error") alertRef.current?.focus();
  }, [state]);

  return (
    <form action={dispatch} aria-label="Accept invite" className="grid gap-4">
      {state.status === "error" ? <ServerAlert ref={alertRef} message={state.message} /> : null}
      <input type="hidden" name="code" value={code} />
      <Button type="submit" variant="brand" size="xl" loading={pending} className="w-full">
        {pending ? "Joining" : "Accept invite"}
        {pending ? null : <ArrowRight aria-hidden />}
      </Button>
    </form>
  );
}

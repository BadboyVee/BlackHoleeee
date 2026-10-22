"use client";

import { Clock, Mail } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LocalDateTime } from "@/components/ui/local-time";
import { initialsFor } from "@/lib/auth/account-display";
import type { SignupRow } from "@/lib/creators/queries";

import { reminderHref } from "./tabs";

/*
 * People who made an account but never sent the form. Each row has their
 * email and a button that opens a ready reminder in the team's mail app.
 */
export function SignupList({ signups, applyUrl }: { signups: SignupRow[]; applyUrl: string }) {
  return (
    <ul className="divide-y overflow-hidden rounded-lg border bg-surface">
      {signups.map((signup) => {
        const name = signup.displayName.trim() || "No name given";
        const remind = reminderHref(signup, applyUrl);
        return (
          <li key={signup.id} className="flex min-w-0 items-center gap-3 px-4 py-3 sm:px-5">
            <Avatar className="size-9">
              <AvatarFallback className="text-[11px]">{initialsFor(name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="text-[15px] leading-snug font-semibold tracking-[-0.01em] break-words">{name}</p>
              {signup.email ? (
                <p className="text-[13px] wrap-anywhere text-muted-foreground select-all">{signup.email}</p>
              ) : null}
              <p className="mt-0.5 inline-flex items-center gap-1.5 text-[13px] text-subtle-foreground">
                <Clock className="size-3.5 shrink-0" aria-hidden />
                <span>
                  Signed up <LocalDateTime value={signup.createdAt} />
                </span>
              </p>
            </div>
            {remind ? (
              <a
                href={remind}
                className="pressable inline-flex h-11 shrink-0 items-center gap-2 rounded-full border border-border-strong px-4 text-sm font-medium text-foreground outline-none transition-colors hover:bg-surface-2 focus-visible:ring-4 focus-visible:ring-ring/20"
              >
                <Mail className="size-4" aria-hidden />
                Remind
                <span className="sr-only"> {name} by email</span>
              </a>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

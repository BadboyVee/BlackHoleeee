"use client";

import { useId, useState } from "react";
import { motion } from "motion/react";
import { CalendarPlus, Clock, Info, PowerOff, Ticket, Users } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { EmptyState } from "@/components/ui/empty-state";
import { LocalDateTime } from "@/components/ui/local-time";
import { formatUtcDate } from "@/lib/time";
import { cn } from "@/lib/utils";

import { springArrive } from "../motion";
import { Panel } from "../panel";
import { InviteLinkField } from "./invite-link";
import type { InviteView } from "./invite-view";
import { SwitchOff } from "./switch-off";

/*
 * Every invite link, newest first. Active links lead with their address and
 * a Copy button; links that no longer work stay in the list, quieter, so the
 * admin can see what was shared and how far it went.
 */

function summary(invites: readonly InviteView[]): string | undefined {
  if (invites.length === 0) return undefined;
  const active = invites.filter((invite) => invite.status === "valid").length;
  const links = invites.length === 1 ? "1 link" : `${invites.length} links`;
  return `${links}, ${active} active. Newest first.`;
}

export function InviteList({ invites }: { invites: InviteView[] }) {
  // Links already here when the page opened. Any others were made just now and get a moment of attention.
  const [known] = useState(() => new Set(invites.map((invite) => invite.id)));

  return (
    <Panel id="invite-links" title="Your links" description={summary(invites)}>
      {invites.length === 0 ? (
        <EmptyState
          className="m-4 border-dashed"
          icon={Ticket}
          title="No invite links yet"
          description="Create one and share it with creators you'd approve anyway. They skip the application and join straight away."
        />
      ) : (
        <>
          <ul className="divide-y">
            {invites.map((invite) => (
              <InviteItem key={invite.id} invite={invite} fresh={!known.has(invite.id)} />
            ))}
          </ul>
          <p className="flex items-start gap-2 border-t bg-surface-2/35 px-4 py-3 text-[13px] leading-snug text-pretty text-muted-foreground sm:px-5">
            <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            Switching a link off stops new sign ups. People who already joined stay in.
          </p>
        </>
      )}
    </Panel>
  );
}

function InviteItem({ invite, fresh }: { invite: InviteView; fresh: boolean }) {
  const uid = useId();
  const nameId = `${uid}-name`;
  const createdId = `${uid}-created`;
  const describedBy = `${nameId} ${createdId}`;
  const active = invite.status === "valid";

  return (
    <motion.li
      initial={fresh ? { opacity: 0, y: -8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={springArrive}
      className={cn("grid min-w-0 grid-cols-1 gap-3 px-4 py-4 sm:px-5", !active && "bg-surface-2/30")}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3
            id={nameId}
            className={cn("text-sm leading-5 font-medium break-words", active ? "text-foreground" : "text-muted-foreground")}
          >
            {invite.label || <span className="font-normal text-muted-foreground">No label</span>}
          </h3>
          {fresh ? <p className="mt-0.5 text-xs font-medium text-brand-text">Just created</p> : null}
        </div>
        <StatusBadge kind="invite" status={invite.status} />
      </div>

      <InviteLinkField link={invite.link} code={invite.code} active={active} describedBy={describedBy} />

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
        <ul className="flex min-w-0 flex-wrap gap-x-4 gap-y-1.5 text-[13px] leading-5 text-muted-foreground">
          <li className="inline-flex min-w-0 items-center gap-1.5">
            <Users className="size-3.5 shrink-0" aria-hidden />
            <span className="tabular">{invite.usage}</span>
            {invite.maxUses ? <UsageBar uses={invite.uses} maxUses={invite.maxUses} /> : null}
          </li>
          <li className="inline-flex min-w-0 items-center gap-1.5">
            <Ending invite={invite} />
          </li>
          <li id={createdId} className="inline-flex min-w-0 items-center gap-1.5">
            <CalendarPlus className="size-3.5 shrink-0" aria-hidden />
            {`Created ${formatUtcDate(invite.createdAt)}`}
          </li>
        </ul>
        <SwitchOff id={invite.id} status={invite.status} describedBy={describedBy} />
      </div>
    </motion.li>
  );
}

/** How full a link with a use limit is. The text beside it says the same in words. */
function UsageBar({ uses, maxUses }: { uses: number; maxUses: number }) {
  const filled = Math.min(1, uses / maxUses);
  return (
    <span aria-hidden className="ml-0.5 block h-1 w-12 shrink-0 overflow-hidden rounded-full bg-surface-3">
      <span
        className={cn("block h-full rounded-full", filled >= 1 ? "bg-subtle-foreground" : "bg-foreground/70")}
        style={{ width: `${Math.round(filled * 100)}%` }}
      />
    </span>
  );
}

/** When it stopped or stops working: switched off, expired, expires, or never. */
function Ending({ invite }: { invite: InviteView }) {
  if (invite.status === "revoked" && invite.revokedAt) {
    return (
      <>
        <PowerOff className="size-3.5 shrink-0" aria-hidden />
        <span className="min-w-0">
          Switched off <LocalDateTime value={invite.revokedAt} />
        </span>
      </>
    );
  }
  return (
    <>
      <Clock className="size-3.5 shrink-0" aria-hidden />
      {invite.expiresAt ? (
        <span className="min-w-0">
          {invite.expiryPassed ? "Expired" : "Expires"} <LocalDateTime value={invite.expiresAt} />
        </span>
      ) : (
        "Never expires"
      )}
    </>
  );
}

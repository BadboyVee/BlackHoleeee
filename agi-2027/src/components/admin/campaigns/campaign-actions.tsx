"use client";

import Link from "next/link";
import { CircleCheckBig, Copy, Ellipsis, ExternalLink, Pause, Pencil, Play, SquareX } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { CampaignStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";
import { previewOnly } from "../preview-toast";

/** Which status changes make sense from where (see PLAN.md, status flows). */
export function statusActions(status: CampaignStatus) {
  return {
    pause: status === "live" || status === "full",
    resume: status === "paused",
    close: status === "live" || status === "full" || status === "paused",
    complete: status === "closed",
  };
}

export const statusActionCopy = {
  pause: "Pausing hides it from new claims. Creators already on it carry on.",
  resume: "Resuming opens it to new claims again, if slots are left.",
  close: "Closing stops new claims for good. Claims in progress carry on.",
  complete: "Marking it complete settles it. Do it once every claim is paid, expired or cancelled.",
} as const;

/** The ⋯ menu on a campaign row: open, edit, duplicate, and status changes. */
export function CampaignRowActions({
  id,
  title,
  status,
  className,
  showOpen = true,
}: {
  id: string;
  title: string;
  status: CampaignStatus;
  className?: string;
  showOpen?: boolean;
}) {
  const actions = statusActions(status);
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className={cn("relative z-10 text-muted-foreground hover:text-foreground pointer-coarse:size-11", className)}
          aria-label={`Actions for ${title}`}
        >
          <Ellipsis />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="truncate text-xs font-normal text-muted-foreground">{title}</DropdownMenuLabel>
        {showOpen ? (
          <DropdownMenuItem asChild>
            <Link href={`/admin/campaigns/${id}`}>
              <ExternalLink />
              Open
            </Link>
          </DropdownMenuItem>
        ) : null}
        <DropdownMenuItem asChild>
          <Link href={`/admin/campaigns/${id}/edit`}>
            <Pencil />
            Edit
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href={`/admin/campaigns/new?from=${id}`}>
            <Copy />
            Duplicate
          </Link>
        </DropdownMenuItem>
        {actions.pause || actions.resume || actions.close || actions.complete ? <DropdownMenuSeparator /> : null}
        {actions.pause ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.pause)}>
            <Pause />
            Pause
          </DropdownMenuItem>
        ) : null}
        {actions.resume ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.resume)}>
            <Play />
            Resume
          </DropdownMenuItem>
        ) : null}
        {actions.close ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.close)}>
            <SquareX />
            Close
          </DropdownMenuItem>
        ) : null}
        {actions.complete ? (
          <DropdownMenuItem onSelect={() => previewOnly(statusActionCopy.complete)}>
            <CircleCheckBig />
            Mark complete
          </DropdownMenuItem>
        ) : null}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

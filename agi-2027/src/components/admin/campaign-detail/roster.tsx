"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Check,
  CircleCheck,
  Ellipsis,
  ExternalLink,
  MessageSquareWarning,
  Shuffle,
  Timer,
  Wallet,
  X,
  XCircle,
} from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { DemoCampaign } from "@/lib/campaigns/demo";
import { formatMoney, totalsByCurrency } from "@/lib/money";
import type { ClaimStatus } from "@/lib/statuses";
import { cn } from "@/lib/utils";
import { brandInitials } from "../brand-tile";
import { isoToLocalInput, localInputToIso } from "../campaign-builder/form-values";
import { shortLink } from "../campaign-preview";
import type { RosterEntry } from "../demo-insights";
import { springArrive } from "../motion";
import { previewOnly } from "../preview-toast";
import { useInBrowser, utcText } from "../time-text";

const NO_ANGLE = "__none";
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

/** Claims where an angle and a post time still matter. */
const ACTIVE: ReadonlySet<ClaimStatus> = new Set([
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
  "proof_submitted",
  "approved",
  "rejected",
  "paid",
]);

type RowAction = { label: string; icon: React.ReactNode; note: string; destructive?: boolean };

function rowActions(status: ClaimStatus, name: string): RowAction[] {
  switch (status) {
    case "requested":
      return [
        { label: "Accept request", icon: <Check />, note: `${name} gets a slot and a notification. It fails if the campaign is already full.` },
        { label: "Decline request", icon: <XCircle />, note: `${name}'s request is cancelled with your reason.`, destructive: true },
      ];
    case "draft_submitted":
      return [
        { label: "Approve draft", icon: <Check />, note: `${name} can post it inside their window.` },
        { label: "Ask for changes", icon: <MessageSquareWarning />, note: `${name} edits the draft using your comment and sends it again.` },
      ];
    case "proof_submitted":
      return [
        { label: "Approve proof", icon: <Check />, note: `An Unpaid earning is created for ${name}.` },
        { label: "Reject proof", icon: <XCircle />, note: `${name} can fix it and resubmit before the proof deadline.`, destructive: true },
      ];
    case "approved":
      return [{ label: "Mark paid", icon: <Wallet />, note: `Records the payment to ${name} with a reference (Milestone 7).` }];
    case "claimed":
    case "changes_requested":
    case "draft_approved":
    case "rejected":
      return [
        { label: "Extend deadline", icon: <Timer />, note: `Gives ${name} more time than the campaign's proof deadline.` },
        { label: "Cancel claim", icon: <XCircle />, note: `${name}'s slot opens again for someone else.`, destructive: true },
      ];
    case "expired":
    case "cancelled":
      return [{ label: "Reinstate", icon: <CircleCheck />, note: `${name} gets their claim back, if a slot is free.` }];
    default:
      return [];
  }
}

function Person({ row }: { row: RosterEntry }) {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span
        aria-hidden
        className="flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-3 font-mono text-[10px] font-medium text-muted-foreground"
      >
        {brandInitials(row.creator.name)}
      </span>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{row.creator.name}</p>
        <p className="truncate text-xs text-muted-foreground">
          {row.creator.handle} · {row.creator.tier}
        </p>
      </div>
    </div>
  );
}

function AngleSelect({
  row,
  angles,
  onChange,
  className,
}: {
  row: RosterEntry;
  angles: string[];
  onChange: (angle: string | undefined) => void;
  className?: string;
}) {
  if (!ACTIVE.has(row.status)) return <span className="text-[13px] text-subtle-foreground">Not needed</span>;
  if (angles.length === 0) return <span className="text-[13px] text-subtle-foreground">No angles on this campaign</span>;
  return (
    <Select value={row.angle ?? NO_ANGLE} onValueChange={(value) => onChange(value === NO_ANGLE ? undefined : value)}>
      <SelectTrigger
        aria-label={`Angle for ${row.creator.name}`}
        className={cn("h-9 rounded-lg px-2.5 text-[13px] sm:text-[13px] [&>span]:truncate", !row.angle && "text-subtle-foreground", className)}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="max-w-80">
        <SelectItem value={NO_ANGLE}>No angle yet</SelectItem>
        {angles.map((angle) => (
          <SelectItem key={angle} value={angle}>
            {angle}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function PostTimeInput({ row, onCommit }: { row: RosterEntry; onCommit: (iso: string) => void }) {
  const inBrowser = useInBrowser();
  const [draft, setDraft] = useState<string | null>(null);
  if (!ACTIVE.has(row.status)) return <span className="text-[13px] text-subtle-foreground">Not needed</span>;
  // Until the browser knows the viewer's time zone, show the UTC value, read-only.
  const value = draft ?? (row.postTime ? (inBrowser ? isoToLocalInput(row.postTime) : row.postTime.slice(0, 16)) : "");
  return (
    <div className="grid gap-0.5">
      <input
        type="datetime-local"
        aria-label={`Post time for ${row.creator.name}`}
        value={value}
        disabled={!inBrowser}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={() => {
          if (draft === null) return;
          const iso = localInputToIso(draft);
          setDraft(null);
          if (iso && iso !== row.postTime) onCommit(iso);
        }}
        className="h-9 w-full min-w-0 rounded-lg border border-input bg-surface px-2 text-[13px] tabular shadow-xs outline-none hover:border-border-strong focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 disabled:opacity-60 [color-scheme:inherit]"
      />
      <span className="truncate text-[11px] text-subtle-foreground">{row.postTime ? utcText(row.postTime) : "Not set yet"}</span>
    </div>
  );
}

function PostLink({ row }: { row: RosterEntry }) {
  if (!row.postUrl) return <span className="text-[13px] text-subtle-foreground">Not posted</span>;
  return (
    <a
      href={row.postUrl}
      target="_blank"
      rel="noreferrer"
      title={shortLink(row.postUrl)}
      className="inline-flex max-w-full min-w-0 items-center gap-1 text-[13px] whitespace-nowrap text-foreground underline decoration-border-strong underline-offset-4 hover:decoration-foreground"
    >
      View post
      <ExternalLink className="size-3 shrink-0 text-muted-foreground" aria-hidden />
      <span className="sr-only">by {row.creator.name}, {shortLink(row.postUrl)} (opens in a new tab)</span>
    </a>
  );
}

function PaidCell({ row }: { row: RosterEntry }) {
  if (row.paid) return <StatusBadge kind="earning" status="paid" />;
  if (row.status === "approved") return <StatusBadge kind="earning" status="unpaid" />;
  return <span className="text-[13px] text-subtle-foreground">Not yet</span>;
}

function RowMenu({ row }: { row: RosterEntry }) {
  const actions = rowActions(row.status, row.creator.name.split(" ")[0]);
  if (actions.length === 0) return null;
  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${row.creator.name}`} className="text-muted-foreground pointer-coarse:size-11">
          <Ellipsis />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="truncate text-xs font-normal text-muted-foreground">{row.creator.name}</DropdownMenuLabel>
        {actions.map((action, index) => (
          <div key={action.label}>
            {action.destructive && index > 0 ? <DropdownMenuSeparator /> : null}
            <DropdownMenuItem variant={action.destructive ? "destructive" : "default"} onSelect={() => previewOnly(action.note)}>
              {action.icon}
              {action.label}
            </DropdownMenuItem>
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/**
 * Everyone on the campaign: status, assigned angle, post time, post link,
 * views and payment. Pick rows to approve, assign an angle or mark paid in one
 * go. Changes are local to this preview until Milestone 6.
 */
export function Roster({ campaign, initialRows }: { campaign: DemoCampaign; initialRows: RosterEntry[] }) {
  const [rows, setRows] = useState(initialRows);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const allSelected = rows.length > 0 && selected.size === rows.length;
  const someSelected = selected.size > 0 && !allSelected;
  const selectedRows = useMemo(() => rows.filter((row) => selected.has(row.creatorId)), [rows, selected]);

  function toggle(id: string, on: boolean) {
    setSelected((current) => {
      const next = new Set(current);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function update(id: string, patch: Partial<RosterEntry>) {
    setRows((current) => current.map((row) => (row.creatorId === id ? { ...row, ...patch } : row)));
  }

  function setAngle(row: RosterEntry, angle: string | undefined) {
    update(row.creatorId, { angle });
    previewOnly(
      angle
        ? `${row.creator.name.split(" ")[0]} gets the angle "${angle}" and a notification.`
        : `${row.creator.name.split(" ")[0]} no longer has an angle.`,
    );
  }

  function setPostTime(row: RosterEntry, iso: string) {
    update(row.creatorId, { postTime: iso });
    previewOnly(`${row.creator.name.split(" ")[0]} posts at ${utcText(iso)} and gets a reminder before it.`);
  }

  function bulkAssign(angle: string) {
    const eligible = selectedRows.filter((row) => ACTIVE.has(row.status));
    setRows((current) => current.map((row) => (selected.has(row.creatorId) && ACTIVE.has(row.status) ? { ...row, angle } : row)));
    previewOnly(`${eligible.length} ${eligible.length === 1 ? "creator gets" : "creators get"} the angle "${angle}".`);
  }

  const approvable = selectedRows.filter((row) => ["requested", "draft_submitted", "proof_submitted"].includes(row.status)).length;
  const payable = selectedRows.filter((row) => row.status === "approved");
  const payTotal = totalsByCurrency(payable.map((row) => row.payout))
    .map((total) => formatMoney(total.amount, total.currency))
    .join(" and ");

  return (
    <div className="relative">
      {/* Desktop: table */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[62rem] table-fixed text-left">
          <caption className="sr-only">Creators on {campaign.title}</caption>
          <colgroup>
            <col className="w-12" />
            <col className="w-[13rem]" />
            <col className="w-[9.5rem]" />
            <col />
            <col className="w-[14rem]" />
            <col className="w-[7rem]" />
            <col className="w-[5rem]" />
            <col className="w-[6rem]" />
            <col className="w-12" />
          </colgroup>
          <thead>
            <tr className="border-b bg-surface-2/40 text-label text-subtle-foreground">
              <th scope="col" className="py-2.5 pl-4">
                <Checkbox
                  aria-label="Select everyone"
                  checked={allSelected ? true : someSelected ? "indeterminate" : false}
                  onCheckedChange={(value) => setSelected(value === true ? new Set(rows.map((row) => row.creatorId)) : new Set())}
                />
              </th>
              <th scope="col" className="px-3 py-2.5 font-medium">Creator</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Status</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Angle</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Post time</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Post</th>
              <th scope="col" className="px-3 py-2.5 text-right font-medium">Views</th>
              <th scope="col" className="px-3 py-2.5 font-medium">Paid</th>
              <th scope="col" className="py-2.5 pr-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isSelected = selected.has(row.creatorId);
              return (
                <tr
                  key={row.creatorId}
                  aria-selected={isSelected}
                  className={cn("border-b align-middle transition-colors last:border-b-0", isSelected ? "bg-surface-2/70" : "hover:bg-surface-2/40")}
                >
                  <td className="py-2.5 pl-4">
                    <Checkbox
                      aria-label={`Select ${row.creator.name}`}
                      checked={isSelected}
                      onCheckedChange={(value) => toggle(row.creatorId, value === true)}
                    />
                  </td>
                  <td className="px-3 py-2.5">
                    <Person row={row} />
                  </td>
                  <td className="px-3 py-2.5">
                    <StatusBadge kind="claim" status={row.status} />
                  </td>
                  <td className="px-3 py-2.5">
                    <AngleSelect row={row} angles={campaign.angles} onChange={(angle) => setAngle(row, angle)} />
                  </td>
                  <td className="px-3 py-2.5">
                    <PostTimeInput row={row} onCommit={(iso) => setPostTime(row, iso)} />
                  </td>
                  <td className="px-3 py-2.5">
                    <PostLink row={row} />
                  </td>
                  <td className="px-3 py-2.5 text-right text-[13px] tabular">
                    {row.views ? compact.format(row.views) : <span className="text-subtle-foreground">None yet</span>}
                  </td>
                  <td className="px-3 py-2.5">
                    <PaidCell row={row} />
                  </td>
                  <td className="py-2.5 pr-3 text-right">
                    <RowMenu row={row} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Phones: cards */}
      <ul className="grid gap-2 p-3 md:hidden">
        <li className="flex items-center gap-3 px-1 pb-1">
          <Checkbox
            id="roster-select-all"
            checked={allSelected ? true : someSelected ? "indeterminate" : false}
            onCheckedChange={(value) => setSelected(value === true ? new Set(rows.map((row) => row.creatorId)) : new Set())}
          />
          <label htmlFor="roster-select-all" className="text-[13px] text-muted-foreground">
            Select everyone
          </label>
        </li>
        {rows.map((row) => {
          const isSelected = selected.has(row.creatorId);
          return (
            <li key={row.creatorId} className={cn("rounded-lg border p-3", isSelected ? "border-border-strong bg-surface-2/60" : "bg-surface")}>
              <div className="flex items-start gap-3">
                <Checkbox
                  className="mt-1.5"
                  aria-label={`Select ${row.creator.name}`}
                  checked={isSelected}
                  onCheckedChange={(value) => toggle(row.creatorId, value === true)}
                />
                <div className="min-w-0 flex-1">
                  <Person row={row} />
                </div>
                <RowMenu row={row} />
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 pl-8">
                <StatusBadge kind="claim" status={row.status} />
                <PaidCell row={row} />
                {row.views ? <span className="text-xs text-muted-foreground tabular">{compact.format(row.views)} views</span> : null}
              </div>
              {ACTIVE.has(row.status) ? (
                <div className="mt-3 grid gap-2 pl-8">
                  <AngleSelect row={row} angles={campaign.angles} onChange={(angle) => setAngle(row, angle)} className="h-11" />
                  <PostTimeInput row={row} onCommit={(iso) => setPostTime(row, iso)} />
                  <PostLink row={row} />
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>

      <AnimatePresence>
        {selected.size > 0 ? (
          <motion.div
            key="bulk"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98, transition: { duration: 0.12 } }}
            transition={springArrive}
            className="pointer-events-none fixed inset-x-0 bottom-[calc(4.75rem+max(env(safe-area-inset-bottom),0.5rem))] z-40 flex justify-center px-3 lg:bottom-6 lg:pl-60"
          >
            <div
              role="toolbar"
              aria-label="Bulk actions"
              className="pointer-events-auto flex max-w-full items-center gap-1 overflow-x-auto rounded-2xl border border-border-strong bg-popover p-1.5 shadow-float [scrollbar-width:none]"
            >
              <span className="shrink-0 px-2.5 text-sm font-medium tabular">{selected.size} selected</span>
              <Button
                size="sm"
                className="shrink-0"
                onClick={() =>
                  previewOnly(
                    approvable
                      ? `Approves the ${approvable} waiting ${approvable === 1 ? "item" : "items"} in your selection. Approved proof creates Unpaid earnings.`
                      : "Nothing in your selection is waiting for approval.",
                  )
                }
              >
                <Check aria-hidden />
                Approve
              </Button>
              <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="secondary" className="shrink-0" disabled={campaign.angles.length === 0}>
                    <Shuffle aria-hidden />
                    Assign angle
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="center" side="top" className="w-72">
                  <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                    Give everyone selected the same angle
                  </DropdownMenuLabel>
                  {campaign.angles.map((angle) => (
                    <DropdownMenuItem key={angle} onSelect={() => bulkAssign(angle)}>
                      {angle}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
              <Button
                size="sm"
                variant="secondary"
                className="shrink-0"
                onClick={() =>
                  previewOnly(
                    payable.length
                      ? `Marks ${payable.length} approved ${payable.length === 1 ? "post" : "posts"} paid, ${payTotal} in total, with one reference.`
                      : "Only approved posts can be marked paid. Nothing selected is approved yet.",
                  )
                }
              >
                <Wallet aria-hidden />
                Mark paid
              </Button>
              <Button
                size="icon-sm"
                variant="ghost"
                className="shrink-0"
                aria-label="Clear selection"
                onClick={() => setSelected(new Set())}
              >
                <X />
              </Button>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

import type { DemoCampaign } from "@/lib/campaigns/demo";
import type { CampaignFormInput, PublishMode } from "@/lib/campaigns/schema";
import type { CampaignStatus } from "@/lib/statuses";

/**
 * Pure helpers behind the campaign builder: empty values, demo campaign to
 * form values, the step each field lives on, and local time to UTC.
 * No React in here, so unit tests can import it.
 */

/** Where the in-progress new campaign is kept on this device. */
export const DRAFT_STORAGE_KEY = "agi-campaign-draft";
/** Edits to an existing campaign are kept per campaign, so they never overwrite a new draft. */
export const editStorageKey = (campaignId: string) => `${DRAFT_STORAGE_KEY}:${campaignId}`;

export type BuilderMode = "new" | "duplicate" | "edit";

export function emptyCampaign(): CampaignFormInput {
  return {
    clientId: "",
    newClient: undefined,
    title: "",
    summary: "",
    brief: { about: "", whatToSay: "", keyMessage: "", dos: [], donts: [] },
    angles: [],
    deliverable: "original",
    platform: "x",
    links: { targetPostUrl: "", trackingUrl: "" },
    requiredTags: { mentions: [], hashtags: [], keywords: [] },
    assets: { brandKitUrl: "", files: [] },
    payout: { amount: "", currency: "USD" },
    tierPayouts: [],
    creatorPayouts: [],
    slots: 10,
    audience: { kind: "all", tiers: [], tags: [], creatorIds: [] },
    claimMode: "instant",
    draftRequired: false,
    paidLabelRequired: true,
    timing: { dropAt: "", postWindowStart: "", postWindowEnd: "", claimDeadline: "", proofDeadline: "" },
    publish: "now",
    internal: { notes: "", budgetAmount: "", budgetCurrency: "USD" },
  };
}

/** Once a campaign is out (live, full, paused, closed, completed) the publish choice no longer applies. */
export function hasDropped(status: CampaignStatus) {
  return status !== "draft" && status !== "scheduled";
}

function publishFor(status: CampaignStatus): PublishMode {
  if (status === "draft") return "draft";
  if (status === "scheduled") return "schedule";
  return "now";
}

/**
 * A demo campaign as builder values. Duplicating keeps the brief, rules and
 * money but clears the times, since a rerun happens on new dates.
 */
export function campaignToFormInput(campaign: DemoCampaign, mode: "edit" | "duplicate"): CampaignFormInput {
  const copy = JSON.parse(JSON.stringify(campaign)) as DemoCampaign;
  const values: CampaignFormInput = {
    clientId: copy.clientId,
    newClient: undefined,
    title: copy.title,
    summary: copy.summary,
    brief: copy.brief,
    angles: copy.angles,
    deliverable: copy.deliverable,
    platform: copy.platform,
    links: copy.links,
    requiredTags: copy.requiredTags,
    assets: copy.assets,
    payout: copy.payout,
    tierPayouts: copy.tierPayouts,
    creatorPayouts: copy.creatorPayouts,
    slots: copy.slots,
    audience: copy.audience,
    claimMode: copy.claimMode,
    draftRequired: copy.draftRequired,
    paidLabelRequired: copy.paidLabelRequired,
    timing: copy.timing,
    publish: publishFor(copy.status),
    internal: copy.internal,
  };
  if (mode === "duplicate") {
    values.timing = { dropAt: "", postWindowStart: "", postWindowEnd: "", claimDeadline: "", proofDeadline: "" };
    values.publish = "now";
  }
  return values;
}

export const STEPS = [
  {
    id: "basics",
    title: "Brand and basics",
    short: "Basics",
    description: "Who it's for, what it's called, and what creators will post.",
    fields: ["clientId", "newClient", "title", "summary", "platform", "deliverable", "links"],
  },
  {
    id: "brief",
    title: "Brief",
    short: "Brief",
    description: "What the company does, what to say, and the angles creators can take.",
    fields: ["brief", "angles"],
  },
  {
    id: "requirements",
    title: "Requirements",
    short: "Rules",
    description: "Tags that must appear, the paid label, drafts, and the files creators need.",
    fields: ["requiredTags", "paidLabelRequired", "draftRequired", "assets"],
  },
  {
    id: "payout",
    title: "Payout and audience",
    short: "Payout",
    description: "What each post pays, how many creators can join, and who can see it.",
    fields: ["payout", "slots", "tierPayouts", "creatorPayouts", "audience", "claimMode"],
  },
  {
    id: "timing",
    title: "Timing",
    short: "Timing",
    description: "When it drops, when people post, and when claiming and proof close.",
    fields: ["publish", "timing"],
  },
  {
    id: "review",
    title: "Internal and review",
    short: "Review",
    description: "Private notes and budget, then one last look before it goes out.",
    fields: ["internal"],
  },
] as const;

export type StepId = (typeof STEPS)[number]["id"];

/** The step a field path ("timing.dropAt", "brief.dos.2") lives on. */
export function stepForPath(path: string): number {
  const root = path.split(".")[0] ?? "";
  const index = STEPS.findIndex((step) => (step.fields as readonly string[]).includes(root));
  return index === -1 ? 0 : index;
}

/** Every leaf path in a react-hook-form errors object, e.g. ["timing.dropAt"]. */
export function errorPaths(errors: unknown, prefix = ""): string[] {
  if (!errors || typeof errors !== "object") return [];
  const record = errors as Record<string, unknown>;
  if (typeof record.message === "string" && "type" in record) return [prefix];
  return Object.entries(record).flatMap(([key, value]) => {
    if (key === "ref" || key === "root") {
      return key === "root" && value && typeof value === "object" ? [prefix] : [];
    }
    return errorPaths(value, prefix ? `${prefix}.${key}` : key);
  });
}

const pad = (value: number) => String(value).padStart(2, "0");

/** An ISO time as the value of a datetime-local input, in the viewer's own time zone. */
export function isoToLocalInput(iso: string): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** A datetime-local value (the viewer's time zone) as an ISO time in UTC: "2026-11-03T16:00:00Z". */
export function localInputToIso(local: string): string {
  if (!local) return "";
  const date = new Date(local);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().replace(/\.\d{3}Z$/, "Z");
}

const HOUR = 60 * 60 * 1000;

/**
 * A typical schedule around a post window start: a four hour window,
 * claiming closes two hours before it opens, proof is due the next day.
 */
export function suggestedTiming(postWindowStart: string) {
  const start = new Date(postWindowStart).getTime();
  const iso = (ms: number) => new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z");
  return {
    postWindowEnd: iso(start + 4 * HOUR),
    claimDeadline: iso(start - 2 * HOUR),
    proofDeadline: iso(start + 24 * HOUR),
  };
}

/**
 * What gets saved: drops answers that no longer apply, like a drop time on a
 * campaign that publishes now, or tier picks once the audience is "all".
 */
export function normalizeCampaign<T extends CampaignFormInput>(values: T): T {
  const { audience } = values;
  return {
    ...values,
    newClient: values.clientId === "new" ? values.newClient : undefined,
    links: {
      ...values.links,
      targetPostUrl: values.deliverable === "quote" || values.deliverable === "reply" ? values.links.targetPostUrl : "",
    },
    audience: {
      kind: audience.kind,
      tiers: audience.kind === "tiers" ? audience.tiers : [],
      tags: audience.kind === "tags" ? audience.tags : [],
      creatorIds: audience.kind === "creators" ? audience.creatorIds : [],
    },
    creatorPayouts:
      audience.kind === "creators" ? values.creatorPayouts.filter((row) => audience.creatorIds.includes(row.creatorId)) : [],
    timing: { ...values.timing, dropAt: values.publish === "schedule" ? values.timing.dropAt : "" },
  };
}

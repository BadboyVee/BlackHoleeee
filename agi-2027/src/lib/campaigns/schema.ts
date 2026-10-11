import { z } from "zod";

import { formatMoney, totalsByCurrency } from "@/lib/money";
import {
  AUDIENCE_KINDS,
  ASSET_KINDS,
  CLAIM_MODES,
  CURRENCIES,
  DELIVERABLES,
  NEEDS_TARGET_POST,
  PLATFORMS,
  TIERS,
} from "@/lib/campaigns/options";

/**
 * Everything the agency fills in to create or edit a campaign. The same schema
 * validates the form in the browser and, from Milestone 5, the server action
 * that saves it. Times are ISO strings in UTC; the form converts the person's
 * local time on the way in.
 */

const MAX_TEXT = 2000;

/** Exact money as a decimal string, never a float: "250", "0.5", "180000.00". */
export const amountSchema = z
  .string()
  .trim()
  .regex(/^\d{1,12}(\.\d{1,2})?$/, "Use a number like 250 or 99.50")
  .refine((value) => Number(value) > 0, "Must be more than 0");

/**
 * Links creators will open: http(s) only, on a real domain. Plain z.url()
 * would also accept javascript: and mailto: links.
 */
export const linkSchema = z.url({
  protocol: /^https?$/,
  hostname: z.regexes.domain,
  message: "Use a full link, starting with https://",
});
const optionalUrl = z.union([z.literal(""), linkSchema]);
const isoTime = z.iso.datetime({ offset: true, message: "Pick a date and time" });
const listItem = (max: number) => z.string().trim().min(1, "Can't be empty").max(max, `Keep it under ${max} characters`);

export const handleSchema = z
  .string()
  .trim()
  .regex(/^@?[A-Za-z0-9_]{1,15}$/, "An X handle is up to 15 letters, numbers or underscores")
  .transform((value) => (value.startsWith("@") ? value : `@${value}`));

export const hashtagSchema = z
  .string()
  .trim()
  .regex(/^#?[\p{L}\p{N}_]{1,60}$/u, "A hashtag is letters, numbers or underscores, no spaces")
  .transform((value) => (value.startsWith("#") ? value : `#${value}`));

export const newClientSchema = z.object({
  name: z.string().trim().min(2, "Add the brand's name").max(60),
  website: optionalUrl,
  xHandle: z.union([z.literal(""), handleSchema]),
});

export const PUBLISH_MODES = ["draft", "now", "schedule"] as const;
export type PublishMode = (typeof PUBLISH_MODES)[number];

export type CampaignSchemaOptions = {
  /**
   * The campaign is already out (live, full, paused, closed or completed).
   * The publish choice no longer applies, so the checks that only matter
   * before a drop (drop time, claiming still open) are skipped.
   */
  alreadyDropped?: boolean;
};

export function makeCampaignSchema(now: () => Date = () => new Date(), options: CampaignSchemaOptions = {}) {
  return z
    .object({
      clientId: z.string().min(1, "Pick a brand or add a new one"),
      newClient: newClientSchema.optional(),

      title: z.string().trim().min(4, "Give it a clear title").max(80, "Keep the title under 80 characters"),
      summary: z
        .string()
        .trim()
        .min(10, "One line on what creators will post")
        .max(140, "Keep the summary to one line (140 characters)"),

      brief: z.object({
        about: z.string().trim().min(20, "Tell creators what the company does").max(MAX_TEXT),
        whatToSay: z.string().trim().min(20, "Explain what the post should say").max(MAX_TEXT),
        keyMessage: z.string().trim().min(5, "Add the one message every post must land").max(280),
        dos: z.array(listItem(200)).max(12),
        donts: z.array(listItem(200)).max(12),
      }),
      angles: z.array(listItem(280)).max(20, "Up to 20 angles"),

      deliverable: z.enum(DELIVERABLES),
      platform: z.enum(PLATFORMS),
      links: z.object({
        targetPostUrl: optionalUrl,
        trackingUrl: optionalUrl,
      }),
      requiredTags: z.object({
        mentions: z.array(handleSchema).max(10),
        hashtags: z.array(hashtagSchema).max(10),
        keywords: z.array(listItem(60)).max(10),
      }),
      assets: z.object({
        brandKitUrl: optionalUrl,
        files: z
          .array(
            z.object({
              name: z.string().min(1).max(200),
              kind: z.enum(ASSET_KINDS),
              sizeBytes: z.number().int().nonnegative().max(200 * 1024 * 1024, "Files can be up to 200 MB"),
            }),
          )
          .max(20, "Up to 20 files"),
      }),

      payout: z.object({ amount: amountSchema, currency: z.enum(CURRENCIES) }),
      tierPayouts: z.array(z.object({ tier: z.enum(TIERS), amount: amountSchema })).max(TIERS.length),
      creatorPayouts: z.array(z.object({ creatorId: z.string().min(1), amount: amountSchema })).max(500),
      slots: z
        .number({ message: "How many creators can take part?" })
        .int("Slots must be a whole number")
        .min(1, "At least 1 slot")
        .max(1000, "Up to 1,000 slots"),

      audience: z.object({
        kind: z.enum(AUDIENCE_KINDS),
        tiers: z.array(z.enum(TIERS)),
        tags: z.array(z.string().min(1)),
        creatorIds: z.array(z.string().min(1)),
      }),
      claimMode: z.enum(CLAIM_MODES),
      draftRequired: z.boolean(),
      paidLabelRequired: z.boolean(),

      timing: z.object({
        dropAt: z.union([z.literal(""), isoTime]),
        postWindowStart: isoTime,
        postWindowEnd: isoTime,
        claimDeadline: isoTime,
        proofDeadline: isoTime,
      }),
      publish: z.enum(PUBLISH_MODES),

      internal: z.object({
        notes: z.string().trim().max(4000),
        budgetAmount: z.union([z.literal(""), amountSchema]),
        budgetCurrency: z.enum(CURRENCIES),
      }),
    })
    .superRefine((value, ctx) => {
      const issue = (path: (string | number)[], message: string) =>
        ctx.addIssue({ code: "custom", path, message });

      if (value.clientId === "new" && !value.newClient) {
        issue(["newClient", "name"], "Add the brand's name");
      }

      if (NEEDS_TARGET_POST.has(value.deliverable) && !value.links.targetPostUrl) {
        issue(["links", "targetPostUrl"], "Add the post creators should quote or reply to");
      }

      const { audience } = value;
      if (audience.kind === "tiers" && audience.tiers.length === 0) {
        issue(["audience", "tiers"], "Pick at least one tier");
      }
      if (audience.kind === "tags" && audience.tags.length === 0) {
        issue(["audience", "tags"], "Pick at least one tag");
      }
      if (audience.kind === "creators" && audience.creatorIds.length === 0) {
        issue(["audience", "creatorIds"], "Pick at least one creator");
      }

      const tiers = value.tierPayouts.map((row) => row.tier);
      if (new Set(tiers).size !== tiers.length) {
        issue(["tierPayouts"], "Each tier can have one custom amount");
      }

      const t = value.timing;
      const time = (iso: string) => new Date(iso).getTime();
      if (time(t.postWindowEnd) <= time(t.postWindowStart)) {
        issue(["timing", "postWindowEnd"], "The window has to end after it starts");
      }
      if (time(t.claimDeadline) > time(t.postWindowEnd)) {
        issue(["timing", "claimDeadline"], "Claiming has to close before the post window ends");
      }
      if (time(t.proofDeadline) < time(t.postWindowEnd)) {
        issue(["timing", "proofDeadline"], "The proof deadline can't be before the window ends");
      }
      if (options.alreadyDropped) return;
      if (value.publish === "schedule") {
        if (!t.dropAt) {
          issue(["timing", "dropAt"], "Pick when the campaign drops");
        } else {
          if (time(t.dropAt) <= now().getTime()) {
            issue(["timing", "dropAt"], "The drop time has to be in the future");
          }
          if (time(t.dropAt) >= time(t.claimDeadline)) {
            issue(["timing", "dropAt"], "Drop it before claiming closes");
          }
        }
      }
      if (value.publish !== "draft" && time(t.claimDeadline) <= now().getTime()) {
        issue(["timing", "claimDeadline"], "Claiming would already be closed. Pick a later time");
      }
    });
}

export const campaignSchema = makeCampaignSchema();
export type CampaignFormInput = z.input<typeof campaignSchema>;
export type CampaignFormValues = z.output<typeof campaignSchema>;

const isAmount = (value: string) => amountSchema.safeParse(value).success;

/** amount x times, exactly (summed in minor units by the money helpers). */
function multiplyAmount(amount: string, currency: string, times: number): string {
  return totalsByCurrency(Array.from({ length: times }, () => ({ amount, currency })))[0]?.amount ?? "0.00";
}

export type CampaignCommitment = {
  currency: string;
  /** Every slot at the base payout. */
  base: string;
  /** Every slot at the lowest and highest rate in play (custom tier or creator amounts). */
  low: string;
  high: string;
  /** Whether custom amounts make the total a range. */
  varies: boolean;
};

/**
 * What paying every slot costs, as exact decimal strings in the payout
 * currency. Returns null while the amount or slots aren't valid yet.
 */
export function campaignCommitment(value: {
  payout: { amount: string; currency: string };
  slots: number;
  tierPayouts: { amount: string }[];
  creatorPayouts: { amount: string }[];
}): CampaignCommitment | null {
  const { amount, currency } = value.payout;
  if (!isAmount(amount) || !Number.isInteger(value.slots) || value.slots < 1 || value.slots > 1000) return null;
  const rates = [amount, ...value.tierPayouts.map((row) => row.amount), ...value.creatorPayouts.map((row) => row.amount)]
    .map((rate) => rate.trim())
    .filter(isAmount);
  const lowest = rates.reduce((a, b) => (Number(b) < Number(a) ? b : a));
  const highest = rates.reduce((a, b) => (Number(b) > Number(a) ? b : a));
  return {
    currency,
    base: multiplyAmount(amount.trim(), currency, value.slots),
    low: multiplyAmount(lowest, currency, value.slots),
    high: multiplyAmount(highest, currency, value.slots),
    varies: Number(lowest) !== Number(highest),
  };
}

const X_POST_LINK = /^https:\/\/(www\.)?(x|twitter)\.com\/[A-Za-z0-9_]{1,15}\/status\/\d+/;

/**
 * Soft checks that never block saving but are worth a second look, like a
 * total payout above the budget.
 */
export function campaignWarnings(value: CampaignFormValues): string[] {
  const warnings: string[] = [];
  const commitment = campaignCommitment(value);
  const { budgetAmount, budgetCurrency } = value.internal;
  if (commitment && budgetAmount) {
    if (budgetCurrency !== commitment.currency) {
      warnings.push(
        `The budget is in ${budgetCurrency} and payouts are in ${commitment.currency}, so they can't be compared.`,
      );
    } else if (Number(commitment.base) > Number(budgetAmount)) {
      warnings.push(
        `Paying every slot costs ${formatMoney(commitment.base, commitment.currency)}, more than the ${formatMoney(budgetAmount, budgetCurrency)} budget.`,
      );
    } else if (Number(commitment.high) > Number(budgetAmount)) {
      warnings.push(
        `If every slot is paid the highest custom amount, it costs ${formatMoney(commitment.high, commitment.currency)}, more than the ${formatMoney(budgetAmount, budgetCurrency)} budget.`,
      );
    }
  }
  if (value.audience.kind === "creators" && value.slots > value.audience.creatorIds.length) {
    warnings.push("There are more slots than hand-picked creators, so some slots can't be filled.");
  }
  if (value.angles.length === 0) {
    warnings.push("No angles yet. Posts tend to sound alike without them.");
  }
  if (!value.paidLabelRequired) {
    warnings.push("The paid partnership label is off. X requires it on paid posts.");
  }
  const { postWindowStart, postWindowEnd } = value.timing;
  const windowMs = new Date(postWindowEnd).getTime() - new Date(postWindowStart).getTime();
  if (windowMs > 0 && windowMs < 60 * 60 * 1000) {
    warnings.push("The post window is under an hour. Creators in other time zones may miss it.");
  }
  if (
    value.platform === "x" &&
    NEEDS_TARGET_POST.has(value.deliverable) &&
    value.links.targetPostUrl &&
    !X_POST_LINK.test(value.links.targetPostUrl)
  ) {
    warnings.push("The post to quote or reply to doesn't look like an X post link (x.com/name/status/...).");
  }
  return warnings;
}

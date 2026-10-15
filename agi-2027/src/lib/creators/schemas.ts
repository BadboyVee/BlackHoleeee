import { z } from "zod";

import { normalizeWebsite, normalizeXHandle } from "@/lib/leads/booking";
import { CURRENCIES } from "@/lib/campaigns/options";

import { isCountryCode } from "./countries";
import {
  assetOnNetwork,
  CRYPTO_ASSETS,
  isWalletAddress,
  MAX_NICHES,
  NETWORK_VALUES,
  NICHE_VALUES,
  addressExample,
} from "./options";

/*
 * The creator forms: the application, the profile, payout details, invite
 * links and reviews. One schema per form, shared by the browser (instant
 * feedback) and the server actions (the check that counts). The database
 * checks the same limits again.
 */

export const LIMITS = { name: 80, why: 1000, whyMin: 20, bio: 300, note: 2000, label: 80 } as const;

/** Where each social link may point. */
const SOCIAL_DOMAINS = {
  tiktok: ["tiktok.com"],
  youtube: ["youtube.com", "youtu.be"],
  instagram: ["instagram.com"],
  linkedin: ["linkedin.com"],
} as const;

export type Social = keyof typeof SOCIAL_DOMAINS;

/** "tiktok.com/@amara" becomes "https://tiktok.com/@amara". Null when it isn't a link to that platform. */
export function normalizeSocialLink(input: string, social: Social): string | null {
  const link = normalizeWebsite(input);
  if (!link) return null;
  const host = new URL(link).hostname.replace(/^(www|m|mobile)\./, "");
  const allowed = SOCIAL_DOMAINS[social].some((domain) => host === domain || host.endsWith(`.${domain}`));
  return allowed ? link.replace(/^http:/, "https:") : null;
}

/** "18,400", "18 400", "18.4k" or "1.2M" become 18400 or 1200000. Null when it isn't a count. */
export function parseCount(input: string): number | null {
  const raw = input.trim().toLowerCase().replace(/[\s,_]/g, "");
  const match = /^(\d+(?:\.\d+)?)([km])?$/.exec(raw);
  if (!match) return null;
  const value = Number(match[1]) * (match[2] === "k" ? 1_000 : match[2] === "m" ? 1_000_000 : 1);
  return Number.isFinite(value) && value <= 2_000_000_000 ? Math.round(value) : null;
}

const displayName = z
  .string()
  .trim()
  .min(1, "Tell us the name you post under.")
  .max(LIMITS.name, `Keep it under ${LIMITS.name} characters.`);

const xHandle = z
  .string()
  .trim()
  .min(1, "Your X handle, like @yourname.")
  .transform((value, ctx) => {
    const handle = normalizeXHandle(value);
    if (!handle) {
      ctx.addIssue({ code: "custom", message: "Enter an X handle like @yourname." });
      return z.NEVER;
    }
    return handle;
  });

function socialLink(social: Social, example: string) {
  return z
    .string()
    .trim()
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      const link = normalizeSocialLink(value, social);
      if (!link) {
        ctx.addIssue({ code: "custom", message: `Paste your profile link, like ${example}.` });
        return z.NEVER;
      }
      return link;
    });
}

const socials = {
  tiktok: socialLink("tiktok", "tiktok.com/@you"),
  youtube: socialLink("youtube", "youtube.com/@you"),
  instagram: socialLink("instagram", "instagram.com/you"),
  linkedin: socialLink("linkedin", "linkedin.com/in/you"),
};

const niches = z
  .array(z.enum(NICHE_VALUES))
  .min(1, "Pick at least one.")
  .max(MAX_NICHES, `Pick up to ${MAX_NICHES}.`)
  .transform((values) => [...new Set(values)]);

function count(message: string) {
  return z
    .string()
    .trim()
    .min(1, message)
    .transform((value, ctx) => {
      const parsed = parseCount(value);
      if (parsed === null) {
        ctx.addIssue({ code: "custom", message: "A number, like 12,400 or 12.4k." });
        return z.NEVER;
      }
      return parsed;
    });
}

const country = z
  .string()
  .trim()
  .refine((value) => isCountryCode(value), "Pick your country.")
  .transform((value) => value.toUpperCase());

const postLink = z
  .string()
  .trim()
  .min(1, "Paste a link to the post.")
  .transform((value, ctx) => {
    const link = normalizeWebsite(value);
    if (!link) {
      ctx.addIssue({ code: "custom", message: "Paste the post's link, like x.com/you/status/123." });
      return z.NEVER;
    }
    return link.replace(/^http:/, "https:");
  });

export const applicationSchema = z.object({
  displayName,
  xHandle,
  ...socials,
  niches,
  followers: count("How many followers on X?"),
  avgViews: count("Roughly how many views a post gets."),
  country,
  bestPosts: z
    .tuple([postLink, postLink, postLink])
    .refine((links) => new Set(links).size === links.length, "Three different posts, please."),
  why: z
    .string()
    .trim()
    .min(LIMITS.whyMin, "A sentence or two, please.")
    .max(LIMITS.why, `Keep it under ${LIMITS.why} characters.`),
  referralCode: z
    .string()
    .trim()
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      const code = value.toLowerCase();
      if (!/^[a-f0-9]{8}$/.test(code)) {
        ctx.addIssue({ code: "custom", message: "Referral codes are 8 letters and numbers." });
        return z.NEVER;
      }
      return code;
    }),
});

export type ApplicationInput = z.input<typeof applicationSchema>;
export type Application = z.output<typeof applicationSchema>;

export const profileSchema = z
  .object({
    displayName,
    ...socials,
    niches,
    followers: count("How many followers on X?"),
    avgViews: count("Roughly how many views a post gets."),
    country,
    bio: z.string().trim().max(LIMITS.bio, `Keep it under ${LIMITS.bio} characters.`),
    ratePerPost: z
      .string()
      .trim()
      .optional()
      .transform((value, ctx) => {
        if (!value) return undefined;
        if (!/^\d{1,10}(\.\d{1,2})?$/.test(value)) {
          ctx.addIssue({ code: "custom", message: "A price like 150 or 150.50." });
          return z.NEVER;
        }
        return value;
      }),
    rateCurrency: z.enum(CURRENCIES).optional(),
  })
  .superRefine((values, ctx) => {
    if (values.ratePerPost && !values.rateCurrency) {
      ctx.addIssue({ code: "custom", path: ["rateCurrency"], message: "Pick a currency for your rate." });
    }
  })
  .transform((values) => (values.ratePerPost ? values : { ...values, rateCurrency: undefined }));

export type ProfileInput = z.input<typeof profileSchema>;
export type ProfileValues = z.output<typeof profileSchema>;

export const payoutSchema = z.discriminatedUnion("method", [
  z
    .object({
      method: z.literal("crypto"),
      asset: z.enum(CRYPTO_ASSETS, { error: "Pick USDC or USDT." }),
      network: z.enum(NETWORK_VALUES, { error: "Pick a network." }),
      wallet: z.string().trim().min(1, "Paste your wallet address."),
    })
    .superRefine((values, ctx) => {
      if (!assetOnNetwork(values.asset, values.network)) {
        ctx.addIssue({ code: "custom", path: ["network"], message: `We don't send ${values.asset} on that network. Pick another.` });
      }
      if (values.wallet && !isWalletAddress(values.network, values.wallet)) {
        ctx.addIssue({
          code: "custom",
          path: ["wallet"],
          message: `That doesn't look like an address on this network. It should be ${addressExample(values.network)}.`,
        });
      }
    }),
  z.object({
    method: z.literal("bank"),
    bankCountry: country,
    bankName: z.string().trim().min(1, "Which bank?").max(120, "Keep it under 120 characters."),
    accountName: z.string().trim().min(1, "The name on the account.").max(120, "Keep it under 120 characters."),
    accountNumber: z
      .string()
      .trim()
      .regex(/^[A-Za-z0-9 -]{4,40}$/, "Your account number or IBAN, letters and numbers only."),
    bankCode: z.string().trim().max(40, "Keep it under 40 characters.").optional(),
  }),
  z.object({
    method: z.literal("other"),
    otherDetails: z
      .string()
      .trim()
      .min(1, "Tell us how you'd like to be paid.")
      .max(500, "Keep it under 500 characters."),
  }),
]);

export type PayoutInput = z.input<typeof payoutSchema>;
export type PayoutValues = z.output<typeof payoutSchema>;

export const INVITE_EXPIRY = [
  { value: "never", label: "Never", days: null },
  { value: "1d", label: "In a day", days: 1 },
  { value: "7d", label: "In a week", days: 7 },
  { value: "30d", label: "In 30 days", days: 30 },
  { value: "90d", label: "In 90 days", days: 90 },
] as const;

export const inviteSchema = z.object({
  label: z.string().trim().max(LIMITS.label, `Keep it under ${LIMITS.label} characters.`),
  maxUses: z
    .string()
    .trim()
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      const uses = Number(value);
      if (!Number.isInteger(uses) || uses < 1 || uses > 10_000) {
        ctx.addIssue({ code: "custom", message: "A whole number from 1 to 10,000, or leave it empty." });
        return z.NEVER;
      }
      return uses;
    }),
  expiresIn: z.enum(INVITE_EXPIRY.map((option) => option.value) as ["never", ...string[]]),
});

export const reviewSchema = z.object({
  decision: z.enum(["approve", "reject"]),
  note: z.string().trim().max(LIMITS.note, `Keep it under ${LIMITS.note} characters.`),
});

/** What a creator form's server action returns (useActionState). */
export type CreatorFormState =
  | { status: "idle" }
  | { status: "saved"; message?: string }
  | { status: "error"; message: string; fieldErrors?: Record<string, string> };

/** The first message for each field, keyed by its path: "bestPosts.2" for the third post link. */
export function issuesByPath(issues: readonly { path: readonly PropertyKey[]; message: string }[]): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const issue of issues) {
    const key = issue.path.map(String).join(".");
    if (key && !errors[key]) errors[key] = issue.message;
  }
  return errors;
}

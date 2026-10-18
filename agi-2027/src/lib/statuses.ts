/**
 * Every status in the product, with the label and color people see.
 * Badges, filters, timelines and emails all read from here so a status
 * always looks and reads the same way everywhere.
 */

export const TONES = [
  "gray",
  "blue",
  "violet",
  "amber",
  "orange",
  "teal",
  "green",
  "red",
  "brand",
] as const;
export type Tone = (typeof TONES)[number];

export type StatusMeta = {
  label: string;
  tone: Tone;
  /** One line telling people what the status means for them. */
  description: string;
  /** Shows a pulsing dot (used for Live). */
  pulse?: boolean;
  /** Someone needs to act: the label takes the tone color, not just the dot. */
  attention?: boolean;
};

export const CLAIM_STATUSES = [
  "requested",
  "claimed",
  "draft_submitted",
  "changes_requested",
  "draft_approved",
  "proof_submitted",
  "approved",
  "rejected",
  "paid",
  "expired",
  "cancelled",
] as const;
export type ClaimStatus = (typeof CLAIM_STATUSES)[number];

export const claimStatusMeta: Record<ClaimStatus, StatusMeta> = {
  requested: {
    label: "Requested",
    tone: "violet",
    description: "Waiting for the agency to accept your request.",
  },
  claimed: {
    label: "Claimed",
    tone: "blue",
    description: "Your slot is reserved. Read the brief and get ready to post.",
  },
  draft_submitted: {
    label: "Draft submitted",
    tone: "violet",
    description: "The agency is reviewing your draft.",
  },
  changes_requested: {
    label: "Changes requested",
    tone: "amber",
    description: "Edit your draft using the agency's notes, then resubmit.",
    attention: true,
  },
  draft_approved: {
    label: "Draft approved",
    tone: "teal",
    description: "Post it inside your post window, then submit the link.",
  },
  proof_submitted: {
    label: "Proof submitted",
    tone: "violet",
    description: "The agency is checking your post.",
  },
  approved: {
    label: "Approved",
    tone: "green",
    description: "Your post is approved and your payment is on the way.",
  },
  rejected: {
    label: "Rejected",
    tone: "red",
    description: "Fix the post using the agency's note and resubmit before the deadline.",
    attention: true,
  },
  paid: {
    label: "Paid",
    tone: "brand",
    description: "Paid. The payment reference is in Earnings.",
  },
  expired: {
    label: "Expired",
    tone: "gray",
    description: "The proof deadline passed and the slot was released.",
  },
  cancelled: {
    label: "Cancelled",
    tone: "gray",
    description: "This claim was dropped or declined.",
  },
};

export const CAMPAIGN_STATUSES = [
  "draft",
  "scheduled",
  "live",
  "paused",
  "full",
  "closed",
  "completed",
] as const;
export type CampaignStatus = (typeof CAMPAIGN_STATUSES)[number];

export const campaignStatusMeta: Record<CampaignStatus, StatusMeta> = {
  draft: {
    label: "Draft",
    tone: "gray",
    description: "Only the agency can see this campaign.",
  },
  scheduled: {
    label: "Scheduled",
    tone: "blue",
    description: "Drops automatically at the scheduled time.",
  },
  live: {
    label: "Live",
    tone: "brand",
    description: "Open to creators now.",
    pulse: true,
  },
  paused: {
    label: "Paused",
    tone: "amber",
    description: "Closed to new claims for now.",
  },
  full: {
    label: "Full",
    tone: "orange",
    description: "Every slot is taken. A slot reopens if someone drops out.",
  },
  closed: {
    label: "Closed",
    tone: "gray",
    description: "No new claims. Claims in progress carry on.",
  },
  completed: {
    label: "Completed",
    tone: "green",
    description: "Every claim on this campaign is settled.",
  },
};

export const APPLICATION_STATUSES = ["submitted", "approved", "rejected"] as const;
export type ApplicationStatus = (typeof APPLICATION_STATUSES)[number];

export const applicationStatusMeta: Record<ApplicationStatus, StatusMeta> = {
  submitted: {
    label: "In review",
    tone: "amber",
    description: "Waiting for a decision.",
    attention: true,
  },
  approved: {
    label: "Approved",
    tone: "green",
    description: "You're in. Campaigns open to you show up in your portal.",
  },
  rejected: {
    label: "Not approved",
    tone: "gray",
    description: "Your application wasn't approved this time.",
  },
};

/** Where an invite link stands. Mirrors private.invite_state in the onboarding migration. */
export const INVITE_STATUSES = ["valid", "expired", "used_up", "revoked"] as const;
export type InviteStatus = (typeof INVITE_STATUSES)[number];

export const inviteStatusMeta: Record<InviteStatus, StatusMeta> = {
  valid: { label: "Active", tone: "green", description: "Anyone with the link can join." },
  expired: { label: "Expired", tone: "gray", description: "Past its expiry date." },
  used_up: { label: "Used up", tone: "gray", description: "Used as many times as it allows." },
  revoked: { label: "Switched off", tone: "red", description: "Switched off. It no longer works." },
};

export const LEAD_STATUSES = ["new", "contacted", "won", "lost"] as const;
export type LeadStatus = (typeof LEAD_STATUSES)[number];

export const leadStatusMeta: Record<LeadStatus, StatusMeta> = {
  new: { label: "New", tone: "blue", description: "Nobody has replied yet." },
  contacted: {
    label: "Contacted",
    tone: "violet",
    description: "We've reached out and the conversation is open.",
  },
  won: { label: "Won", tone: "green", description: "They booked a campaign." },
  lost: { label: "Lost", tone: "gray", description: "It didn't go ahead." },
};

export const EARNING_STATUSES = ["unpaid", "paid"] as const;
export type EarningStatus = (typeof EARNING_STATUSES)[number];

export const earningStatusMeta: Record<EarningStatus, StatusMeta> = {
  unpaid: {
    label: "Unpaid",
    tone: "amber",
    description: "Approved and waiting to be paid.",
  },
  paid: {
    label: "Paid",
    tone: "brand",
    description: "Paid, with a payment reference.",
  },
};

export const statusMeta = {
  claim: claimStatusMeta,
  campaign: campaignStatusMeta,
  application: applicationStatusMeta,
  invite: inviteStatusMeta,
  lead: leadStatusMeta,
  earning: earningStatusMeta,
} as const;

export type StatusKind = keyof typeof statusMeta;

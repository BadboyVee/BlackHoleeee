import type { CampaignCardData } from "@/components/campaign/campaign-card";
import { adjustSlotsTaken, isNewDrop, liveStatus, slotsLeft, type CreatorClaim } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";
import { deliverableMeta } from "@/lib/campaigns/options";
import type { ClaimStatus } from "@/lib/statuses";

/** Slots taken once this creator's own latest claim is counted. */
export function effectiveSlots(
  campaign: CreatorCampaign,
  seedStatus: ClaimStatus | undefined,
  claim: CreatorClaim | undefined,
) {
  const taken = adjustSlotsTaken(campaign.slotsTaken, seedStatus, claim?.status);
  const left = slotsLeft({ slots: campaign.slots, slotsTaken: taken });
  return { taken, left, status: liveStatus(campaign.status, left) };
}

/** A creator's campaign as card data. `now` is null until the browser knows the time. */
export function toCardData(
  campaign: CreatorCampaign,
  { claim, seedStatus, now }: { claim?: CreatorClaim; seedStatus?: ClaimStatus; now: number | null },
): CampaignCardData {
  const slots = effectiveSlots(campaign, seedStatus, claim);
  return {
    href: `/dashboard/campaigns/${campaign.id}`,
    brand: {
      name: campaign.brand.name,
      initials: campaign.brand.initials,
      color: campaign.brand.color,
      handle: campaign.brand.xHandle || undefined,
    },
    title: campaign.title,
    summary: campaign.summary,
    payout: campaign.payout,
    slots: { total: campaign.slots, taken: slots.taken },
    platform: campaign.platform,
    deliverable: deliverableMeta[campaign.deliverable].label,
    postWindow: { start: campaign.timing.postWindowStart, end: campaign.timing.postWindowEnd },
    status: slots.status,
    isNew: now !== null && !claim && isNewDrop(campaign.droppedAt, now),
    claimDeadline: campaign.timing.claimDeadline,
    claimMode: campaign.claimMode,
    claimStatus: claim?.status,
  };
}

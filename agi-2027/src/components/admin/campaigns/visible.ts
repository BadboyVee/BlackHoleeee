import { campaignById, demoCampaigns } from "@/lib/campaigns/demo";

/*
 * Which campaigns the admin can open: the samples on preview links, none on
 * the live site until real campaigns exist (Milestone 5). Pass
 * showSampleData().
 */

export function adminCampaign(id: string, showSamples: boolean) {
  return showSamples ? campaignById(id) : undefined;
}

/**
 * Ids to prerender. Cache Components needs at least one, so the live site
 * gets a placeholder that renders Not found.
 */
export function adminCampaignParams(showSamples: boolean): { id: string }[] {
  return showSamples ? demoCampaigns.map((campaign) => ({ id: campaign.id })) : [{ id: "none" }];
}

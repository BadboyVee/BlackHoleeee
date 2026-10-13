import { DEMO_BOARD_NOW, publicCampaigns } from "@/lib/campaigns/public";
import { dropImage, OgCampaignFan } from "@/lib/og/drop-image";

/* The /campaigns link preview: the open campaigns, fanned out in front of the word Claim. */

export const alt = "Open campaigns on AGI 2027: campaign cards in front of the word Claim.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  // The same fixed demo moment as the board itself (see the page for why).
  const campaigns = publicCampaigns(new Date(DEMO_BOARD_NOW));
  return dropImage({
    word: "Claim",
    kicker: "For creators",
    line: "Live campaigns from AI and tech startups.",
    cta: "Sign up to see payout",
    children: campaigns.length > 0 ? <OgCampaignFan campaigns={campaigns} /> : null,
  });
}

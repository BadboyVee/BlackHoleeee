import type { Metadata } from "next";

import { CampaignCard } from "@/components/campaign/campaign-card";
import { PageHeader } from "@/components/layout/page-header";
import { SampleBadge } from "@/components/sample-badge";
import { sampleCampaigns } from "@/lib/sample-data";

export const metadata: Metadata = { title: "Campaigns" };

export default function CreatorCampaignsPage() {
  return (
    <>
      <PageHeader
        eyebrow={<SampleBadge milestone={5} />}
        title="Campaigns"
        description="Every campaign open to you, with payout, slots left, post window and a countdown."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {sampleCampaigns.map((campaign) => (
          <CampaignCard key={campaign.title} campaign={campaign} />
        ))}
      </div>
    </>
  );
}

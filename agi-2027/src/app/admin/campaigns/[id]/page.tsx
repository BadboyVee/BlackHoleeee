import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CampaignDetail } from "@/components/admin/campaign-detail/campaign-detail";
import { CampaignDetailSkeleton } from "@/components/admin/campaign-detail/detail-skeleton";
import { campaignById, demoCampaigns } from "@/lib/campaigns/demo";

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return demoCampaigns.map((campaign) => ({ id: campaign.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return { title: campaignById(id)?.title ?? "Campaign" };
}

// The URL is read inside Suspense, so navigating here shows the frame at once.
// Every demo campaign is prerendered, so the skeleton only shows for unknown ids.
export default function CampaignPage({ params }: Props) {
  return (
    <Suspense fallback={<CampaignDetailSkeleton />}>
      <CampaignFromParams params={params} />
    </Suspense>
  );
}

async function CampaignFromParams({ params }: Props) {
  const { id } = await params;
  const campaign = campaignById(id);
  if (!campaign) notFound();
  return <CampaignDetail campaignId={campaign.id} />;
}

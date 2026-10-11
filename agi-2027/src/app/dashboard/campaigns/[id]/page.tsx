import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CampaignDetail } from "@/components/creator/detail/campaign-detail";
import { DetailSkeleton } from "@/components/creator/detail/skeleton";
import { creatorCampaignById, creatorCampaignIds } from "@/lib/campaigns/demo-creator";

type Params = Promise<{ id: string }>;

/** Every campaign the demo creator can open is built ahead of time. */
export function generateStaticParams() {
  return creatorCampaignIds().map((id) => ({ id }));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  const campaign = creatorCampaignById(id);
  return { title: campaign ? campaign.title : "Campaign not found" };
}

/* The id is URL data, so it's read inside Suspense: navigations show the skeleton at once. */
export default function CreatorCampaignPage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <CampaignForId params={params} />
    </Suspense>
  );
}

async function CampaignForId({ params }: { params: Params }) {
  const { id } = await params;
  // Unknown campaigns, drafts, scheduled drops and campaigns for other creators all look the same: not found.
  if (!creatorCampaignById(id)) notFound();
  return <CampaignDetail campaignId={id} />;
}

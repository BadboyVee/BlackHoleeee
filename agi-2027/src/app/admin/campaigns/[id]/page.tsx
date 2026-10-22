import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CampaignDetail } from "@/components/admin/campaign-detail/campaign-detail";
import { CampaignDetailSkeleton } from "@/components/admin/campaign-detail/detail-skeleton";
import { adminCampaign, adminCampaignParams } from "@/components/admin/campaigns/visible";
import { showSampleData } from "@/lib/sample-data";

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return adminCampaignParams(showSampleData());
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  return { title: adminCampaign(id, showSampleData())?.title ?? "Campaign" };
}

// The URL is read inside Suspense, so navigating here shows the frame at once.
// Every sample campaign is prerendered on preview links, so the skeleton only
// shows for unknown ids. The live site has no campaigns yet: every id is Not found.
export default function CampaignPage({ params }: Props) {
  return (
    <Suspense fallback={<CampaignDetailSkeleton />}>
      <CampaignFromParams params={params} />
    </Suspense>
  );
}

async function CampaignFromParams({ params }: Props) {
  const { id } = await params;
  const campaign = adminCampaign(id, showSampleData());
  if (!campaign) notFound();
  return <CampaignDetail campaignId={campaign.id} />;
}

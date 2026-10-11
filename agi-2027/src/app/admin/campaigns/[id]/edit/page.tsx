import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { BuilderSkeleton, CampaignBuilder } from "@/components/admin/campaign-builder/builder";
import { campaignById, demoCampaigns } from "@/lib/campaigns/demo";

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return demoCampaigns.map((campaign) => ({ id: campaign.id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const campaign = campaignById(id);
  return { title: campaign ? `Edit ${campaign.title}` : "Edit campaign" };
}

export default function EditCampaignPage({ params }: Props) {
  return (
    <Suspense fallback={<BuilderSkeleton />}>
      <EditFromParams params={params} />
    </Suspense>
  );
}

async function EditFromParams({ params }: Props) {
  const { id } = await params;
  const campaign = campaignById(id);
  if (!campaign) notFound();
  return <CampaignBuilder mode="edit" sourceId={campaign.id} />;
}

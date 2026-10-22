import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { BuilderSkeleton, CampaignBuilder } from "@/components/admin/campaign-builder/builder";
import { adminCampaign, adminCampaignParams } from "@/components/admin/campaigns/visible";
import { showSampleData } from "@/lib/sample-data";

type Props = { params: Promise<{ id: string }> };

export function generateStaticParams() {
  return adminCampaignParams(showSampleData());
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const campaign = adminCampaign(id, showSampleData());
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
  const campaign = adminCampaign(id, showSampleData());
  if (!campaign) notFound();
  return <CampaignBuilder mode="edit" sourceId={campaign.id} />;
}

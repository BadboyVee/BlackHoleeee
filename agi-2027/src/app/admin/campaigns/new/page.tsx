import { Suspense } from "react";
import type { Metadata } from "next";

import { BuilderSkeleton } from "@/components/admin/campaign-builder/builder";
import { NewCampaignFromUrl } from "@/components/admin/campaign-builder/new-campaign";

export const metadata: Metadata = { title: "New campaign" };

export default function NewCampaignPage() {
  return (
    <Suspense fallback={<BuilderSkeleton />}>
      <NewCampaignFromUrl />
    </Suspense>
  );
}

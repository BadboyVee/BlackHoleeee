import { Suspense } from "react";
import type { Metadata } from "next";
import { Megaphone } from "lucide-react";

import { BuilderSkeleton } from "@/components/admin/campaign-builder/builder";
import { NewCampaignFromUrl } from "@/components/admin/campaign-builder/new-campaign";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ComingSoon } from "@/components/layout/coming-soon";
import { showSampleData } from "@/lib/sample-data";

export const metadata: Metadata = { title: "New campaign" };

/**
 * The builder only saves on preview links for now, so the live site says so
 * instead of offering a form that goes nowhere.
 */
export default function NewCampaignPage() {
  if (!showSampleData()) {
    return (
      <>
        <AdminPageHeader title="New campaign" />
        <ComingSoon
          icon={Megaphone}
          title="The campaign builder is coming soon"
          description="You'll create campaigns and send them to your creators from here."
          milestone={5}
        />
      </>
    );
  }
  return (
    <Suspense fallback={<BuilderSkeleton />}>
      <NewCampaignFromUrl />
    </Suspense>
  );
}

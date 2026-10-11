import { Suspense } from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { BookOpen, Plus } from "lucide-react";

import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { CampaignList, CampaignListFromUrl } from "@/components/admin/campaigns/campaign-list";
import { campaignsByStatus, reviewCount } from "@/components/admin/demo-insights";
import { Button } from "@/components/ui/button";
import { demoCampaigns } from "@/lib/campaigns/demo";

export const metadata: Metadata = { title: "Campaigns" };

export default function AdminCampaignsPage() {
  const live = campaignsByStatus("live").length;
  return (
    <>
      <AdminPageHeader
        title="Campaigns"
        description={`${demoCampaigns.length} campaigns, ${live} live right now, ${reviewCount()} items waiting for review.`}
        actions={
          <>
            <Button asChild variant="ghost" className="text-muted-foreground">
              <Link href="/admin/campaigns/new?guide=1">
                <BookOpen aria-hidden />
                How listing works
              </Link>
            </Button>
            <Button asChild className="hidden md:inline-flex">
              <Link href="/admin/campaigns/new">
                <Plus aria-hidden />
                New campaign
              </Link>
            </Button>
          </>
        }
      />
      <Suspense fallback={<CampaignList />}>
        <CampaignListFromUrl />
      </Suspense>
    </>
  );
}

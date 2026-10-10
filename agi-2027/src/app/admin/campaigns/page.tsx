import type { Metadata } from "next";
import { Megaphone } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Campaigns" };

export default function AdminCampaignsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Run"
        title="Campaigns"
        description="Create, schedule, drop and track every campaign and every creator on it."
      />
      <ComingSoon
        icon={Megaphone}
        title="No campaigns yet"
        description="Create a campaign, publish it now or schedule the drop, and watch every claim move in real time."
        milestone={5}
      />
    </>
  );
}

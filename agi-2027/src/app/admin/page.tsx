import type { Metadata } from "next";
import { LayoutDashboard } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Overview" };

export default function AdminOverviewPage() {
  return (
    <>
      <PageHeader
        eyebrow="Today"
        title="Overview"
        description="Live campaigns, posts due today, the review queue, money owed and new leads at a glance."
      />
      <ComingSoon
        icon={LayoutDashboard}
        title="Your agency at a glance"
        description="Live campaigns, posts due today, items waiting for review, unpaid and paid totals, new applications and leads, plus a chart of posts and payouts."
        milestone={9}
      />
    </>
  );
}

import type { Metadata } from "next";
import { History } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Activity log" };

export default function ActivityLogPage() {
  return (
    <>
      <PageHeader
        eyebrow="System"
        title="Activity log"
        description="Who did what and when, for claims, approvals, payouts and settings."
      />
      <ComingSoon
        icon={History}
        title="No activity yet"
        description="Every claim, approval, payout and settings change is recorded here with who did it and when."
        milestone={9}
      />
    </>
  );
}

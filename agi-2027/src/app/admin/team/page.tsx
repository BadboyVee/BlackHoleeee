import type { Metadata } from "next";
import { ShieldCheck } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Team" };

export default function TeamPage() {
  return (
    <>
      <PageHeader
        eyebrow="People"
        title="Team"
        description="Invite agency staff and set their role."
      />
      <ComingSoon
        icon={ShieldCheck}
        title="Just you for now"
        description="Invite team members by email. They can run campaigns and reviews, but never see payouts, team or settings."
        milestone={9}
      />
    </>
  );
}

import type { Metadata } from "next";
import { Layers } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "My campaigns" };

export default function MyCampaignsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Your claims"
        title="My campaigns"
        description="Everything you've claimed, sorted into Active, Submitted, Approved, Paid and Past."
      />
      <ComingSoon
        icon={Layers}
        title="You haven't claimed anything yet"
        description="Claim a campaign and it moves through these tabs as you draft, post, submit proof and get paid."
        milestone={6}
      />
    </>
  );
}

import type { Metadata } from "next";
import { Users } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Creators" };

export default function CreatorsDirectoryPage() {
  return (
    <>
      <PageHeader
        eyebrow="People"
        title="Creators"
        description="Search and filter every creator by tier, niche and audience."
      />
      <ComingSoon
        icon={Users}
        title="No creators yet"
        description="Approved creators appear here with their history, approval rate, on-time rate, earnings and your private notes."
        milestone={9}
      />
    </>
  );
}

import type { Metadata } from "next";
import { UserPlus } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Leads" };

export default function LeadsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Growth"
        title="Leads"
        description="Book a campaign requests, from New to Won."
      />
      <ComingSoon
        icon={UserPlus}
        title="No leads yet"
        description="Every Book a campaign form lands here and in your inbox. Move each from New to Contacted, Won or Lost."
        milestone={9}
      />
    </>
  );
}

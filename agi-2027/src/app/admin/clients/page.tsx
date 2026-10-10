import type { Metadata } from "next";
import { Building2 } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Clients" };

export default function ClientsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Growth"
        title="Clients"
        description="The startups you work with, their contacts, campaigns and total spend."
      />
      <ComingSoon
        icon={Building2}
        title="No clients yet"
        description="Clients are added when you create their first campaign, or here directly."
        milestone={9}
      />
    </>
  );
}

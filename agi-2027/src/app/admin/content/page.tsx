import type { Metadata } from "next";
import { PanelsTopLeft } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Site content" };

export default function SiteContentPage() {
  return (
    <>
      <AdminPageHeader
        title="Site content"
        description="Edit the homepage stats, brand logos, featured posts and FAQ."
      />
      <ComingSoon
        icon={PanelsTopLeft}
        title="Homepage content"
        description="Change the numbers, logos, featured posts and FAQ on the public site without touching code."
        milestone={9}
      />
    </>
  );
}

import type { Metadata } from "next";
import { Inbox } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Applications" };

export default function ApplicationsPage() {
  return (
    <>
      <AdminPageHeader
        title="Applications"
        description="New creator applications waiting for a decision."
      />
      <ComingSoon
        icon={Inbox}
        title="No applications yet"
        description="When someone applies, their answers land here for you to approve or reject, with notes."
        milestone={4}
      />
    </>
  );
}

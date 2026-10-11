import type { Metadata } from "next";
import { Bell } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Notifications" };

export default function AdminNotificationsPage() {
  return (
    <>
      <AdminPageHeader
        title="Notifications"
        description="New applications, leads, drafts and proofs waiting on the agency."
      />
      <ComingSoon
        icon={Bell}
        title="You're all caught up"
        description="New applications, leads and submissions show up here live, and in your email."
        milestone={8}
      />
    </>
  );
}

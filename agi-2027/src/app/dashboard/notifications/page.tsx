import type { Metadata } from "next";
import { Bell } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Notifications" };

export default function CreatorNotificationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Inbox"
        title="Notifications"
        description="Everything that happened on your account, newest first."
      />
      <ComingSoon
        icon={Bell}
        title="You're all caught up"
        description="Drops, approvals, change requests and payments show up here live."
        milestone={8}
      />
    </>
  );
}

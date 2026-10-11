import type { Metadata } from "next";
import { Settings } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <>
      <AdminPageHeader
        title="Settings"
        description="Agency name, Telegram bot, currencies, default campaign rules and email sender."
      />
      <ComingSoon
        icon={Settings}
        title="Agency settings"
        description="Connect the Telegram bot, pick the creators group, and set currencies, defaults and the email sender."
        milestone={8}
      />
    </>
  );
}

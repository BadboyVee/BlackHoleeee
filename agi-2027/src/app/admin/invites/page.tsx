import type { Metadata } from "next";
import { Ticket } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Invites" };

export default function InvitesPage() {
  return (
    <>
      <AdminPageHeader
        title="Invites"
        description="Invite links that approve new creators straight away."
      />
      <ComingSoon
        icon={Ticket}
        title="No invite links yet"
        description="Create a link with an optional use limit and expiry to move your current creators in fast."
        milestone={4}
      />
    </>
  );
}

import type { Metadata } from "next";
import { Ticket } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Invites" };

export default function InvitesPage() {
  return (
    <>
      <PageHeader
        eyebrow="People"
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

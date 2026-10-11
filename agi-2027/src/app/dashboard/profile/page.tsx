import type { Metadata } from "next";
import { UserRound } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Profile" };

export default function ProfilePage() {
  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Your profile, payout details and personal referral link."
      />
      <ComingSoon
        icon={UserRound}
        title="Your profile lives here"
        description="Photo, handles, niches, audience numbers, payout method and your referral link."
        milestone={4}
      />
    </>
  );
}

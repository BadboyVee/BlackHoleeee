import type { Metadata } from "next";
import { Wallet } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Earnings" };

export default function EarningsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Money"
        title="Earnings"
        description="Total earned, unpaid and paid, per currency, with a reference for every payment."
      />
      <ComingSoon
        icon={Wallet}
        title="No earnings yet"
        description="Once the agency approves your proof, the earning appears here as Unpaid, then Paid with its reference."
        milestone={7}
      />
    </>
  );
}

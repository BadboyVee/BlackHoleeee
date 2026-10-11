import type { Metadata } from "next";
import { Banknote } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { AdminPageHeader } from "@/components/admin/admin-page-header";

export const metadata: Metadata = { title: "Payouts" };

export default function PayoutsPage() {
  return (
    <>
      <AdminPageHeader
        title="Payouts"
        description="Unpaid totals by creator, with their payout details. Mark payments as paid."
      />
      <ComingSoon
        icon={Banknote}
        title="Nothing to pay yet"
        description="Approved posts create unpaid earnings here, grouped by creator and currency, ready to mark paid with a reference."
        milestone={7}
      />
    </>
  );
}

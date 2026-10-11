import type { Metadata } from "next";
import { Megaphone } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";
import { MarketingMain } from "@/components/layout/marketing-main";

export const metadata: Metadata = {
  title: "Open campaigns",
  description: "Live campaigns from AI and tech startups. Sign up to see the payout and claim a slot.",
};

export default function OpenCampaignsPage() {
  return (
    <MarketingMain>
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
        <PageHeader title="Open campaigns" description="Live campaigns from AI and tech startups. Sign up to see the payout and claim a slot." />
        <ComingSoon
          icon={Megaphone}
          title="The campaign board is on its way"
          description="Live campaigns will show here with brand, platform and post date. Payouts unlock when you sign up."
          milestone={2}
        />
      </div>
    </MarketingMain>
  );
}

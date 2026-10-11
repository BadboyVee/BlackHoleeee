import type { Metadata } from "next";
import { Lock } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";
import { MarketingMain } from "@/components/layout/marketing-main";

export const metadata: Metadata = {
  title: "Privacy",
  description: "How AGI 2027 collects, uses and protects your data.",
};

export default function PrivacyPage() {
  return (
    <MarketingMain>
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
        <PageHeader title="Privacy" description="How AGI 2027 collects, uses and protects your data." />
        <ComingSoon
          icon={Lock}
          title="The privacy policy is being written"
          description="How we collect, use and protect data will be published here."
          milestone={2}
        />
      </div>
    </MarketingMain>
  );
}

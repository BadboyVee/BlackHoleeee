import type { Metadata } from "next";
import { Sparkles } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";
import { MarketingMain } from "@/components/layout/marketing-main";

export const metadata: Metadata = {
  title: "Apply as a creator",
  description: "Get paid to post about the most interesting launches in AI and tech.",
};

export default function ApplyPage() {
  return (
    <MarketingMain>
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
        <PageHeader title="Apply as a creator" description="Get paid to post about the most interesting launches in AI and tech." />
        <ComingSoon
          icon={Sparkles}
          title="Applications open soon"
          description="Create an account, tell us about your audience, and we'll review your application."
          milestone={4}
        />
      </div>
    </MarketingMain>
  );
}

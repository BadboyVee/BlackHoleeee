import type { Metadata } from "next";
import { Sparkles } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Home" };

export default function CreatorHomePage() {
  return (
    <>
      <PageHeader
        eyebrow="Today"
        title="Home"
        description="New drops, your active claims with countdowns, earnings, and anything that needs you."
      />
      <ComingSoon
        icon={Sparkles}
        title="Nothing needs you yet"
        description="When the agency drops a campaign, it shows up here first, along with your active claims and what's due next."
        milestone={5}
      />
    </>
  );
}

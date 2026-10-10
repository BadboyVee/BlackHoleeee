import type { Metadata } from "next";
import { Megaphone } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Campaigns" };

export default function CreatorCampaignsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Open now"
        title="Campaigns"
        description="Every campaign open to you, with payout, slots left, post window and a countdown."
      />
      <ComingSoon
        icon={Megaphone}
        title="No open campaigns yet"
        description="New drops land here the moment they go live. You'll also get an email and a Telegram alert."
        milestone={5}
      />
    </>
  );
}

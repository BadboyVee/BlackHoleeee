import type { Metadata } from "next";

import { CampaignBoard } from "@/components/creator/board";

export const metadata: Metadata = { title: "Campaigns" };

export default function CreatorCampaignsPage() {
  return <CampaignBoard />;
}

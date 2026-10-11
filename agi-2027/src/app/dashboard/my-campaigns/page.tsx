import type { Metadata } from "next";

import { MyCampaigns } from "@/components/creator/my-campaigns";

export const metadata: Metadata = { title: "My campaigns" };

export default function MyCampaignsPage() {
  return <MyCampaigns />;
}

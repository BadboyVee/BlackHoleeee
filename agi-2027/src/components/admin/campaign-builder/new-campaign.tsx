"use client";

import { useSearchParams } from "next/navigation";

import { CampaignBuilder } from "./builder";

/** /admin/campaigns/new, or ?from=<id> to duplicate a campaign, ?guide=1 to open the guide. */
export function NewCampaignFromUrl() {
  const params = useSearchParams();
  const from = params.get("from") ?? undefined;
  const guide = params.get("guide") === "1";
  return <CampaignBuilder key={from ?? "new"} mode={from ? "duplicate" : "new"} sourceId={from} openGuide={guide} />;
}

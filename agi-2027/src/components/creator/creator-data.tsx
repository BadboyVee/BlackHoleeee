"use client";

import { createContext, useContext, useMemo } from "react";

import type { CreatorCampaign, CreatorDemo } from "@/lib/campaigns/demo-creator";

/*
 * The creator's demo world, handed down once from the layout (a Server
 * Component) so pages and the shell read the same campaigns and seed claims.
 * Real data replaces this in Milestones 5 and 6.
 */

const CreatorDemoContext = createContext<CreatorDemo | null>(null);

function CreatorDemoProvider({ value, children }: { value: CreatorDemo; children: React.ReactNode }) {
  return <CreatorDemoContext.Provider value={value}>{children}</CreatorDemoContext.Provider>;
}

function useCreatorDemo(): CreatorDemo {
  const value = useContext(CreatorDemoContext);
  if (!value) throw new Error("useCreatorDemo must be used inside the creator shell");
  return value;
}

/** Looks campaigns up by id. */
function useCampaignLookup(): (id: string) => CreatorCampaign | undefined {
  const { campaigns } = useCreatorDemo();
  const byId = useMemo(() => new Map(campaigns.map((campaign) => [campaign.id, campaign])), [campaigns]);
  return (id: string) => byId.get(id);
}

export { CreatorDemoProvider, useCampaignLookup, useCreatorDemo };

import Link from "next/link";
import { ArrowRight, Bell, Check } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { CampaignCard } from "@/components/campaign/campaign-card";
import { Button } from "@/components/ui/button";
import { creatorPerks } from "@/lib/marketing-content";
import { sampleCampaigns } from "@/lib/sample-data";
import { Section, SectionHeader } from "./section";

/** A phone showing the creator portal, built from the real components. */
function PortalPhone() {
  return (
    <div className="relative mx-auto w-full max-w-[22rem]">
      <div className="rounded-[2.9rem] bg-[#161513] p-2.5 shadow-float ring-1 ring-black/40">
        <div className="relative overflow-hidden rounded-[2.35rem] bg-background">
          <div className="flex items-center justify-between px-6 pt-3.5 text-[11px] font-semibold">
            <span>9:41</span>
            <span className="h-5 w-20 rounded-full bg-[#161513]" />
            <span className="tabular">100%</span>
          </div>
          <div className="flex items-center justify-between px-5 pt-4 pb-3">
            <LogoMark className="size-4" />
            <span className="relative">
              <Bell className="size-4 text-muted-foreground" />
              <span className="absolute -top-0.5 -right-0.5 size-1.5 rounded-full bg-(--tone-brand)" />
            </span>
          </div>
          <div className="px-4 pb-5">
            <p className="px-1 pb-3 text-lg font-semibold tracking-[-0.03em]">Campaigns</p>
            <div className="pointer-events-none">
              <CampaignCard campaign={sampleCampaigns[0]} />
            </div>
          </div>
        </div>
      </div>
      <div className="absolute -bottom-5 left-1/2 flex -translate-x-1/2 items-center gap-2.5 rounded-full border border-white/10 bg-[#161513] py-2 pr-4 pl-2.5 text-[13px] whitespace-nowrap text-white shadow-float">
        <span className="flex size-6 items-center justify-center rounded-full bg-[#c6ff3a] text-[#0a0d02]">
          <Check className="size-3.5" strokeWidth={3} />
        </span>
        Paid <span className="font-mono font-medium">250 USDC</span>
        <span className="text-white/50">· ref 0x9f…3a</span>
      </div>
    </div>
  );
}

function ForCreators() {
  return (
    <Section id="creators">
      <div className="grid items-center gap-20 lg:grid-cols-2 lg:gap-16">
        <div>
          <SectionHeader kicker="For creators" title="Get paid to post about launches you'd talk about *anyway*." />
          <ul className="mt-9 space-y-4">
            {creatorPerks.map((perk) => (
              <li key={perk} className="flex gap-3 text-[15px] text-pretty text-muted-foreground">
                <Check className="mt-1 size-4 shrink-0 text-brand-text" aria-hidden />
                {perk}
              </li>
            ))}
          </ul>
          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link href="/apply">Apply as a creator</Link>
            </Button>
            <Button asChild size="lg" variant="ghost">
              <Link href="/campaigns">
                See open campaigns
                <ArrowRight />
              </Link>
            </Button>
          </div>
        </div>
        <PortalPhone />
      </div>
    </Section>
  );
}

export { ForCreators };

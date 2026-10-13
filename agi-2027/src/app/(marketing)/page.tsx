import type { Metadata } from "next";

import { MarketingMain } from "@/components/layout/marketing-main";
import { HomeHero } from "@/components/marketing/home-hero";
import { BrandsMarquee } from "@/components/marketing/sections/brands";
import { FaqSection } from "@/components/marketing/sections/faq";
import { FinalCtaSection } from "@/components/marketing/sections/final-cta";
import { ForCreatorsSection } from "@/components/marketing/sections/for-creators";
import { HowItWorksSection } from "@/components/marketing/sections/how-it-works";
import { ProofSection } from "@/components/marketing/sections/proof";
import { ServicesSection } from "@/components/marketing/sections/services";
import { StatsSection } from "@/components/marketing/sections/stats";

// The title and description come from the root layout.
export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <MarketingMain overlay>
      <HomeHero />
      <StatsSection />
      <BrandsMarquee />
      <ProofSection />
      <ServicesSection />
      <HowItWorksSection />
      <ForCreatorsSection />
      <FaqSection />
      <FinalCtaSection />
    </MarketingMain>
  );
}

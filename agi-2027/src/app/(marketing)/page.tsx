import { FeaturedPosts } from "@/components/marketing/featured-posts";
import { Faq } from "@/components/marketing/faq";
import { FinalCta } from "@/components/marketing/final-cta";
import { ForCreators } from "@/components/marketing/for-creators";
import { Hero } from "@/components/marketing/hero";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { Services } from "@/components/marketing/services";
import { StatsStrip } from "@/components/marketing/stats-strip";

export default function HomePage() {
  return (
    <>
      <Hero />
      <StatsStrip />
      <FeaturedPosts />
      <Services />
      <HowItWorks />
      <ForCreators />
      <Faq />
      <FinalCta />
    </>
  );
}

import { SiteFooter } from "@/components/layout/site-footer";
import { SkipLink } from "@/components/layout/skip-link";

/** Public pages. Each page renders its own header: the home page floats it over the hero. */
export default function MarketingLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink />
      {children}
      <SiteFooter />
    </div>
  );
}

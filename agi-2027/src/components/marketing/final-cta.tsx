import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site";
import { Accented } from "./section";

function FinalCta() {
  return (
    <section className="relative isolate overflow-hidden border-t bg-wall">
      <div className="mx-auto max-w-3xl px-5 py-28 text-center sm:px-8 sm:py-40">
        <div className="mx-auto flex size-20 items-center justify-center rounded-[22px] bg-[radial-gradient(130%_130%_at_18%_12%,#f6f4f0,#dedad3_55%,#cfcac2)] shadow-[inset_2px_2px_2px_rgb(255_255_255/0.8),inset_-3px_-5px_10px_rgb(70_55_40/0.16),var(--shadow-float)] dark:bg-[radial-gradient(130%_130%_at_18%_12%,#3a3733,#2a2825_55%,#211f1d)] dark:shadow-[inset_2px_2px_2px_rgb(255_255_255/0.08),inset_-3px_-5px_10px_rgb(0_0_0/0.4),var(--shadow-float)]">
          <LogoMark className="size-9 text-[#d9d5cd] [filter:drop-shadow(-1px_-1px_0_rgb(255_255_255/0.9))_drop-shadow(1.5px_2px_2px_rgb(70_55_40/0.38))] dark:text-[#2c2a27] dark:[filter:drop-shadow(-1px_-1px_0_rgb(255_255_255/0.08))_drop-shadow(1.5px_2px_2px_rgb(0_0_0/0.6))]" />
        </div>
        <h2 className="mt-10 text-h1 text-balance">
          <Accented text="Make your next launch *impossible* to miss." />
        </h2>
        <p className="mx-auto mt-6 max-w-lg text-lead text-pretty text-muted-foreground">
          Tell us what you&apos;re launching and when. We&apos;ll come back with a plan and the
          creators to run it.
        </p>
        <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
          <Button asChild size="lg">
            <Link href="/book">
              Book a campaign
              <ArrowRight />
            </Link>
          </Button>
          {siteConfig.contactEmail ? (
            <Button asChild size="lg" variant="secondary">
              <a href={`mailto:${siteConfig.contactEmail}`}>{siteConfig.contactEmail}</a>
            </Button>
          ) : (
            <Button asChild size="lg" variant="secondary">
              <Link href="/apply">Apply as a creator</Link>
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}

export { FinalCta };

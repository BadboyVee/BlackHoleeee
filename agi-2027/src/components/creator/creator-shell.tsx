import { SkipLink } from "@/components/layout/skip-link";
import { buildCreatorWorld } from "@/lib/campaigns/demo-creator";
import { showSampleData } from "@/lib/sample-data";

import { CreatorDemoProvider } from "./creator-data";
import { CreatorMotion, CreatorRail, CreatorTabBar } from "./creator-nav";
import { CreatorTopBar } from "./creator-top-bar";

/**
 * The creator portal frame. It's built like a phone app, on purpose different
 * from the owner's dense admin: a floating tab bar on phones, a slim rail and
 * one centered column on desktop, big tap targets and springy motion.
 *
 * The demo data is trimmed to what a creator may see here, on the server, and
 * handed to the client once. The live site hands over an empty world instead:
 * no sample campaigns, claims or earnings.
 */
function CreatorShell({ children }: { children: React.ReactNode }) {
  const demo = buildCreatorWorld(showSampleData());

  return (
    <CreatorDemoProvider value={demo}>
      <CreatorMotion>
        <div className="relative isolate min-h-dvh">
          <SkipLink />
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[34rem] bg-spotlight opacity-90"
          />
          <CreatorRail />
          <div className="relative lg:pl-[5.75rem]">
            <CreatorTopBar />
            <main
              id="main"
              tabIndex={-1}
              className="relative mx-auto w-full max-w-[68rem] px-4 pt-3 pb-36 outline-none sm:px-6 sm:pt-5 lg:px-10 lg:pb-20"
            >
              {children}
            </main>
          </div>
          <CreatorTabBar />
        </div>
      </CreatorMotion>
    </CreatorDemoProvider>
  );
}

export { CreatorShell };

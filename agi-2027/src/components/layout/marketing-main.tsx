import { ViewTransition } from "react";

import { SiteHeader } from "./site-header";

/**
 * Header plus the main landmark for public pages. The home page floats the
 * header over its hero. Moving between public pages, the old page fades out
 * quickly and the new one rises in (the header stays put).
 */
function MarketingMain({ children, overlay = false }: { children: React.ReactNode; overlay?: boolean }) {
  return (
    <>
      <SiteHeader overlay={overlay} />
      <ViewTransition enter="page-in" exit="page-out" default="none">
        <main id="main" tabIndex={-1} className="flex-1 outline-none">
          {children}
        </main>
      </ViewTransition>
    </>
  );
}

export { MarketingMain };

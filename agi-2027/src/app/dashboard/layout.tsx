import { Suspense } from "react";
import type { Metadata } from "next";

import { AccountScope } from "@/components/auth/account-scope";
import { CreatorShell } from "@/components/creator/creator-shell";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

/**
 * The account lookup starts here and streams into the greeting and the
 * account menu. The boundary is what lets it read the session cookie;
 * AccountScope never suspends, so the shell and pages still prerender.
 */
export default function CreatorLayout({ children }: LayoutProps<"/dashboard">) {
  return (
    <Suspense>
      <AccountScope>
        <CreatorShell>{children}</CreatorShell>
      </AccountScope>
    </Suspense>
  );
}

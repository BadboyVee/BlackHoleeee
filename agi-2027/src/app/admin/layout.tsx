import { Suspense } from "react";
import type { Metadata } from "next";

import { AdminShell } from "@/components/admin/admin-shell";
import { AccountScope } from "@/components/auth/account-scope";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

/**
 * The account lookup starts here and streams into the account menu. The
 * boundary is what lets it read the session cookie; AccountScope never
 * suspends, so the shell and pages still prerender.
 */
export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return (
    <Suspense>
      <AccountScope>
        <AdminShell>{children}</AdminShell>
      </AccountScope>
    </Suspense>
  );
}

import type { Metadata } from "next";

import { AppShell } from "@/components/layout/app-shell";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function CreatorLayout({ children }: LayoutProps<"/dashboard">) {
  return <AppShell area="creator">{children}</AppShell>;
}

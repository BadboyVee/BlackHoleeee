import type { Metadata } from "next";

import { CreatorShell } from "@/components/creator/creator-shell";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

export default function CreatorLayout({ children }: LayoutProps<"/dashboard">) {
  return <CreatorShell>{children}</CreatorShell>;
}

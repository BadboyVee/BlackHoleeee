import type { Metadata } from "next";

import { CreatorHome } from "@/components/creator/home";

export const metadata: Metadata = { title: "Home" };

export default function CreatorHomePage() {
  return <CreatorHome />;
}

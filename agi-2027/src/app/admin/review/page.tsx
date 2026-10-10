import type { Metadata } from "next";
import { ClipboardCheck } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = { title: "Review queue" };

export default function ReviewQueuePage() {
  return (
    <>
      <PageHeader
        eyebrow="Run"
        title="Review queue"
        description="Claim requests, drafts and proof links waiting on you, oldest first."
      />
      <ComingSoon
        icon={ClipboardCheck}
        title="Nothing waiting for review"
        description="Requests, drafts and proof links land here with free automatic checks. Approve each in one tap, or in bulk."
        milestone={6}
      />
    </>
  );
}

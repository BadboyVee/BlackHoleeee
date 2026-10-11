import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export default function CampaignNotFound() {
  return (
    <EmptyState
      icon={SearchX}
      title="We couldn't find that campaign"
      description="It may have been deleted, or the link is mistyped. Every campaign is listed on the Campaigns page."
      action={
        <Button asChild variant="secondary">
          <Link href="/admin/campaigns">
            <ArrowLeft aria-hidden />
            All campaigns
          </Link>
        </Button>
      }
    />
  );
}

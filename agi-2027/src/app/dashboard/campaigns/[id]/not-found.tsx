import Link from "next/link";
import { ArrowLeft, SearchX } from "lucide-react";

import { displayType, panel } from "@/components/creator/ui";
import { cn } from "@/lib/utils";

export default function CampaignNotFound() {
  return (
    <div className={cn(panel, "mt-4 flex flex-col items-center px-6 py-16 text-center sm:mt-8")}>
      <span className="mb-5 flex size-14 items-center justify-center rounded-2xl bg-surface-2 text-muted-foreground">
        <SearchX className="size-6" />
      </span>
      <h1 className={cn(displayType, "text-[2rem] leading-none")}>Campaign not found</h1>
      <p className="mt-3 max-w-sm text-[15px] text-pretty text-muted-foreground">
        It may have ended, not dropped yet, or be meant for other creators. Everything open to you is on the board.
      </p>
      <Link
        href="/dashboard/campaigns"
        className="pressable mt-7 inline-flex h-12 items-center gap-2 rounded-full bg-foreground px-6 text-[15px] font-semibold text-background"
      >
        <ArrowLeft className="size-4" />
        Back to campaigns
      </Link>
    </div>
  );
}

import type { Metadata } from "next";
import { CalendarClock } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = {
  title: "Book a campaign",
  description: "Tell us what you're launching and when. We'll come back with a plan and the right creators.",
};

export default function BookPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
      <PageHeader title="Book a campaign" description="Tell us what you're launching and when. We'll come back with a plan and the right creators." />
      <ComingSoon
        icon={CalendarClock}
        title="The booking form is on its way"
        description="Name, company, what you're launching, launch date and budget. It lands straight in the agency's inbox."
        milestone={2}
      />
    </div>
  );
}

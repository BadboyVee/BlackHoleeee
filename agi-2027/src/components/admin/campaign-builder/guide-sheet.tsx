"use client";

import { BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";

const sections: { title: string; points: string[] }[] = [
  {
    title: "Six short steps",
    points: [
      "Brand and basics: who it's for, the title, the one-line summary, the platform and the kind of post.",
      "Brief: what the company does, what to say, the key message, do's and don'ts, and angles.",
      "Requirements: mentions, hashtags and keywords, the paid label, drafts, and files.",
      "Payout and audience: the amount, the slots, who can see it, and how claiming works.",
      "Timing: publish now, schedule a drop, or keep a draft. Then the post window and deadlines.",
      "Review: private notes and budget, then one last look before it goes out.",
    ],
  },
  {
    title: "When it drops",
    points: [
      "It appears on the board for the creators in the audience. Nobody else ever sees it.",
      "They get an in-app notification and an email, and the Telegram bot posts it in the group.",
      "Every time shows in each creator's own time zone, with UTC beside it.",
    ],
  },
  {
    title: "Claiming",
    points: [
      "Instant: the first creators to tap Claim get the slots.",
      "Apply: creators send a note and you accept each one from the review queue.",
      "A campaign can never be overfilled, even when everyone taps at once.",
    ],
  },
  {
    title: "Drafts, proof and pay",
    points: [
      "With drafts on, you approve each post before it goes out.",
      "After posting, creators paste the link. Free checks look at the link, the handle and the post.",
      "Approving proof creates an Unpaid earning. Mark it paid from Payouts with a reference.",
    ],
  },
  {
    title: "After it's live",
    points: [
      "Edit it any time. Creators on it are told the brief changed, and their payout stays as claimed.",
      "Duplicate it to rerun it with new dates. Pause, close or mark it complete from the menu.",
    ],
  },
];

/** A short, in-app version of docs/listing-a-campaign.md. */
export function GuideSheet({ defaultOpen = false }: { defaultOpen?: boolean }) {
  return (
    <Sheet defaultOpen={defaultOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="text-muted-foreground">
          <BookOpen aria-hidden />
          <span className="sm:hidden">Guide</span>
          <span className="hidden sm:inline">How listing works</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[92%] max-w-md gap-0 overflow-y-auto">
        <SheetHeader className="border-b px-6 pt-6 pb-4">
          <SheetTitle className="text-lg">How listing a campaign works</SheetTitle>
          <SheetDescription>The short version. The full guide lives in docs/listing-a-campaign.md.</SheetDescription>
        </SheetHeader>
        <div className="grid gap-6 px-6 py-5">
          {sections.map((section, index) => (
            <section key={section.title} aria-labelledby={`guide-${index}`}>
              <h3 id={`guide-${index}`} className="flex items-center gap-2 text-sm font-semibold">
                <span className="flex size-5 items-center justify-center rounded-full bg-foreground font-mono text-[10px] text-background">
                  {index + 1}
                </span>
                {section.title}
              </h3>
              <ul className="mt-2 grid gap-1.5 pl-7 text-[13px] leading-relaxed text-muted-foreground">
                {section.points.map((point) => (
                  <li key={point} className="list-disc">
                    {point}
                  </li>
                ))}
              </ul>
            </section>
          ))}
          <p className="rounded-lg border border-dashed px-4 py-3 text-xs leading-relaxed text-muted-foreground">
            Today this is a preview with demo data. Saving and drops arrive in Milestone 5, claiming and review in 6, payouts
            in 7, and notifications in 8.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}

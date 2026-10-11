import { buildIcs } from "@/lib/campaigns/claims";
import type { CreatorCampaign } from "@/lib/campaigns/demo-creator";

/**
 * Saves a calendar file with two events: the post window (with a reminder
 * 30 minutes before) and the proof deadline. Built in the browser, nothing
 * is uploaded.
 */
export function downloadCampaignCalendar(campaign: CreatorCampaign, { angle }: { angle?: string } = {}) {
  const link = `${window.location.origin}/dashboard/campaigns/${campaign.id}`;
  const tags = [
    ...campaign.requiredTags.mentions,
    ...campaign.requiredTags.hashtags,
    ...campaign.requiredTags.keywords,
  ].join(" ");
  const proofDue = new Date(campaign.timing.proofDeadline);
  const ics = buildIcs(
    [
      {
        uid: `${campaign.id}-window@agi2027`,
        title: `Post for ${campaign.brand.name}: ${campaign.title}`,
        start: campaign.timing.postWindowStart,
        end: campaign.timing.postWindowEnd,
        description: [
          angle ? `Your angle: ${angle}` : null,
          `Key message: ${campaign.brief.keyMessage}`,
          tags ? `Include: ${tags}` : null,
          campaign.paidLabelRequired ? "Turn on the paid partnership label." : null,
          `Brief and proof: ${link}`,
        ]
          .filter(Boolean)
          .join("\n"),
        url: link,
        alarmMinutesBefore: 30,
      },
      {
        uid: `${campaign.id}-proof@agi2027`,
        title: `Proof due: ${campaign.title}`,
        start: new Date(proofDue.getTime() - 15 * 60_000).toISOString(),
        end: proofDue.toISOString(),
        description: `Paste your post link before this time, or the slot reopens.\n${link}`,
        url: link,
        alarmMinutesBefore: 120,
      },
    ],
    new Date(),
  );

  const href = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = `agi-2027-${campaign.id}.ics`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(href), 2000);
}

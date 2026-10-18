import { countryName } from "@/lib/creators/countries";
import { nicheLabel } from "@/lib/creators/options";
import { formatUtcDate, formatUtcTime } from "@/lib/time";

import { singleLine } from "./html";
import { renderEmail, siteBase, type EmailRow, type RenderedEmail } from "./layout";

/*
 * Emails about creator onboarding, built from database rows when the outbox
 * sends them. Pure functions, so they're easy to test.
 */

const NUMBER = new Intl.NumberFormat("en-US");

function firstName(name: string): string {
  return singleLine(name).split(" ")[0] || "there";
}

function contactLine(contactEmail: string, lead: string): string {
  const email = contactEmail.trim();
  return email ? `${lead} Email us at ${email}.` : lead;
}

/** The application, as the owner's "new application" email needs it. */
export type ApplicationEmailData = {
  createdAt: string;
  bestPosts: string[] | null;
  why: string | null;
  applicant: {
    displayName: string;
    email: string | null;
    xHandle: string | null;
    followers: number | null;
    avgViews: number | null;
    niches: string[];
    country: string | null;
    tiktokUrl: string | null;
    youtubeUrl: string | null;
    instagramUrl: string | null;
    linkedinUrl: string | null;
  };
  referrer: { displayName: string; xHandle: string | null } | null;
};

/** To the owner: someone applied. Replies go to the applicant. */
export function applicationReceivedEmail(data: ApplicationEmailData, { siteUrl }: { siteUrl: string }): RenderedEmail {
  const person = data.applicant;
  const name = singleLine(person.displayName) || "Someone";
  const handle = person.xHandle ? `@${person.xHandle}` : "";
  const rows: EmailRow[] = [{ label: "Name", text: name }];
  if (person.xHandle) rows.push({ label: "X", text: handle, href: `https://x.com/${person.xHandle}` });
  if (person.followers !== null) rows.push({ label: "Followers", text: NUMBER.format(person.followers) });
  if (person.avgViews !== null) rows.push({ label: "Views per post", text: NUMBER.format(person.avgViews) });
  if (person.niches.length) rows.push({ label: "Niches", text: person.niches.map(nicheLabel).join(", ") });
  if (person.country) rows.push({ label: "Country", text: countryName(person.country) });
  (data.bestPosts ?? []).forEach((link, index) => rows.push({ label: index === 0 ? "Best posts" : "", text: link, href: link }));
  if (data.why) rows.push({ label: "Why", text: data.why.trim() });
  for (const [label, link] of [
    ["TikTok", person.tiktokUrl],
    ["YouTube", person.youtubeUrl],
    ["Instagram", person.instagramUrl],
    ["LinkedIn", person.linkedinUrl],
  ] as const) {
    if (link) rows.push({ label, text: link, href: link });
  }
  if (data.referrer) {
    const referrer = singleLine(data.referrer.displayName);
    rows.push({ label: "Referred by", text: data.referrer.xHandle ? `${referrer} (@${data.referrer.xHandle})` : referrer });
  }
  if (person.email) rows.push({ label: "Email", text: person.email, href: `mailto:${person.email}` });
  rows.push({ label: "Applied", text: `${formatUtcDate(data.createdAt)}, ${formatUtcTime(data.createdAt)}` });

  const subject = handle ? `New creator application: ${name} (${handle})` : `New creator application: ${name}`;
  return renderEmail({
    subject,
    heading: subject,
    paragraphs: [`${name} wants to join as a creator. Approve or reject them in the admin.`],
    rows,
    button: { label: "Review applications", href: `${siteBase(siteUrl)}/admin/applications` },
  });
}

/** To the creator: they're in, through an approval or an invite link. */
export function applicationApprovedEmail(
  data: { displayName: string; referralCode: string | null; viaInvite: boolean },
  { siteUrl, contactEmail }: { siteUrl: string; contactEmail: string },
): RenderedEmail {
  const base = siteBase(siteUrl);
  const paragraphs = [
    data.viaInvite
      ? `Hi ${firstName(data.displayName)}, welcome to AGI 2027. Your invite worked, so you're in straight away.`
      : `Hi ${firstName(data.displayName)}, good news: your application is approved. Welcome to AGI 2027.`,
    "Campaigns open to you show up on your dashboard. Claim a slot, post in your own words, and get paid per post.",
    "One thing first: add your payout details on your profile, so we can pay you.",
  ];
  if (data.referralCode) {
    paragraphs.push(`Know a creator who'd fit? Send them your link: ${base}/apply?ref=${data.referralCode}`);
  }
  return renderEmail({
    subject: "You're in: welcome to AGI 2027",
    heading: "You're in",
    paragraphs,
    button: { label: "Open your dashboard", href: `${base}/dashboard` },
    footer: [contactLine(contactEmail, "Questions?")],
  });
}

/** To the applicant: not this time. Kind, and no reasons (the notes are private). */
export function applicationRejectedEmail(
  data: { displayName: string },
  { contactEmail }: { contactEmail: string },
): RenderedEmail {
  return renderEmail({
    subject: "About your AGI 2027 application",
    heading: "About your application",
    paragraphs: [
      `Hi ${firstName(data.displayName)}, thanks for applying to AGI 2027.`,
      "We can't offer you a place right now. We keep the group small so every creator gets real work, and we read every application with care.",
      "If that changes, we'll get in touch.",
    ],
    footer: [contactLine(contactEmail, "Questions?")],
  });
}

/** To the creator: their payout details changed. If it wasn't them, they can stop it in time. */
export function payoutDetailsChangedEmail(
  data: { displayName: string; summary: string },
  { siteUrl, contactEmail }: { siteUrl: string; contactEmail: string },
): RenderedEmail {
  return renderEmail({
    subject: "Your payout details changed",
    heading: "Your payout details changed",
    paragraphs: [
      `Hi ${firstName(data.displayName)}, the payout details on your AGI 2027 account were just changed.`,
      "If that was you, there's nothing to do.",
      contactLine(
        contactEmail,
        "If it wasn't you, tell us straight away and we'll hold your payments until it's sorted.",
      ),
    ],
    rows: [{ label: "Now paying to", text: singleLine(data.summary) }],
    button: { label: "Check your payout details", href: `${siteBase(siteUrl)}/dashboard/profile` },
  });
}

import { budgetLabel } from "@/lib/leads/booking";
import { formatUtcDate, formatUtcTime } from "@/lib/time";

import { escapeHtml, escapeMultiline, singleLine } from "./html";

/** The columns of public.leads the owner's email needs. */
export type LeadEmailData = {
  id: string;
  name: string;
  email: string;
  company: string;
  website: string | null;
  x_handle: string | null;
  launching: string;
  /** YYYY-MM-DD, or null when they haven't picked one. */
  launch_date: string | null;
  budget: string;
  message: string | null;
  source: string;
  created_at: string;
};

export type RenderedEmail = { subject: string; html: string; text: string };

const SOURCE_LABELS: Record<string, string> = {
  book_page: "Book a campaign page",
  home_cta: "Home page form",
};

/** "12 Nov 2026" for a YYYY-MM-DD date. Calendar dates have no time zone, so read them as UTC. */
function launchDateLabel(value: string): string {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? formatUtcDate(`${value}T00:00:00Z`) : value;
}

type Row = {
  label: string;
  /** Plain text for the text version. */
  text: string;
  /** Ready-made HTML (already escaped) for the HTML version. */
  html: string;
};

function textRow(label: string, value: string): Row {
  return { label, text: value, html: escapeMultiline(value) };
}

function linkRow(label: string, value: string, href: string): Row {
  return {
    label,
    text: value,
    html: `<a href="${escapeHtml(href)}" style="color:inherit">${escapeHtml(value)}</a>`,
  };
}

/**
 * The owner's "new lead" email. Every value from the form is escaped, empty
 * optional fields are left out, and replies go to the lead (set by the sender).
 */
export function leadReceivedEmail(lead: LeadEmailData, { siteUrl }: { siteUrl: string }): RenderedEmail {
  const company = singleLine(lead.company) || "a new company";
  const subject = `New campaign inquiry: ${company}`;
  const leadsUrl = `${siteUrl.replace(/\/+$/, "")}/admin/leads`;

  const rows: Row[] = [
    textRow("Name", singleLine(lead.name)),
    linkRow("Email", lead.email, `mailto:${lead.email}`),
    textRow("Company", singleLine(lead.company)),
  ];
  if (lead.website && /^https?:\/\//i.test(lead.website)) {
    rows.push(linkRow("Website", lead.website, lead.website));
  } else if (lead.website) {
    rows.push(textRow("Website", lead.website));
  }
  if (lead.x_handle) {
    const handle = lead.x_handle.replace(/^@/, "");
    rows.push(
      /^[A-Za-z0-9_]{1,15}$/.test(handle)
        ? linkRow("X", `@${handle}`, `https://x.com/${handle}`)
        : textRow("X", lead.x_handle),
    );
  }
  rows.push(textRow("Launching", lead.launching.trim()));
  if (lead.launch_date) rows.push(textRow("Launch date", launchDateLabel(lead.launch_date)));
  rows.push(textRow("Budget", budgetLabel(lead.budget)));
  if (lead.message?.trim()) rows.push(textRow("Message", lead.message.trim()));
  rows.push(textRow("Sent from", SOURCE_LABELS[lead.source] ?? lead.source));
  rows.push(textRow("Received", `${formatUtcDate(lead.created_at)}, ${formatUtcTime(lead.created_at)}`));

  const intro = `${singleLine(lead.name)} from ${company} wants to book a campaign. Hit reply to answer them.`;
  const footer = "Every lead will also show in Admin > Leads once sign-in is live.";

  const text = [
    intro,
    "",
    ...rows.map((row) => `${row.label}: ${row.text}`),
    "",
    footer,
    leadsUrl,
  ].join("\n");

  const tableRows = rows
    .map(
      (row) =>
        `<tr><td style="padding:8px 16px 8px 0;vertical-align:top;color:#666666;white-space:nowrap">${escapeHtml(row.label)}</td>` +
        `<td style="padding:8px 0;vertical-align:top;color:#111111">${row.html}</td></tr>`,
    )
    .join("");

  // Email clients ignore stylesheets and CSS variables, so the few colors here are inline and neutral.
  const html = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(subject)}</title></head>
<body style="margin:0;padding:24px;background:#ffffff;color:#111111;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5">
<div style="max-width:560px;margin:0 auto">
<p style="margin:0 0 4px;font-size:13px;color:#666666">AGI 2027</p>
<h1 style="margin:0 0 16px;font-size:20px;line-height:1.3">${escapeHtml(subject)}</h1>
<p style="margin:0 0 16px">${escapeHtml(intro)}</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5;margin:0 0 16px">${tableRows}</table>
<p style="margin:0;font-size:13px;color:#666666">${escapeHtml(footer)} <a href="${escapeHtml(leadsUrl)}" style="color:inherit">Open Leads</a></p>
</div>
</body>
</html>`;

  return { subject, html, text };
}

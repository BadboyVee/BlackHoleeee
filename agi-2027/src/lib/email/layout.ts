import { escapeHtml, escapeMultiline } from "./html";

/*
 * The plain, branded frame every email shares: a small "AGI 2027" line, a
 * heading, paragraphs, an optional table of details, one button and a quiet
 * footer. Email clients ignore stylesheets and CSS variables, so the few
 * colors are inline and neutral. Every value passed in is escaped here.
 */

export type EmailRow = { label: string; text: string; href?: string };

export type EmailContent = {
  subject: string;
  heading: string;
  paragraphs: string[];
  rows?: EmailRow[];
  button?: { label: string; href: string };
  /** Small print under the button. */
  footer?: string[];
};

export type RenderedEmail = { subject: string; html: string; text: string };

const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";

function rowHtml(row: EmailRow): string {
  const value = row.href
    ? `<a href="${escapeHtml(row.href)}" style="color:inherit">${escapeHtml(row.text)}</a>`
    : escapeMultiline(row.text);
  return (
    `<tr><td style="padding:8px 16px 8px 0;vertical-align:top;color:#666666;white-space:nowrap">${escapeHtml(row.label)}</td>` +
    `<td style="padding:8px 0;vertical-align:top;color:#111111">${value}</td></tr>`
  );
}

export function renderEmail(content: EmailContent): RenderedEmail {
  const rows = content.rows ?? [];
  const html = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(content.subject)}</title></head>
<body style="margin:0;padding:24px;background:#ffffff;color:#111111;font-family:${FONT};font-size:15px;line-height:1.5">
<div style="max-width:560px;margin:0 auto">
<p style="margin:0 0 4px;font-size:13px;color:#666666">AGI 2027</p>
<h1 style="margin:0 0 16px;font-size:20px;line-height:1.3">${escapeHtml(content.heading)}</h1>
${content.paragraphs.map((paragraph) => `<p style="margin:0 0 16px">${escapeMultiline(paragraph)}</p>`).join("\n")}
${rows.length ? `<table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5;margin:0 0 20px">${rows.map(rowHtml).join("")}</table>` : ""}
${content.button ? `<p style="margin:0 0 24px"><a href="${escapeHtml(content.button.href)}" style="display:inline-block;padding:12px 22px;border-radius:999px;background:#111111;color:#ffffff;font-weight:600;text-decoration:none">${escapeHtml(content.button.label)}</a></p>` : ""}
${(content.footer ?? []).map((line) => `<p style="margin:0 0 8px;font-size:13px;color:#666666">${escapeMultiline(line)}</p>`).join("\n")}
</div>
</body>
</html>`;

  const text = [
    content.heading,
    "",
    ...content.paragraphs.flatMap((paragraph) => [paragraph, ""]),
    ...rows.map((row) => `${row.label}: ${row.text}${row.href && row.href !== row.text ? ` (${row.href})` : ""}`),
    ...(rows.length ? [""] : []),
    ...(content.button ? [`${content.button.label}: ${content.button.href}`, ""] : []),
    ...(content.footer ?? []),
  ]
    .join("\n")
    .trim();

  return { subject: content.subject, html, text };
}

/** The site's address without a trailing slash, for building links. */
export function siteBase(siteUrl: string): string {
  return siteUrl.replace(/\/+$/, "");
}

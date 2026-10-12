/** Escapes text for HTML element content and quoted attribute values. */
export function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** Escaped text with its line breaks kept, for multi-line answers. */
export function escapeMultiline(value: string): string {
  return escapeHtml(value.replace(/\r\n?/g, "\n")).replace(/\n/g, "<br>");
}

/** One line of plain text: no line breaks or control characters, for subjects and labels. */
export function singleLine(value: string): string {
  return value.replace(/[\u0000-\u001f\u007f]+/g, " ").replace(/\s+/g, " ").trim();
}

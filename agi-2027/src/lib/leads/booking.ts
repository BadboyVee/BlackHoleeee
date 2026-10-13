import { z } from "zod";

/*
 * The "Book a campaign" form: one schema shared by the browser (instant
 * feedback) and the server action (the check that counts). The database
 * function public.submit_lead checks the same limits again.
 */

export const BUDGET_RANGES = [
  { value: "under_5k", label: "Under $5k" },
  { value: "5k_10k", label: "$5k to $10k" },
  { value: "10k_25k", label: "$10k to $25k" },
  { value: "25k_plus", label: "$25k+" },
  { value: "not_sure", label: "Not sure yet" },
] as const;

export type BudgetRange = (typeof BUDGET_RANGES)[number]["value"];

export function budgetLabel(value: string): string {
  return BUDGET_RANGES.find((range) => range.value === value)?.label ?? value;
}

/** Where on the site the form was sent from. */
export const LEAD_SOURCES = ["book_page", "home_cta"] as const;
export type LeadSource = (typeof LEAD_SOURCES)[number];

/** Field limits, mirrored by CHECK constraints on public.leads. */
export const LIMITS = {
  name: 80,
  email: 254,
  company: 120,
  website: 2048,
  launching: 600,
  message: 2000,
} as const;

const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Keep it under ${max} characters.`)
    .optional()
    .transform((value) => value || undefined);

/** "kled.ai" or "https://kled.ai/" become "https://kled.ai". Only http(s) links on a real domain. */
export function normalizeWebsite(input: string): string | null {
  const raw = input.trim();
  if (!raw) return null;
  const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(raw) ? raw : `https://${raw}`;
  let url: URL;
  try {
    url = new URL(withScheme);
  } catch {
    return null;
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null;
  if (url.username || url.password) return null;
  if (!/^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$/i.test(url.hostname)) return null;
  const path = url.pathname === "/" ? "" : url.pathname.replace(/\/$/, "");
  return `${url.protocol}//${url.hostname.toLowerCase()}${path}${url.search}`;
}

/** "@Kled_AI", "kled_ai" or "x.com/kled_ai" become "kled_ai". */
export function normalizeXHandle(input: string): string | null {
  const raw = input.trim();
  if (!raw) return null;
  const fromUrl = /^(?:https?:\/\/)?(?:www\.|mobile\.)?(?:x|twitter)\.com\/([^/?#]+)/i.exec(raw);
  const handle = (fromUrl ? fromUrl[1] : raw).replace(/^@/, "");
  return /^[A-Za-z0-9_]{1,15}$/.test(handle) ? handle : null;
}

export const LAUNCH_DATE_MESSAGE = "Pick a date, or leave it empty.";

/**
 * True for a YYYY-MM-DD date that exists on the calendar. JavaScript reads
 * "2026-02-31" as 3 March, but Postgres refuses it, so the form catches it
 * in the browser and again on the server, before anything is saved.
 */
export function isCalendarDate(value: string): boolean {
  // Postgres has no year 0, and a rolled-over date no longer reads the same.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith("0000")) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export const bookingSchema = z.object({
  name: z.string().trim().min(1, "Tell us your name.").max(LIMITS.name, `Keep it under ${LIMITS.name} characters.`),
  // Trim first: z.email() checks the raw text, so a stray space would fail.
  email: z.string().trim().max(LIMITS.email).pipe(z.email("Enter an email we can reply to.")),
  company: z
    .string()
    .trim()
    .min(1, "Which company is launching?")
    .max(LIMITS.company, `Keep it under ${LIMITS.company} characters.`),
  website: z
    .string()
    .trim()
    .max(LIMITS.website)
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      const normalized = normalizeWebsite(value);
      if (!normalized) {
        ctx.addIssue({ code: "custom", message: "Enter a website like example.com." });
        return z.NEVER;
      }
      return normalized;
    }),
  xHandle: z
    .string()
    .trim()
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      const handle = normalizeXHandle(value);
      if (!handle) {
        ctx.addIssue({ code: "custom", message: "Enter an X handle like @yourcompany." });
        return z.NEVER;
      }
      return handle;
    }),
  launching: z
    .string()
    .trim()
    .min(10, "A sentence or two about what you're launching.")
    .max(LIMITS.launching, `Keep it under ${LIMITS.launching} characters.`),
  /** YYYY-MM-DD from a date input, or empty when it isn't set yet. */
  launchDate: z
    .string()
    .trim()
    .optional()
    .transform((value, ctx) => {
      if (!value) return undefined;
      if (!isCalendarDate(value)) {
        ctx.addIssue({ code: "custom", message: LAUNCH_DATE_MESSAGE });
        return z.NEVER;
      }
      return value;
    }),
  budget: z.enum(BUDGET_RANGES.map((range) => range.value) as [BudgetRange, ...BudgetRange[]], {
    error: "Pick a budget range.",
  }),
  message: optionalText(LIMITS.message),
});

/** What the form fields hold before validation. */
export type BookingFormValues = z.input<typeof bookingSchema>;
/** Clean, normalized values, ready for the database. */
export type Booking = z.output<typeof bookingSchema>;

/** Hidden spam traps that travel with the form. */
export const HONEYPOT_FIELD = "company_site";
export const STARTED_AT_FIELD = "started_at";
/** Real people take longer than this to fill the form; bots usually don't. */
export const MIN_FILL_MS = 3000;

/** What the server action returns to the form (useActionState). */
export type BookingState =
  | { status: "idle" }
  | { status: "success"; name: string; email: string }
  | {
      status: "error";
      /** A message for the whole form, such as rate limiting or the database being unreachable. */
      message: string;
      fieldErrors?: Partial<Record<keyof BookingFormValues, string>>;
      /** The values sent, so the form can be refilled after a server error. */
      values?: Partial<Record<keyof BookingFormValues, string>>;
    };

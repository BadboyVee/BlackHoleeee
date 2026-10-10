/**
 * Money helpers. Amounts are exact decimal strings from the database
 * (numeric), never floats, and every amount carries its currency. Totals are
 * kept per currency: USD and NGN are never added together.
 */

/** Currencies with an ISO code that Intl can format with a symbol. */
const ISO_CURRENCIES = new Set(["USD", "NGN", "EUR", "GBP"]);

export function formatMoney(amount: number | string, currency: string): string {
  const value = typeof amount === "string" ? Number(amount) : amount;
  if (!Number.isFinite(value)) return `${amount} ${currency}`;
  const wholeNumber = Number.isInteger(value);
  if (ISO_CURRENCIES.has(currency)) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      currencyDisplay: "narrowSymbol",
      minimumFractionDigits: wholeNumber ? 0 : 2,
      maximumFractionDigits: 2,
    }).format(value);
  }
  // Stablecoins and anything else: "250 USDC".
  const number = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: wholeNumber ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(value);
  return `${number} ${currency}`;
}

/**
 * Sums amounts per currency using integer minor units, so 0.1 + 0.2 is
 * exactly 0.3. Returns one total per currency, in first-seen order.
 */
export function totalsByCurrency(
  rows: Array<{ amount: number | string; currency: string }>,
): Array<{ currency: string; amount: string }> {
  const cents = new Map<string, bigint>();
  for (const row of rows) {
    cents.set(row.currency, (cents.get(row.currency) ?? 0n) + toCents(row.amount));
  }
  return [...cents].map(([currency, value]) => ({ currency, amount: fromCents(value) }));
}

function toCents(amount: number | string): bigint {
  const text = typeof amount === "number" ? amount.toFixed(2) : amount.trim();
  const match = /^(-)?(\d+)(?:\.(\d{1,2}))?$/.exec(text);
  if (!match) throw new Error(`Invalid amount: ${amount}`);
  const [, sign, whole, fraction = ""] = match;
  const value = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0"));
  return sign ? -value : value;
}

function fromCents(value: bigint): string {
  const negative = value < 0n;
  const abs = negative ? -value : value;
  const whole = abs / 100n;
  const fraction = (abs % 100n).toString().padStart(2, "0");
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}

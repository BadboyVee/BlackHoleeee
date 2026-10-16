import { Coins, Landmark, MessageSquareText } from "lucide-react";

import { LocalDateTime } from "@/components/ui/local-time";
import { lastFour, networkLabel } from "@/lib/creators/options";
import type { PayoutDetails } from "@/lib/creators/queries";

const ICONS = { crypto: Coins, bank: Landmark, other: MessageSquareText } as const;

/** The end of an account number, ignoring the spaces and dashes people type in IBANs. */
function endOf(value: string): string {
  return lastFour(value.replace(/[\s-]+/g, ""));
}

function clip(value: string, length: number): string {
  const clean = value.replace(/\s+/g, " ").trim();
  return clean.length > length ? `${clean.slice(0, length).trimEnd()}…` : clean;
}

/** One line on where the money goes, without the full address or account number. */
export function payoutSummaryText(payout: PayoutDetails): string {
  switch (payout.method) {
    case "crypto": {
      const asset = payout.cryptoAsset ?? "Crypto";
      const network = payout.cryptoNetwork ? ` on ${networkLabel(payout.cryptoNetwork)}` : "";
      const wallet = payout.walletAddress ? `, wallet ending ${lastFour(payout.walletAddress)}` : "";
      return `${asset}${network}${wallet}`;
    }
    case "bank": {
      const account = payout.accountNumber ? `, account ending ${endOf(payout.accountNumber)}` : "";
      return `${payout.bankName ?? "Bank transfer"}${account}`;
    }
    case "other":
      return `Other: ${clip(payout.otherDetails ?? "", 60)}`;
  }
}

/** The payout details on file, shown above the form that changes them. */
export function PayoutSummary({ payout }: { payout: PayoutDetails }) {
  const Icon = ICONS[payout.method];
  return (
    <div className="flex items-start gap-3.5 rounded-xl border bg-surface-2/50 p-4">
      <span
        aria-hidden
        className="flex size-10 shrink-0 items-center justify-center rounded-xl border bg-surface text-muted-foreground shadow-xs"
      >
        <Icon className="size-[18px]" />
      </span>
      <div className="min-w-0">
        <p className="text-xs font-medium text-muted-foreground">Where we pay you</p>
        <p className="mt-0.5 text-[15px] font-semibold tracking-[-0.01em] break-words">{payoutSummaryText(payout)}</p>
        <p className="mt-1 text-[13px] text-muted-foreground">
          Changed <LocalDateTime value={payout.updatedAt} />
        </p>
      </div>
    </div>
  );
}

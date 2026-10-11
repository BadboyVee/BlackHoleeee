import { splitMoney } from "@/lib/money";
import { cn } from "@/lib/utils";

/** An amount with its unit set small: "250 USDC", "$400", "₦180,000". */
function MoneyFigure({
  amount,
  currency,
  className,
  unitClassName,
}: {
  amount: string | number;
  currency: string;
  className?: string;
  unitClassName?: string;
}) {
  const money = splitMoney(amount, currency);
  return (
    <span className={cn("inline-flex items-baseline gap-1 whitespace-nowrap", className)}>
      <span className="text-figure">{money.value}</span>
      {money.unit ? (
        <span className={cn("text-[0.62em] font-medium tracking-normal text-muted-foreground", unitClassName)}>
          {money.unit}
        </span>
      ) : null}
    </span>
  );
}

/** One line per currency. Currencies are never added together. */
function MoneyList({
  rows,
  className,
  figureClassName,
  empty = "Nothing yet",
}: {
  rows: { amount: string; currency: string }[];
  className?: string;
  figureClassName?: string;
  empty?: string;
}) {
  if (rows.length === 0) return <p className="text-sm text-muted-foreground">{empty}</p>;
  return (
    <div className={cn("flex flex-col gap-1", className)}>
      {rows.map((row) => (
        <MoneyFigure key={row.currency} amount={row.amount} currency={row.currency} className={figureClassName} />
      ))}
    </div>
  );
}

export { MoneyFigure, MoneyList };

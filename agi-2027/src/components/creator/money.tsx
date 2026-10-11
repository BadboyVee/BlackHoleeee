import { splitMoney } from "@/lib/money";
import { cn } from "@/lib/utils";

const sizes = {
  sm: { value: "text-[15px]", unit: "text-[11px]" },
  md: { value: "text-[1.375rem]", unit: "text-xs" },
  lg: { value: "text-[1.875rem]", unit: "text-[13px]" },
  xl: { value: "text-[2.5rem] sm:text-[2.75rem]", unit: "text-sm" },
} as const;

/** An exact amount with its currency: the number big, a stablecoin's code small. */
function Money({
  amount,
  currency,
  size = "md",
  className,
}: {
  amount: string;
  currency: string;
  size?: keyof typeof sizes;
  className?: string;
}) {
  const money = splitMoney(amount, currency);
  return (
    <span className={cn("inline-flex items-baseline gap-1 whitespace-nowrap", className)}>
      <span className={cn("text-figure leading-none", sizes[size].value)}>{money.value}</span>
      {money.unit ? <span className={cn("font-medium text-muted-foreground", sizes[size].unit)}>{money.unit}</span> : null}
    </span>
  );
}

export { Money };

"use client";

import { useState } from "react";
import { BarChart3, Table2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { formatMoney } from "@/lib/money";
import { formatDateTime } from "@/lib/time";
import { cn } from "@/lib/utils";
import { CHART_CURRENCIES, weeklyActivity } from "../demo-insights";
import { Segmented } from "../segmented";

type Currency = (typeof CHART_CURRENCIES)[number];
type Bar = { key: string; label: string; value: number; partial: boolean };

const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

/** "17 Aug" for a week that starts on that day (dates are UTC). */
function weekLabel(week: string) {
  return formatDateTime(`${week}T00:00:00Z`, "UTC").split(",")[0].split(" ").slice(1).join(" ");
}

/** A round top for the axis and evenly spaced ticks: 0, 10, 20. */
function niceScale(max: number) {
  if (max <= 0) return { top: 1, ticks: [0, 1] };
  const rough = max / 3;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * power).find((candidate) => candidate >= rough) ?? 10 * power;
  const top = Math.ceil(max / step) * step;
  const ticks: number[] = [];
  for (let tick = 0; tick <= top + step / 2; tick += step) ticks.push(tick);
  return { top, ticks };
}

function Bars({
  bars,
  format,
  name,
}: {
  bars: Bar[];
  /** Full value for the tooltip and screen readers. */
  format: (value: number) => string;
  name: string;
}) {
  const [active, setActive] = useState<number | null>(null);
  const { top, ticks } = niceScale(Math.max(...bars.map((bar) => bar.value)));

  return (
    <div>
      <div className="relative h-44" onPointerLeave={() => setActive(null)}>
        {/* Gridlines with their values: hairline and recessive. */}
        {ticks.map((tick) => (
          <div
            key={tick}
            aria-hidden
            className="absolute inset-x-0 border-t border-border"
            style={{ bottom: `${(tick / top) * 100}%` }}
          >
            <span className="absolute -top-2 left-0 bg-surface pr-1.5 font-mono text-[10px] leading-4 text-subtle-foreground tabular">
              {compact.format(tick)}
            </span>
          </div>
        ))}
        <div role="group" className="absolute inset-y-0 right-0 left-9 flex items-end gap-0.5" aria-label={name}>
          {bars.map((bar, index) => {
            const height = (bar.value / top) * 100;
            const isActive = active === index;
            return (
              <div
                key={bar.key}
                role="img"
                tabIndex={0}
                aria-label={`${bar.partial ? "This week so far" : `Week of ${bar.label}`}: ${format(bar.value)}`}
                onPointerEnter={() => setActive(index)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
                className="group relative flex h-full flex-1 cursor-default items-end justify-center rounded-sm outline-none focus-visible:bg-surface-2/60"
              >
                <span
                  aria-hidden
                  className={cn(
                    "block w-full max-w-6 rounded-t-[4px] transition-[background-color,opacity] duration-150",
                    bar.partial ? "bg-foreground/30" : "bg-foreground/70",
                    isActive && (bar.partial ? "bg-foreground/45" : "bg-foreground"),
                  )}
                  style={{ height: `${Math.max(height, bar.value > 0 ? 1.5 : 0)}%` }}
                />
                {isActive ? (
                  <span
                    role="presentation"
                    className={cn(
                      "pointer-events-none absolute bottom-full z-10 mb-2 w-max max-w-40 rounded-lg border border-border-strong bg-popover px-2.5 py-1.5 text-left shadow-lg",
                      index > bars.length - 3 ? "right-0" : index < 2 ? "left-0" : "left-1/2 -translate-x-1/2",
                    )}
                  >
                    <span className="block text-[13px] font-semibold text-foreground tabular">{format(bar.value)}</span>
                    <span className="block text-[11px] text-muted-foreground">
                      {bar.partial ? "This week so far" : `Week of ${bar.label}`}
                    </span>
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
      <div aria-hidden className="mt-2 flex pl-9 font-mono text-[10px] text-subtle-foreground">
        {bars.map((bar, index) => (
          <span key={bar.key} className={cn("flex-1 text-center", index % 3 !== 0 && "invisible", index === bars.length - 1 && "visible")}>
            {index === bars.length - 1 ? "Now" : bar.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * Posts approved and money paid per week. Two separate charts on purpose:
 * different measures never share an axis, and currencies are never added
 * together, so payouts show one currency at a time.
 */
export function ActivityChart() {
  const [currency, setCurrency] = useState<Currency>("USDC");
  const [asTable, setAsTable] = useState(false);
  const last = weeklyActivity.length - 1;

  const posts: Bar[] = weeklyActivity.map((week, index) => ({
    key: week.week,
    label: weekLabel(week.week),
    value: week.posts,
    partial: index === last,
  }));
  const paid: Bar[] = weeklyActivity.map((week, index) => ({
    key: week.week,
    label: weekLabel(week.week),
    value: Number(week.paid[currency]),
    partial: index === last,
  }));
  const totalPosts = posts.reduce((sum, bar) => sum + bar.value, 0);

  return (
    <section
      aria-labelledby="activity-title"
      className="min-w-0 overflow-hidden rounded-lg border bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.04)]"
    >
      <div className="flex min-h-13 items-center justify-between gap-3 border-b px-4 py-3 sm:px-5">
        <div className="min-w-0">
          <h2 id="activity-title" className="text-[14px] font-semibold tracking-[-0.01em]">
            Posts and payouts
          </h2>
          <p className="mt-0.5 text-xs text-muted-foreground">Last 12 weeks. The latest week is still running.</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setAsTable((value) => !value)} aria-pressed={asTable}>
          {asTable ? <BarChart3 aria-hidden /> : <Table2 aria-hidden />}
          {asTable ? "Show chart" : "Show table"}
        </Button>
      </div>

      {asTable ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-sm">
            <caption className="sr-only">Posts approved and amounts paid per week</caption>
            <thead>
              <tr className="border-b text-left text-label text-subtle-foreground">
                <th scope="col" className="px-5 py-2.5 font-medium">Week of</th>
                <th scope="col" className="px-3 py-2.5 text-right font-medium">Posts</th>
                {CHART_CURRENCIES.map((code) => (
                  <th key={code} scope="col" className="px-3 py-2.5 text-right font-medium last:pr-5">
                    Paid {code}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {weeklyActivity.map((week, index) => (
                <tr key={week.week} className="border-b last:border-b-0">
                  <th scope="row" className="px-5 py-2 text-left font-medium">
                    {weekLabel(week.week)}
                    {index === last ? <span className="ml-1.5 text-xs font-normal text-muted-foreground">(so far)</span> : null}
                  </th>
                  <td className="px-3 py-2 text-right tabular">{week.posts}</td>
                  {CHART_CURRENCIES.map((code) => (
                    <td key={code} className="px-3 py-2 text-right tabular last:pr-5">
                      {formatMoney(week.paid[code], code)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid gap-px bg-border md:grid-cols-2">
          <figure className="bg-surface px-4 pt-4 pb-4 sm:px-5">
            <figcaption className="mb-5 flex min-h-8 items-center justify-between gap-3">
              <span className="text-[13px] font-medium">Posts approved per week</span>
              <span className="text-xs text-muted-foreground tabular">{totalPosts} in 12 weeks</span>
            </figcaption>
            <Bars bars={posts} name="Posts approved per week" format={(value) => `${value} ${value === 1 ? "post" : "posts"}`} />
          </figure>
          <figure className="bg-surface px-4 pt-4 pb-4 sm:px-5">
            <figcaption className="mb-5 flex min-h-8 items-center justify-between gap-3">
              <span className="text-[13px] font-medium">Paid out per week</span>
              <Segmented
                size="sm"
                value={currency}
                onChange={setCurrency}
                aria-label="Currency"
                options={CHART_CURRENCIES.map((code) => ({ value: code, label: code }))}
              />
            </figcaption>
            <Bars bars={paid} name={`Paid out per week in ${currency}`} format={(value) => formatMoney(value, currency)} />
          </figure>
        </div>
      )}
    </section>
  );
}

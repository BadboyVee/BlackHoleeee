import { cn } from "@/lib/utils";

function channel(value: number) {
  const s = value / 255;
  return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** White or near-black, whichever reads better on a brand color. */
export function inkOn(hex: string): string {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!match) return "#ffffff";
  const n = parseInt(match[1], 16);
  const luminance = 0.2126 * channel((n >> 16) & 255) + 0.7152 * channel((n >> 8) & 255) + 0.0722 * channel(n & 255);
  const onWhite = 1.05 / (luminance + 0.05);
  const onInk = (luminance + 0.05) / 0.0565;
  return onWhite >= onInk ? "#ffffff" : "#16120f";
}

const sizes = {
  xs: "size-7 text-[10px]",
  sm: "size-9 text-[11px]",
  md: "size-11 text-[13px]",
  lg: "size-14 text-base",
  xl: "size-[4.5rem] text-xl",
} as const;

/** The client's logo tile: their color, their initials, a little shine. */
function BrandTile({
  initials,
  color,
  size = "md",
  className,
}: {
  initials: string;
  color: string;
  size?: keyof typeof sizes;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-[min(30%,calc(var(--radius)*1.1))] font-display leading-none tracking-[0.02em] uppercase select-none [font-weight:var(--display-weight)]",
        "shadow-[inset_0_1px_0_rgb(255_255_255/0.28),inset_0_-1px_0_rgb(0_0_0/0.12),0_1px_2px_rgb(var(--shadow-rgb)/0.18),0_6px_14px_-6px_rgb(var(--shadow-rgb)/0.35)]",
        sizes[size],
        className,
      )}
      style={{ backgroundColor: color, color: inkOn(color) }}
    >
      <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_90%_at_15%_0%,rgb(255_255_255/0.32),transparent_55%)]" />
      <span className="relative">{initials}</span>
    </span>
  );
}

/** A soft wash of the brand color for the top of a card. */
function brandWash(color: string, strength = 14) {
  return {
    backgroundImage: `radial-gradient(130% 90% at 0% 0%, color-mix(in oklab, ${color} ${strength}%, transparent), transparent 62%)`,
  };
}

export { BrandTile, brandWash };

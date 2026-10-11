import { cn } from "@/lib/utils";

const sizes = {
  xs: "size-6 text-[9px]",
  sm: "size-8 text-[10px]",
  md: "size-9 text-[11px]",
  lg: "size-11 text-[13px]",
  xl: "size-14 text-base",
} as const;

/**
 * A client's logo tile: their brand color with white initials, shaped like an
 * app icon. Brands without a color yet (a new brand) get a neutral tile.
 */
function BrandTile({
  initials,
  color,
  size = "md",
  className,
}: {
  initials: string;
  color?: string;
  size?: keyof typeof sizes;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center rounded-[30%] font-mono font-semibold tracking-tight select-none",
        color
          ? "text-white shadow-[inset_0_1px_0_rgb(255_255_255/0.22),0_1px_2px_rgb(var(--shadow-rgb)/0.18)]"
          : "border border-border-strong bg-surface-3 text-foreground",
        sizes[size],
        className,
      )}
      style={color ? { backgroundColor: color } : undefined}
    >
      {initials || "?"}
    </span>
  );
}

/** Two letters from a brand name: "Nebula AI" is NA, "Orbitar" is OR. */
function brandInitials(name: string) {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

export { BrandTile, brandInitials };

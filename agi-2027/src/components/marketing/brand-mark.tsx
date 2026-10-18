import Image from "next/image";

import type { Brand } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";

/**
 * A client's own logo beside their name in the brand strip: their X profile
 * picture, square or round as X shows it. Brands without a logo of their own
 * get nothing here, and their name stands alone as a wordmark. Never draw a
 * stand-in mark: it would read as the brand's logo.
 *
 * Asked for at 40 pixels, the largest the strip shows it (Drop on a wide
 * screen), so it stays sharp on high density screens. The ring is stronger in
 * dark mode, where a dark logo (Maincode's) would otherwise melt into the page.
 */
function BrandMark({ brand, className }: { brand: Brand; className?: string }) {
  if (!brand.logo) return null;
  return (
    <Image
      src={brand.logo.src}
      alt=""
      width={40}
      height={40}
      className={cn(
        "size-6 shrink-0 object-cover ring-1 ring-border-strong dark:ring-foreground/30",
        brand.logo.shape === "circle" ? "rounded-full" : "rounded-[22%]",
        className,
      )}
    />
  );
}

export { BrandMark };

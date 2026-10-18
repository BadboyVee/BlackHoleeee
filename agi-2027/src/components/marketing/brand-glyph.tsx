import Image from "next/image";

import type { Brand } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";

/**
 * A client's own logo beside their name in the brand strip: their X profile
 * picture, square or round as X shows it. Brands without a logo of their own
 * get nothing here, and their name stands alone as a wordmark. Never draw a
 * stand-in mark: it would read as the brand's logo.
 */
function BrandMark({ brand, className }: { brand: Brand; className?: string }) {
  if (!brand.logo) return null;
  return (
    <Image
      src={brand.logo.src}
      alt=""
      width={32}
      height={32}
      className={cn(
        "size-6 shrink-0 object-cover ring-1 ring-border",
        brand.logo.shape === "circle" ? "rounded-full" : "rounded-[22%]",
        className,
      )}
    />
  );
}

export { BrandMark };

import * as React from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";

import type { Tone } from "@/lib/statuses";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex h-[22px] w-fit shrink-0 items-center gap-1.5 rounded-full px-2 text-xs font-medium whitespace-nowrap [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-3",
  {
    variants: {
      variant: {
        /** Neutral pill. Pair with a StatusDot for status. */
        default: "border border-border bg-surface-2/60 text-muted-foreground",
        /** Text in the tone color, for statuses that need attention. */
        tone: "border border-border bg-surface-2/60 text-(--tone-fg)",
        outline: "border border-border-strong text-muted-foreground",
        solid: "bg-foreground text-background",
        brand: "bg-brand text-brand-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

type BadgeProps = React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & {
    tone?: Tone;
    asChild?: boolean;
  };

function Badge({ className, variant, tone = "gray", asChild = false, ...props }: BadgeProps) {
  const Comp = asChild ? Slot.Root : "span";
  return (
    <Comp
      data-slot="badge"
      data-tone={tone}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };

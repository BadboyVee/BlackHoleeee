import * as React from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-full font-medium whitespace-nowrap select-none",
    "transition-[color,background-color,border-color,box-shadow,transform,opacity] duration-200 ease-out",
    "active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ],
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-sm hover:bg-primary/88",
        brand:
          "bg-brand text-brand-foreground shadow-[0_0_0_1px_var(--brand-edge),0_10px_30px_-10px_var(--brand-glow)] hover:shadow-[0_0_0_1px_var(--brand-edge),0_14px_40px_-8px_var(--brand-glow)] hover:brightness-105",
        secondary:
          "border border-border bg-surface-2 text-foreground hover:border-border-strong hover:bg-surface-3",
        outline:
          "border border-border-strong bg-transparent text-foreground hover:bg-surface-2",
        ghost: "text-foreground hover:bg-surface-2",
        destructive: "bg-destructive text-white shadow-sm hover:bg-destructive/90",
        link: "h-auto rounded-sm px-0 text-brand-text underline-offset-4 hover:underline active:scale-100",
      },
      size: {
        sm: "h-9 px-3.5 text-[13px]",
        default: "h-11 px-5 text-sm",
        lg: "h-12 px-6 text-[15px]",
        xl: "h-14 px-7 text-base",
        icon: "size-11",
        "icon-sm": "size-9",
      },
    },
    compoundVariants: [{ variant: "link", class: "h-auto px-0" }],
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
    /** Shows a spinner and blocks clicks while an action runs. */
    loading?: boolean;
  };

function Button({
  className,
  variant,
  size,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot.Root : "button";

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={asChild ? undefined : disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {asChild ? (
        children
      ) : (
        <>
          {loading ? <Loader2 className="animate-spin" aria-hidden /> : null}
          {children}
        </>
      )}
    </Comp>
  );
}

export { Button, buttonVariants };
export type { ButtonProps };

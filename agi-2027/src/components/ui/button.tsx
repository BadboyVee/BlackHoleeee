import * as React from "react";
import { Slot } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-full font-medium tracking-[-0.01em] whitespace-nowrap select-none",
    "transition-[color,background-color,border-color,box-shadow,transform,opacity] duration-200 ease-out",
    "active:scale-[0.98] disabled:pointer-events-none disabled:opacity-45 aria-disabled:pointer-events-none aria-disabled:opacity-45",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ],
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-[inset_0_1px_0_rgb(255_255_255/0.14),0_1px_2px_rgb(var(--shadow-rgb)/0.25),0_4px_10px_rgb(var(--shadow-rgb)/0.12)] hover:bg-primary/85",
        brand: "bg-brand text-brand-foreground hover:bg-brand/90",
        secondary:
          "border border-border-strong bg-surface text-foreground shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.06)] hover:bg-surface-2",
        outline: "border border-border-strong text-foreground hover:bg-surface-2",
        ghost: "text-muted-foreground hover:bg-surface-2 hover:text-foreground",
        destructive: "bg-destructive text-white hover:bg-destructive/90",
        link: "h-auto rounded-sm px-0 text-foreground underline decoration-border-strong underline-offset-4 hover:decoration-foreground active:scale-100",
      },
      size: {
        sm: "h-8 px-3 text-[13px]",
        default: "h-10 px-4 text-sm",
        lg: "h-11 px-5 text-[15px]",
        xl: "h-12 px-6 text-[15px]",
        icon: "size-10",
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

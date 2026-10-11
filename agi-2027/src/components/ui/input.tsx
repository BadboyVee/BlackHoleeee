import * as React from "react";

import { cn } from "@/lib/utils";

/** Shared look for text inputs, textareas and select triggers. */
export const fieldControlClass = cn(
  "w-full min-w-0 rounded-xl border border-input bg-surface text-foreground shadow-xs outline-none",
  "transition-[border-color,box-shadow,background-color] duration-150",
  "placeholder:text-subtle-foreground",
  "hover:border-border-strong",
  "focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-ring/20 focus-visible:outline-none",
  "aria-invalid:border-destructive-text aria-invalid:focus-visible:ring-destructive-text/20",
  "disabled:cursor-not-allowed disabled:opacity-50",
  // 16px on phones stops iOS from zooming into the field.
  "text-base sm:text-[15px]",
);

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        fieldControlClass,
        "h-11 px-3.5",
        "file:mr-3 file:inline-flex file:h-7 file:rounded-md file:border-0 file:bg-surface-2 file:px-2.5 file:text-sm file:font-medium file:text-foreground",
        className,
      )}
      {...props}
    />
  );
}

export { Input };

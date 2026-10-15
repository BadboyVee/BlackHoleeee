import * as React from "react";
import { ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { fieldControlClass } from "./input";

/**
 * The browser's own select, styled like the other fields. Use it for long
 * lists (countries): phones open their native picker, typing jumps to an
 * option, and it posts with the form before JavaScript loads.
 */
function NativeSelect({ className, children, ...props }: React.ComponentProps<"select">) {
  return (
    <div data-slot="native-select" className="relative">
      <select
        className={cn(
          fieldControlClass,
          "h-11 cursor-pointer appearance-none pr-10 pl-3.5 invalid:text-subtle-foreground [&>option]:text-foreground",
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown aria-hidden className="pointer-events-none absolute top-1/2 right-3.5 size-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  );
}

export { NativeSelect };

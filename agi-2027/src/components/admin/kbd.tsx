"use client";

import { useSyncExternalStore } from "react";

import { cn } from "@/lib/utils";

const noopSubscribe = () => () => {};

/** True on Apple devices (show ⌘), false elsewhere (show Ctrl). False on the server and during hydration. */
export function useIsApple() {
  return useSyncExternalStore(
    noopSubscribe,
    () => /Mac|iPhone|iPad/i.test(navigator.userAgent),
    () => false,
  );
}

/** A keyboard key hint, like ⌘K or Enter. */
function Kbd({ className, ...props }: React.ComponentProps<"kbd">) {
  return (
    <kbd
      className={cn(
        "inline-flex h-5 min-w-5 items-center justify-center gap-0.5 rounded-[5px] border border-border-strong bg-surface px-1 font-mono text-[10px] font-medium text-muted-foreground shadow-[0_1px_0_var(--border-strong)]",
        className,
      )}
      {...props}
    />
  );
}

export { Kbd };

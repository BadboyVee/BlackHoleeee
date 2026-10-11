"use client";

import { useLayoutEffect, useSyncExternalStore } from "react";
import { Check, Palette } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  applyLook,
  currentLook,
  LOOKS,
  readStoredLook,
  storeLook,
  subscribeLook,
  type Look,
} from "@/lib/theme";
import { cn } from "@/lib/utils";

/** The active look, or null during server render (the attribute is set before paint). */
export function useLook(): Look | null {
  return useSyncExternalStore(subscribeLook, currentLook, () => null);
}

/** Switch looks with a circle that grows from where the visitor tapped. */
export function switchLook(look: Look, origin?: { x: number; y: number }) {
  storeLook(look);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!("startViewTransition" in document) || reduceMotion) {
    applyLook(look);
    return;
  }
  const x = origin?.x ?? window.innerWidth / 2;
  const y = origin?.y ?? 0;
  const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
  const transition = document.startViewTransition(() => applyLook(look));
  transition.ready
    .then(() => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        {
          duration: 700,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          pseudoElement: "::view-transition-new(root)",
        },
      );
    })
    .catch(() => {});
}

/** Tiny preview of each look, drawn with CSS so it costs nothing. */
export function LookSwatch({ look, className }: { look: Look; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn(
        "relative block shrink-0 overflow-hidden rounded-md ring-1 ring-black/10 ring-inset",
        look === "renaissance" && "bg-[url(/art/orion-1600.webp)] bg-cover bg-position-[62%_40%]",
        look === "agent" && "bg-[radial-gradient(circle_at_65%_45%,#f0493c,#b5170f_75%)]",
        look === "drop" &&
          "bg-[linear-gradient(90deg,#e0252b_0_25%,#cf4a00_25%_50%,#127a36_50%_75%,#5b2ee8_75%)]",
        className,
      )}
    >
      {look === "renaissance" ? (
        <span className="absolute top-[38%] left-[48%] size-1.5 rounded-full bg-white shadow-[0_0_8px_3px_rgb(255_255_255/0.8)]" />
      ) : null}
      {look === "agent" ? (
        <span className="absolute top-1/2 right-[18%] flex size-[60%] max-h-5 max-w-5 -translate-y-1/2 items-center justify-center gap-[2px] rounded-full bg-[#e9b48f]">
          <span className="size-[3px] rounded-full bg-[#231511]" />
          <span className="size-[3px] rounded-full bg-[#231511]" />
        </span>
      ) : null}
      {look === "drop" ? (
        <span className="absolute inset-0 flex items-center justify-center font-[family-name:var(--font-anton)] text-[11px] leading-none text-white">
          GO
        </span>
      ) : null}
    </span>
  );
}

/** Keeps the saved mode and look applied (React's dev remount can drop them). */
export function useLookSync() {
  useLayoutEffect(() => {
    if (currentLook() !== readStoredLook() && !new URLSearchParams(location.search).get("look")) {
      applyLook(readStoredLook());
    }
  }, []);
}

function LookPicker({
  className,
  tone = "default",
}: {
  className?: string;
  /** "hero" draws a white control for use over the hero art. */
  tone?: "default" | "hero";
}) {
  const look = useLook();
  useLookSync();
  const active = LOOKS.find((item) => item.id === look);

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger
        className={cn(
          "pressable inline-flex h-9 cursor-pointer items-center gap-2 rounded-full pr-3 pl-1.5 text-[13px] font-medium outline-none",
          tone === "hero"
            ? "bg-white/15 text-white ring-1 ring-white/25 backdrop-blur-md hover:bg-white/25"
            : "bg-surface-2 text-foreground ring-1 ring-border hover:bg-surface-3",
          className,
        )}
        aria-label={`Change the look. Current look: ${active?.name ?? "loading"}`}
      >
        {look ? (
          <LookSwatch look={look} className="size-6 rounded-full" />
        ) : (
          <Palette className="size-4" aria-hidden />
        )}
        <span>Look</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={10} className="w-[19rem] p-1.5">
        <DropdownMenuLabel className="px-2 pt-1.5 pb-2 text-xs font-normal text-muted-foreground">
          Pick a look for the whole site. It&apos;s saved on this device.
        </DropdownMenuLabel>
        {LOOKS.map((item) => (
          <DropdownMenuItem
            key={item.id}
            onSelect={(event) => {
              const target = event.currentTarget as HTMLElement | null;
              const rect = target?.getBoundingClientRect();
              switchLook(
                item.id,
                rect ? { x: rect.left + 28, y: rect.top + rect.height / 2 } : undefined,
              );
            }}
            className="items-start gap-3 rounded-lg p-2"
          >
            <LookSwatch look={item.id} className="mt-0.5 h-10 w-14" />
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
                {item.name}
                {item.id === look ? <Check className="size-3.5 text-brand-text" aria-hidden /> : null}
              </span>
              <span className="mt-0.5 block text-xs leading-snug text-muted-foreground">
                {item.description}
              </span>
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { LookPicker };

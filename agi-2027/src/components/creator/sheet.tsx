"use client";

import { useState } from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { X } from "lucide-react";
import { AnimatePresence, motion, useDragControls } from "motion/react";

import { cn } from "@/lib/utils";

import { useMediaQuery } from "./hooks";
import { springArrive } from "./motion";

type CreatorSheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  /** Keep the title for screen readers but don't show it (the body has its own heading). */
  hideHeader?: boolean;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
};

/**
 * The creator app's sheet: rises from the bottom on phones (drag the handle
 * down to dismiss), a centered card on bigger screens. Springs in, and fades
 * only for people who ask for reduced motion.
 */
function CreatorSheet({ open, onOpenChange, title, description, hideHeader, children, footer, className }: CreatorSheetProps) {
  const desktop = useMediaQuery("(min-width: 640px)");
  const drag = useDragControls();

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open ? (
          <DialogPrimitive.Portal forceMount>
            <DialogPrimitive.Overlay asChild forceMount>
              <motion.div
                className="fixed inset-0 z-50 bg-overlay backdrop-blur-[3px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.22 }}
              />
            </DialogPrimitive.Overlay>
            <DialogPrimitive.Content
              asChild
              forceMount
              {...(description ? {} : { "aria-describedby": undefined })}
            >
              <motion.div
                className={cn(
                  "fixed z-50 flex flex-col border border-border-strong bg-popover text-foreground shadow-2xl outline-none",
                  "inset-x-0 bottom-0 max-h-[92dvh] rounded-t-[1.75rem]",
                  "sm:inset-auto sm:top-1/2 sm:left-1/2 sm:max-h-[min(88dvh,46rem)] sm:w-[min(32rem,calc(100vw-2rem))] sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-[1.75rem]",
                  className,
                )}
                initial={desktop ? { opacity: 0, scale: 0.96, y: 14 } : { y: "105%" }}
                animate={desktop ? { opacity: 1, scale: 1, y: 0 } : { y: 0 }}
                exit={desktop ? { opacity: 0, scale: 0.97, y: 10 } : { y: "105%" }}
                transition={springArrive}
                drag={desktop ? false : "y"}
                dragListener={false}
                dragControls={drag}
                dragConstraints={{ top: 0, bottom: 0 }}
                dragElastic={{ top: 0.04, bottom: 0.65 }}
                onDragEnd={(_, info) => {
                  if (info.offset.y > 110 || info.velocity.y > 650) onOpenChange(false);
                }}
              >
                {desktop ? null : (
                  <div
                    aria-hidden
                    onPointerDown={(event) => drag.start(event)}
                    className="flex h-6 shrink-0 cursor-grab touch-none items-end justify-center active:cursor-grabbing"
                  >
                    <span className="h-1.5 w-11 rounded-full bg-border-strong" />
                  </div>
                )}
                <div
                  onPointerDown={desktop ? undefined : (event) => drag.start(event)}
                  className={cn(
                    "flex shrink-0 items-start gap-3 px-5 pt-2 pb-3 sm:px-6 sm:pt-6",
                    hideHeader && "sr-only",
                    !desktop && "touch-none",
                  )}
                >
                  <div className="min-w-0 flex-1 pt-1.5">
                    <DialogPrimitive.Title className="text-lg leading-tight font-semibold tracking-[-0.02em] text-balance">
                      {title}
                    </DialogPrimitive.Title>
                    {description ? (
                      <DialogPrimitive.Description className="mt-1.5 text-sm text-pretty text-muted-foreground">
                        {description}
                      </DialogPrimitive.Description>
                    ) : null}
                  </div>
                  <DialogPrimitive.Close className="-mr-1.5 inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground">
                    <X className="size-[18px]" />
                    <span className="sr-only">Close</span>
                  </DialogPrimitive.Close>
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 pb-5 sm:px-6 sm:pb-6">{children}</div>
                {footer ? (
                  <div className="shrink-0 border-t px-5 pt-3 pb-[max(env(safe-area-inset-bottom),1rem)] sm:px-6 sm:pb-5">
                    {footer}
                  </div>
                ) : null}
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        ) : null}
      </AnimatePresence>
    </DialogPrimitive.Root>
  );
}

/** Actions pinned to the bottom of a sheet's scrolling body. */
function SheetActions({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "sticky bottom-0 z-10 -mx-5 mt-6 -mb-5 flex flex-col-reverse gap-2 border-t bg-popover px-5 pt-3 pb-[max(env(safe-area-inset-bottom),1rem)] sm:-mx-6 sm:-mb-6 sm:flex-row sm:justify-end sm:px-6 sm:pb-5",
        className,
      )}
    >
      {children}
    </div>
  );
}

/**
 * Counts each time a sheet opens, so its content can start fresh on every
 * open while the old content stays put during the closing animation.
 */
function useSheetSession(open: boolean): number {
  const [session, setSession] = useState({ open, key: 0 });
  if (session.open !== open) setSession({ open, key: open ? session.key + 1 : session.key });
  return session.key;
}

export { CreatorSheet, SheetActions, useSheetSession };

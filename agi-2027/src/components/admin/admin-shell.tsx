"use client";

import { MotionConfig } from "motion/react";

import { SkipLink } from "@/components/layout/skip-link";
import { AdminSidebar } from "./admin-sidebar";
import { AdminTabBar } from "./admin-tabbar";
import { AdminTopBar } from "./admin-topbar";
import { CommandPaletteProvider } from "./command-palette";

/**
 * The owner's control room: a grouped sidebar with New campaign on top, a top
 * bar with breadcrumbs, search (⌘K), notifications, theme, look and account.
 * Phones get a compact top bar, four tabs plus More, and a floating New
 * campaign button. Motion follows the viewer's reduced motion setting.
 */
export function AdminShell({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user">
      <CommandPaletteProvider>
        <div className="relative min-h-dvh bg-background lg:grid lg:grid-cols-[15rem_minmax(0,1fr)]">
          <SkipLink />
          <AdminSidebar />
          <div className="flex min-w-0 flex-col">
            <AdminTopBar />
            <main
              id="main"
              tabIndex={-1}
              className="mx-auto w-full max-w-[86rem] flex-1 px-4 pt-5 pb-36 outline-none sm:px-6 lg:px-8 lg:pt-8 lg:pb-16"
            >
              {children}
            </main>
          </div>
          <AdminTabBar />
        </div>
      </CommandPaletteProvider>
    </MotionConfig>
  );
}

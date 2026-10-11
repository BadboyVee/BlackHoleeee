"use client";

import { useLayoutEffect } from "react";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { applyTheme, readStoredTheme, storeTheme, THEME_STORAGE_KEY, type Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";

function ThemeToggle({ className }: { className?: string }) {
  useLayoutEffect(() => {
    // React's dev remount clears attributes set by the inline script; put the
    // saved theme back before paint. Also follow changes made in other tabs.
    applyTheme(readStoredTheme());
    function onStorage(event: StorageEvent) {
      if (event.key === THEME_STORAGE_KEY) applyTheme(readStoredTheme());
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  function toggle() {
    const current: Theme =
      document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
    const next: Theme = current === "dark" ? "light" : "dark";
    storeTheme(next);
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if ("startViewTransition" in document && !reduceMotion) {
      document.startViewTransition(() => applyTheme(next));
    } else {
      applyTheme(next);
    }
  }

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={toggle}
      className={cn("text-muted-foreground hover:text-foreground", className)}
      aria-label="Switch between dark and light mode"
      title="Switch between dark and light mode"
    >
      <Sun className="hidden dark:block" />
      <Moon className="dark:hidden" />
    </Button>
  );
}

export { ThemeToggle };

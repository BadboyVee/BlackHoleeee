import Link from "next/link";
import { Bell } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { BottomTabBar, SideNav, type Area } from "./app-nav";
import { SkipLink } from "./skip-link";
import { UserMenu } from "./user-menu";

const areaConfig: Record<Area, { home: string; label: string; notifications: string }> = {
  creator: {
    home: "/dashboard",
    label: "Creator portal",
    notifications: "/dashboard/notifications",
  },
  admin: {
    home: "/admin",
    label: "Agency admin",
    notifications: "/admin/notifications",
  },
};

/**
 * The signed-in app frame: a sidebar on desktop, a top bar plus a bottom tab
 * bar on phones. Shared by the creator portal and the agency admin.
 */
function AppShell({ area, children }: { area: Area; children: React.ReactNode }) {
  const config = areaConfig[area];

  return (
    <div className="relative min-h-dvh lg:grid lg:grid-cols-[17rem_minmax(0,1fr)]">
      <SkipLink />

      <aside className="sticky top-0 hidden h-dvh flex-col border-r bg-surface/40 lg:flex">
        <div className="flex h-16 shrink-0 items-center gap-2 px-5">
          <Link href={config.home} aria-label={`${config.label} home`}>
            <Logo />
          </Link>
          {area === "admin" ? <AdminPill /> : null}
        </div>
        <nav aria-label={config.label} className="flex-1 overflow-y-auto px-3 py-3">
          <SideNav area={area} />
        </nav>
        <div className="m-3 flex items-center gap-2.5 rounded-xl border bg-surface px-3 py-2.5">
          <span aria-hidden className="size-1.5 shrink-0 rounded-full bg-(--tone-amber)" />
          <p className="text-xs leading-snug text-muted-foreground">
            Preview mode. Sign in arrives in Milestone 3.
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-xl">
          <div className="flex h-14 items-center gap-2 px-4 sm:px-6 lg:h-16 lg:px-10">
            <Link href={config.home} className="lg:hidden" aria-label={`${config.label} home`}>
              <Logo />
            </Link>
            {area === "admin" ? <AdminPill className="lg:hidden" /> : null}
            <p className="hidden text-label text-subtle-foreground lg:block">{config.label}</p>
            <div className="ml-auto flex items-center gap-1">
              <Button asChild variant="ghost" size="icon-sm" className="text-muted-foreground hover:text-foreground">
                <Link href={config.notifications} aria-label="Notifications">
                  <Bell />
                </Link>
              </Button>
              <ThemeToggle />
              <UserMenu area={area} />
            </div>
          </div>
        </header>

        <main
          id="main"
          tabIndex={-1}
          className="mx-auto w-full max-w-6xl flex-1 px-4 pt-6 pb-32 outline-none sm:px-6 lg:px-10 lg:pt-10 lg:pb-16"
        >
          {children}
        </main>
      </div>

      <BottomTabBar area={area} />
    </div>
  );
}

function AdminPill({ className }: { className?: string }) {
  return (
    <span
      className={`rounded-full border border-border-strong px-2 py-0.5 font-mono text-[10px] font-medium tracking-[0.12em] text-muted-foreground uppercase ${className ?? ""}`}
    >
      Admin
    </span>
  );
}

export { AppShell };

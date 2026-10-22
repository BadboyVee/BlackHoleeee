"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "motion/react";
import { Lock, Plus } from "lucide-react";

import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { showSampleData } from "@/lib/sample-data";

import { adminNavGroups, isActiveAdminPath, type AdminNavItem } from "./admin-nav";
import { springMove } from "./motion";

/*
 * Active highlighting reads the URL, which isn't known while a page with an
 * unknown dynamic segment prerenders. Each list renders once without a
 * highlight as the Suspense fallback, so the shell stays in the static HTML.
 */

function NavLink({
  item,
  active,
  layoutKey,
  onNavigate,
}: {
  item: AdminNavItem;
  active: boolean;
  layoutKey: string;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex min-h-9 items-center gap-2.5 rounded-lg px-2.5 text-[13.5px] font-medium transition-colors duration-150 pointer-coarse:min-h-11",
        active ? "text-foreground" : "text-muted-foreground hover:bg-surface/70 hover:text-foreground",
      )}
    >
      {active ? (
        <motion.span
          layoutId={`${layoutKey}-active`}
          transition={springMove}
          aria-hidden
          className="absolute inset-0 rounded-lg border border-border bg-surface shadow-[0_1px_2px_rgb(var(--shadow-rgb)/0.08)]"
        />
      ) : null}
      <Icon
        aria-hidden
        className={cn(
          "relative size-4 shrink-0 transition-colors",
          active ? "text-foreground" : "text-subtle-foreground group-hover:text-foreground",
        )}
      />
      <span className="relative truncate">{item.label}</span>
      <span className="relative ml-auto flex items-center gap-1.5">
        {item.adminOnly ? (
          <span title="Only the admin can open this" className="inline-flex">
            <Lock aria-hidden className="size-3 text-subtle-foreground" />
            <span className="sr-only">(admin only)</span>
          </span>
        ) : null}
        {item.count ? (
          <span
            className={cn(
              "min-w-5 rounded-full px-1.5 text-center font-mono text-[11px] leading-5 font-medium tabular",
              item.urgent ? "bg-foreground text-background" : "text-subtle-foreground",
            )}
          >
            {item.count}
            <span className="sr-only">{item.urgent ? " waiting" : " new"}</span>
          </span>
        ) : null}
      </span>
    </Link>
  );
}

export function NavGroups({
  pathname,
  layoutKey,
  onNavigate,
}: {
  pathname: string | null;
  layoutKey: string;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex flex-col gap-5">
      {adminNavGroups.map((group) => (
        <div key={group.label}>
          <p className="px-2.5 pb-1.5 text-label text-subtle-foreground">{group.label}</p>
          <ul className="flex flex-col gap-px">
            {group.items.map((item) => (
              <li key={item.href}>
                <NavLink
                  item={item}
                  layoutKey={layoutKey}
                  onNavigate={onNavigate}
                  active={pathname ? isActiveAdminPath(pathname, item.href) : false}
                />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function ActiveNavGroups(props: { layoutKey: string; onNavigate?: () => void }) {
  const pathname = usePathname();
  return <NavGroups pathname={pathname} {...props} />;
}

/** Nav that highlights the current page once the URL is known. */
export function AdminNav(props: { layoutKey: string; onNavigate?: () => void }) {
  return (
    <Suspense fallback={<NavGroups pathname={null} {...props} />}>
      <ActiveNavGroups {...props} />
    </Suspense>
  );
}

/** A quiet reminder that nothing here is saved yet. Preview links only. */
export function PreviewNote({ className }: { className?: string }) {
  if (!showSampleData()) return null;
  return (
    <div className={cn("flex items-start gap-2.5 px-2 py-1.5", className)}>
      <span aria-hidden className="mt-[7px] size-1.5 shrink-0 rounded-full bg-(--tone-amber)" />
      <p className="text-xs leading-relaxed text-muted-foreground">
        <span className="font-medium text-foreground">Preview with demo data.</span> Nothing is saved until Milestone 5.
      </p>
    </div>
  );
}

export function AdminSidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh flex-col border-r bg-surface-2/40 lg:flex">
      <div className="flex h-14 shrink-0 items-center gap-2 px-5">
        <Link href="/admin" aria-label="Agency admin home" className="rounded-md">
          <Logo />
        </Link>
        <span className="rounded-full border border-border-strong px-1.5 py-px font-mono text-[10px] font-medium tracking-[0.12em] text-muted-foreground uppercase">
          Admin
        </span>
      </div>
      {/* The builder only saves on preview links for now, so the live site doesn't offer it. */}
      {showSampleData() ? (
        <div className="px-3 pt-1 pb-4">
          <Button asChild className="w-full">
            <Link href="/admin/campaigns/new">
              <Plus aria-hidden />
              New campaign
            </Link>
          </Button>
        </div>
      ) : (
        <div className="pb-2" />
      )}
      <nav aria-label="Admin sections" className="min-h-0 flex-1 overflow-y-auto px-3 pb-4">
        <AdminNav layoutKey="sidebar" />
      </nav>
      {showSampleData() ? (
        <div className="border-t px-3 py-3">
          <PreviewNote />
        </div>
      ) : null}
    </aside>
  );
}

"use client";

import Link from "next/link";
import { ArrowUpRight, LogIn, Palette, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * Avatar menu. Until sign-in lands in Milestone 3 the portal runs in preview
 * mode, so the menu says so and offers the sign-in page instead of log out.
 */
function UserMenu({ area }: { area: "creator" | "admin" }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label="Account menu" className="rounded-full">
          <span className="flex size-8 items-center justify-center rounded-full bg-surface-3 ring-1 ring-border-strong">
            <UserRound className="size-4 text-muted-foreground" />
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel className="flex flex-col gap-1">
          <span>Preview mode</span>
          <span className="text-xs font-normal text-muted-foreground">
            You&apos;re looking at the {area === "admin" ? "admin" : "creator portal"} layout. Sign in arrives in
            Milestone 3.
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/styleguide">
            <Palette />
            Design system
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/">
            <ArrowUpRight />
            Public site
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/login">
            <LogIn />
            Sign in
          </Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { UserMenu };

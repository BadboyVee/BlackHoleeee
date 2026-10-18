"use client";

import { Suspense } from "react";
import Link from "next/link";
import { ArrowUpRight, LogIn, Palette, Smartphone, UserRound } from "lucide-react";

import { useAccount } from "@/components/auth/account-context";
import { SignOutMenuItem } from "@/components/auth/sign-out";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { roleLabel, type Account } from "@/lib/auth/account-display";
import { isStaff } from "@/lib/auth/routes";

function AvatarCircle({ account }: { account?: Account | null }) {
  return (
    <span className="flex size-8 items-center justify-center rounded-full bg-surface-3 font-mono text-[12px] font-semibold tracking-tight ring-1 ring-border-strong">
      {account ? account.initials : <UserRound className="size-4 text-muted-foreground" />}
    </span>
  );
}

/** The admin's account menu: who's signed in, the other apps, and Log out. */
function UserMenu() {
  return (
    <Suspense
      fallback={
        <Button variant="ghost" size="icon-sm" aria-label="Account menu" className="rounded-full" disabled>
          <AvatarCircle />
        </Button>
      }
    >
      <AccountMenu />
    </Suspense>
  );
}

function AccountMenu() {
  const account = useAccount();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={account ? `Account menu for ${account.name}` : "Account menu"}
          className="rounded-full"
        >
          <AvatarCircle account={account} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        {account ? (
          <DropdownMenuLabel className="flex flex-col gap-1">
            <span className="truncate">{account.name}</span>
            <span className="truncate text-xs font-normal text-muted-foreground">{account.email}</span>
            <span className="text-xs font-normal text-muted-foreground">{roleLabel(account.role)}</span>
          </DropdownMenuLabel>
        ) : (
          // No Supabase settings yet: a demo preview, where anyone with the link can look around.
          <DropdownMenuLabel className="flex flex-col gap-1">
            <span>Preview mode</span>
            <span className="text-xs font-normal text-muted-foreground">
              You&apos;re looking at the admin with demo data. Sign in works once Supabase is connected.
            </span>
          </DropdownMenuLabel>
        )}
        <DropdownMenuSeparator />
        {!account || isStaff(account.role) ? (
          <>
            <DropdownMenuItem asChild>
              <Link href="/dashboard">
                <Smartphone />
                Creator app
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/styleguide">
                <Palette />
                Design system
              </Link>
            </DropdownMenuItem>
          </>
        ) : null}
        <DropdownMenuItem asChild>
          <Link href="/">
            <ArrowUpRight />
            Public site
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {account ? (
          <SignOutMenuItem />
        ) : (
          <DropdownMenuItem asChild>
            <Link href="/login">
              <LogIn />
              Sign in
            </Link>
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { UserMenu };

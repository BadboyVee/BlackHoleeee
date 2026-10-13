"use client";

import { createContext, use } from "react";

import type { Account } from "@/lib/auth/account-display";

/*
 * The signed-in account for Client Components, following the Next.js pattern
 * for Cache Components: the server starts the lookup once (AccountScope) and
 * hands the promise down; each component that needs the account unwraps it
 * inside its own <Suspense> boundary, so the rest of the page never waits.
 */

const AccountContext = createContext<Promise<Account | null> | null>(null);

export function AccountProvider({ accountPromise, children }: { accountPromise: Promise<Account | null>; children: React.ReactNode }) {
  return <AccountContext value={accountPromise}>{children}</AccountContext>;
}

/**
 * The signed-in account, or null when nobody is (or Supabase isn't set up,
 * on a demo preview). Suspends until it's known: always call it inside a
 * <Suspense> boundary of its own.
 */
export function useAccount(): Account | null {
  const promise = use(AccountContext);
  return promise ? use(promise) : null;
}

/** The account's first name, or `fallback` (the demo creator's) when nobody is signed in. Needs a <Suspense> boundary. */
export function AccountFirstName({ fallback }: { fallback: string }) {
  const account = useAccount();
  return <>{account?.firstName ?? fallback}</>;
}

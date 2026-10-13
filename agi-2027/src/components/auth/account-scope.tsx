import { getAccount } from "@/lib/auth/account";

import { AccountProvider } from "./account-context";

/**
 * Starts the account lookup for an app's layout without waiting for it.
 * Render it inside a <Suspense> boundary (the lookup reads the session
 * cookie); it never suspends itself, so everything inside still prerenders.
 * Components that read the account suspend in their own boundaries.
 */
export function AccountScope({ children }: { children: React.ReactNode }) {
  return <AccountProvider accountPromise={getAccount()}>{children}</AccountProvider>;
}

import { Suspense } from "react";
import type { Metadata } from "next";
import { connection } from "next/server";

import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { InvitesScreen } from "@/components/admin/invites/invites-screen";
import { InvitesSkeleton } from "@/components/admin/invites/invites-skeleton";
import { toInviteViews } from "@/components/admin/invites/invite-view";
import { DEMO_ONBOARDING_NOW, demoInvites } from "@/lib/creators/demo";
import { listInvites } from "@/lib/creators/queries";
import { getSupabaseEnv } from "@/lib/supabase/env";

export const metadata: Metadata = { title: "Invites" };

/**
 * Invite links: anyone who signs up through one is approved straight away.
 * Admin only (the proxy sends the team elsewhere, and RLS hides the rows).
 * The header prerenders; the links read the session, so they stream in.
 */
export default function InvitesPage() {
  return (
    <>
      <AdminPageHeader
        title="Invites"
        description="Links that approve new creators straight away. Share them only with people you'd approve."
      />
      <Suspense fallback={<InvitesSkeleton />}>
        <Invites />
      </Suspense>
    </>
  );
}

async function Invites() {
  // A preview link without Supabase: sample links on the demo clock, and nothing is saved.
  if (!getSupabaseEnv()) {
    return <InvitesScreen invites={toInviteViews(demoInvites, new Date(DEMO_ONBOARDING_NOW))} preview />;
  }

  // Null means nobody is signed in: the proxy sends them to sign in, so this is only a fallback.
  const rows = (await listInvites()) ?? [];
  // Each link's status depends on the time of this request.
  await connection();
  return <InvitesScreen invites={toInviteViews(rows, new Date())} />;
}

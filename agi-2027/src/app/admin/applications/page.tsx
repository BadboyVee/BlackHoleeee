import { Suspense } from "react";
import type { Metadata } from "next";

import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ApplicationList } from "@/components/admin/applications/application-list";
import { ApplicationsSkeleton } from "@/components/admin/applications/applications-skeleton";
import { applicationTabFrom } from "@/components/admin/applications/tabs";
import { NoteBanner } from "@/components/auth/parts";
import { firstParam } from "@/lib/auth/search-params";
import { demoApplications } from "@/lib/creators/demo";
import { listApplications } from "@/lib/creators/queries";
import { getSupabaseEnv } from "@/lib/supabase/env";

export const metadata: Metadata = { title: "Applications" };

/**
 * Staff approve or reject creator applications here, with private notes. The
 * header prerenders; the list reads the session, so it streams in.
 */
export default function ApplicationsPage({ searchParams }: PageProps<"/admin/applications">) {
  return (
    <>
      <AdminPageHeader title="Applications" description="Approve or reject new creators. Notes stay private to the team." />
      <Suspense fallback={<ApplicationsSkeleton />}>
        <Applications searchParams={searchParams} />
      </Suspense>
    </>
  );
}

async function Applications({ searchParams }: Pick<PageProps<"/admin/applications">, "searchParams">) {
  const initialTab = applicationTabFrom(firstParam(await searchParams, "status"));

  // A preview link without Supabase: sample applications, and nothing is saved.
  if (!getSupabaseEnv()) {
    return (
      <div className="grid max-w-5xl grid-cols-1 gap-5">
        <NoteBanner
          note={{ tone: "info", text: "Sample applications. Accounts aren't connected yet, so nothing you decide here is saved or sent." }}
        />
        <ApplicationList rows={demoApplications} initialTab={initialTab} preview />
      </div>
    );
  }

  // Null means nobody is signed in: the proxy sends them to sign in, so this is only a fallback.
  const rows = (await listApplications()) ?? [];
  return <ApplicationList rows={rows} initialTab={initialTab} />;
}

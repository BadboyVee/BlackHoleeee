import { Suspense } from "react";
import type { Metadata } from "next";
import Link from "next/link";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { AuthHeading, NoteBanner } from "@/components/auth/parts";
import { SignOutButton } from "@/components/auth/sign-out";
import { ApplicationForm } from "@/components/onboarding/application-form";
import { ApplicationStatusView } from "@/components/onboarding/application-status";
import { Button } from "@/components/ui/button";
import { getAccount } from "@/lib/auth/account";
import { nameFromEmail } from "@/lib/auth/account-display";
import { firstParam } from "@/lib/auth/search-params";
import { getMyApplication } from "@/lib/creators/queries";
import { getSupabaseEnv } from "@/lib/supabase/env";

export const metadata: Metadata = {
  title: "Your application",
  robots: { index: false, follow: false },
};

/** A referral code from the link that brought them here (/apply?ref= passes it on). */
function referralFrom(value: string | null): string {
  const code = value?.trim().toLowerCase() ?? "";
  return /^[a-f0-9]{8}$/.test(code) ? code : "";
}

/**
 * Where new accounts land: they start as applicants. With no application yet
 * it's the form; after that, where it stands. The proxy moves people on to
 * the creator app once they're approved.
 */
export default function ApplicationPage({ searchParams }: PageProps<"/application">) {
  return (
    <Suspense fallback={<AuthFormSkeleton title="Your application" fields={6} />}>
      <Application searchParams={searchParams} />
    </Suspense>
  );
}

async function Application({ searchParams }: Pick<PageProps<"/application">, "searchParams">) {
  const params = await searchParams;
  const referralCode = referralFrom(firstParam(params, "ref"));

  // A preview link without Supabase: the form can be tried, and ?preview= shows each status.
  if (!getSupabaseEnv()) {
    const preview = firstParam(params, "preview");
    if (preview === "submitted" || preview === "rejected" || preview === "approved") {
      return (
        <ApplicationStatusView status={preview} createdAt="2026-11-03T08:12:00Z" firstName="Amara" email="amara@example.com" />
      );
    }
    return (
      <div className="grid gap-8">
        <ApplicationHeading />
        <NoteBanner note={{ tone: "info", text: "Preview: accounts aren't connected yet, so nothing you send here is saved." }} />
        <ApplicationForm defaultName="" referralCode={referralCode} previewOnly />
      </div>
    );
  }

  const [account, application] = await Promise.all([getAccount(), getMyApplication()]);
  if (!account) {
    return (
      <div className="grid gap-6">
        <AuthHeading eyebrow="For creators" title="Your application" lead="Sign in to apply, or to see where your application stands." />
        <Button asChild size="xl" variant="brand" className="w-full">
          <Link href={`/login?next=${encodeURIComponent("/application")}`}>Sign in</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="grid gap-8">
      {application ? (
        <ApplicationStatusView
          status={application.status}
          createdAt={application.createdAt}
          firstName={account.firstName}
          email={account.email}
        />
      ) : (
        <>
          <ApplicationHeading firstName={account.firstName} />
          {/* The account's name falls back to the start of the email: not a name to suggest. */}
          <ApplicationForm
            defaultName={account.name === nameFromEmail(account.email) ? "" : account.name}
            referralCode={referralCode}
          />
        </>
      )}
      <div className="flex justify-center">
        <SignOutButton />
      </div>
    </div>
  );
}

function ApplicationHeading({ firstName }: { firstName?: string }) {
  return (
    <AuthHeading
      eyebrow="Apply as a creator"
      title={firstName ? `Tell us about you, ${firstName}` : "Tell us about you"}
      lead="About five minutes. We read every application ourselves."
    />
  );
}

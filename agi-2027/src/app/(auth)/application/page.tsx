import { Suspense } from "react";
import type { Metadata } from "next";
import { Sparkles } from "lucide-react";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { AuthHeading } from "@/components/auth/parts";
import { SignOutButton } from "@/components/auth/sign-out";
import { ComingSoon } from "@/components/layout/coming-soon";
import { EmailUs } from "@/components/layout/email-us";
import { getAccount } from "@/lib/auth/account";

export const metadata: Metadata = {
  title: "Your application",
  robots: { index: false, follow: false },
};

/**
 * Where new accounts land: they start as applicants. Milestone 4 puts the
 * application form and its live status here; the proxy moves people on
 * once they're approved.
 */
export default function ApplicationPage() {
  return (
    <Suspense fallback={<AuthFormSkeleton title="Your application" fields={0} />}>
      <Application />
    </Suspense>
  );
}

async function Application() {
  const account = await getAccount();
  return (
    <div className="grid gap-6">
      <AuthHeading
        eyebrow={account ? "Your application" : "For creators"}
        title={account ? `Welcome, ${account.firstName}` : "Your application"}
        lead={account ? `You're signed in as ${account.email}.` : "Sign in to see where your application stands."}
      />
      <ComingSoon
        icon={Sparkles}
        title="The creator application opens here soon"
        description="You'll tell us about your audience, your best posts and why you want in. We'll email you the moment it's ready. In a hurry? Email us your X handle."
        milestone={4}
        action={<EmailUs label="Email us your X handle" subject="Creator application" />}
      />
      {account ? (
        <div className="flex justify-center">
          <SignOutButton />
        </div>
      ) : null}
    </div>
  );
}

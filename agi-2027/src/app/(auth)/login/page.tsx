import type { Metadata } from "next";
import { LogIn } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { EmailUs } from "@/components/layout/email-us";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AGI 2027 to see campaigns, claims and earnings.",
  robots: { index: false, follow: true },
};

export default function LoginPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="text-center">
        <p className="text-label text-brand-text">Welcome back</p>
        <h1 className="mt-3 text-h2">Sign in</h1>
        <p className="mx-auto mt-2.5 max-w-sm text-pretty text-muted-foreground">Sign in with Google in one tap, or with your email and password.</p>
      </div>
      <ComingSoon
        icon={LogIn}
        title="Sign in is on its way"
        description="Accounts open here soon, with Google or email. Until then, email us and we'll help."
        milestone={3}
        action={<EmailUs label="Email us" subject="Signing in to AGI 2027" />}
      />
    </div>
  );
}

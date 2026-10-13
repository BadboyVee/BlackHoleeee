import type { Metadata } from "next";
import { UserPlus } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { EmailUs } from "@/components/layout/email-us";

export const metadata: Metadata = {
  title: "Create your account",
  description: "Create an AGI 2027 account to apply as a creator and claim campaigns.",
  robots: { index: false, follow: true },
};

export default function SignupPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="text-center">
        <p className="text-label text-brand-text">Join AGI 2027</p>
        <h1 className="mt-3 text-h2">Create your account</h1>
        <p className="mx-auto mt-2.5 max-w-sm text-pretty text-muted-foreground">Create an account with Google or email to apply as a creator.</p>
      </div>
      <ComingSoon
        icon={UserPlus}
        title="Sign up is on its way"
        description="Accounts open here soon, with Google or email. Want in now? Email us your X handle."
        milestone={3}
        action={<EmailUs label="Email us to join" subject="Joining AGI 2027" />}
      />
    </div>
  );
}

import type { Metadata } from "next";
import { UserPlus } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Create your account" };

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
        description="Create an account with Google in one tap, or with email and a verified address."
        milestone={3}
      />
    </div>
  );
}

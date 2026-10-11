import type { Metadata } from "next";
import { KeyRound } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Reset your password" };

export default function ForgotPasswordPage() {
  return (
    <div className="flex flex-col gap-8">
      <div className="text-center">
        <p className="text-label text-brand-text">Forgot it?</p>
        <h1 className="mt-3 text-h2">Reset your password</h1>
        <p className="mx-auto mt-2.5 max-w-sm text-pretty text-muted-foreground">We&apos;ll email you a link to set a new password.</p>
      </div>
      <ComingSoon
        icon={KeyRound}
        title="Password reset is on its way"
        description="Enter your email and we'll send a secure reset link."
        milestone={3}
      />
    </div>
  );
}

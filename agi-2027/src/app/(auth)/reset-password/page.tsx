import type { Metadata } from "next";

import { ResetPasswordForm } from "@/components/auth/password-forms";

export const metadata: Metadata = {
  title: "Pick a new password",
  description: "Set a new password for your AGI 2027 account.",
  robots: { index: false, follow: false },
};

/** Opened from a reset link, which signs the person in for this. The proxy sends everyone else to ask for a link. */
export default function ResetPasswordPage() {
  return <ResetPasswordForm />;
}

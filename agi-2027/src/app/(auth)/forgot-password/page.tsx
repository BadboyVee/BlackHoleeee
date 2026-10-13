import { Suspense } from "react";
import type { Metadata } from "next";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { ForgotPasswordForm } from "@/components/auth/password-forms";
import { authPageParams } from "@/lib/auth/search-params";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: "Reset your password",
  description: "Reset the password for your AGI 2027 account.",
  robots: { index: false, follow: true },
};

export default function ForgotPasswordPage({ searchParams }: PageProps<"/forgot-password">) {
  return (
    <Suspense fallback={<AuthFormSkeleton title="Reset your password" fields={1} />}>
      <ForgotPassword searchParams={searchParams} />
    </Suspense>
  );
}

async function ForgotPassword({ searchParams }: Pick<PageProps<"/forgot-password">, "searchParams">) {
  const { note } = authPageParams(await searchParams, siteConfig.contactEmail);
  return <ForgotPasswordForm note={note} />;
}

import { Suspense } from "react";
import type { Metadata } from "next";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { SignUpForm } from "@/components/auth/sign-up-form";
import { enabledProviders } from "@/lib/auth/providers";
import { authPageParams } from "@/lib/auth/search-params";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: "Create your account",
  description: "Create an AGI 2027 account to apply as a creator and claim campaigns.",
  robots: { index: false, follow: true },
};

export default function SignupPage({ searchParams }: PageProps<"/signup">) {
  return (
    <Suspense fallback={<AuthFormSkeleton title="Create your account" fields={3} />}>
      <Signup searchParams={searchParams} />
    </Suspense>
  );
}

async function Signup({ searchParams }: Pick<PageProps<"/signup">, "searchParams">) {
  const [params, providers] = await Promise.all([searchParams, enabledProviders()]);
  const { next, note } = authPageParams(params, siteConfig.contactEmail);
  return <SignUpForm googleEnabled={providers.google} next={next} note={note} />;
}

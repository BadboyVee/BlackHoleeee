import { Suspense } from "react";
import type { Metadata } from "next";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { SignInForm } from "@/components/auth/sign-in-form";
import { enabledProviders } from "@/lib/auth/providers";
import { authPageParams } from "@/lib/auth/search-params";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to AGI 2027 to see campaigns, claims and earnings.",
  robots: { index: false, follow: true },
};

/** The form reads ?next= and ?status= on the server, so it's in the page's HTML and works before JavaScript loads. */
export default function LoginPage({ searchParams }: PageProps<"/login">) {
  return (
    <Suspense fallback={<AuthFormSkeleton title="Sign in" />}>
      <Login searchParams={searchParams} />
    </Suspense>
  );
}

async function Login({ searchParams }: Pick<PageProps<"/login">, "searchParams">) {
  const [params, providers] = await Promise.all([searchParams, enabledProviders()]);
  const { next, note } = authPageParams(params, siteConfig.contactEmail);
  return <SignInForm googleEnabled={providers.google} next={next} note={note} />;
}

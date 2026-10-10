import type { Metadata } from "next";
import { LogIn } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Sign in" };

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
        description="Google and email sign-in, with sessions that stay signed in across visits."
        milestone={3}
      />
    </div>
  );
}

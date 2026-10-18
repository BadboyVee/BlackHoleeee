import { Suspense } from "react";
import type { Metadata } from "next";

import { AuthFormSkeleton } from "@/components/auth/form-skeleton";
import { NoteBanner } from "@/components/auth/parts";
import {
  InviteAccept,
  InviteAccountInactive,
  InviteAlreadyIn,
  InviteCheckFailed,
  InviteUnusable,
  InviteWelcome,
} from "@/components/onboarding/invite-view";
import { getAccount } from "@/lib/auth/account";
import { firstParam } from "@/lib/auth/search-params";
import { parseInviteCode } from "@/lib/creators/display";
import { inviteState } from "@/lib/creators/queries";
import { getSupabaseEnv } from "@/lib/supabase/env";

export const metadata: Metadata = {
  title: "You're invited",
  robots: { index: false, follow: false },
};

/** The code from the address, decoded. Invalid percent-encoding won't match a code either way. */
function decoded(raw: string): string {
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

/**
 * An invite link: whoever opens it can join as a creator without waiting for
 * review. Signed out, it's the way into sign up or sign in (both come back
 * here); signed in as an applicant, it's one button. Open to everyone: the
 * proxy only refreshes the session here, and the database decides whether a
 * code works.
 */
export default function InvitePage({ params, searchParams }: PageProps<"/invite/[code]">) {
  return (
    <Suspense fallback={<AuthFormSkeleton title="You're invited" fields={0} />}>
      <Invite params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function Invite({ params, searchParams }: PageProps<"/invite/[code]">) {
  // Anything but 16 hex characters is unknown without asking the database.
  const code = parseInviteCode(decoded((await params).code));
  if (!code) return <InviteUnusable state="unknown" />;

  // A preview link without Supabase: any well-formed code works, and ?preview= shows the other cases.
  if (!getSupabaseEnv()) return <InvitePreview code={code} preview={firstParam(await searchParams, "preview")} />;

  const [state, account] = await Promise.all([inviteState(code), getAccount()]);

  // Creators and staff have nothing to accept, whatever state the link is in.
  if (account && account.role !== "applicant") {
    if (account.role === "none") return <InviteAccountInactive code={code} email={account.email} />;
    return <InviteAlreadyIn role={account.role} email={account.email} />;
  }

  if (state === null) return <InviteCheckFailed code={code} />;
  if (state !== "valid") return <InviteUnusable state={state} applyHref={account ? "/application" : "/apply"} />;
  if (!account) return <InviteWelcome code={code} />;
  return <InviteAccept code={code} firstName={account.firstName} email={account.email} />;
}

const PREVIEW_NOTE = (
  <NoteBanner note={{ tone: "info", text: "Preview: accounts aren't connected yet, so this is sample data and nothing is saved." }} />
);

/** Sample views for preview links, where nobody can sign in. */
function InvitePreview({ code, preview }: { code: string; preview: string | null }) {
  const sample = { firstName: "Jesse", email: "jesse@example.com" };
  switch (preview) {
    case "applicant":
      return <InviteAccept code={code} {...sample} note={PREVIEW_NOTE} />;
    case "creator":
    case "admin":
      return <InviteAlreadyIn role={preview} email={sample.email} note={PREVIEW_NOTE} />;
    case "inactive":
      return <InviteAccountInactive code={code} email={sample.email} note={PREVIEW_NOTE} />;
    case "revoked":
    case "expired":
    case "used_up":
      return <InviteUnusable state={preview} note={PREVIEW_NOTE} />;
    case "error":
      return <InviteCheckFailed code={code} note={PREVIEW_NOTE} />;
    default:
      return <InviteWelcome code={code} note={PREVIEW_NOTE} />;
  }
}

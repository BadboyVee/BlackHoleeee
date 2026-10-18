import { Suspense } from "react";
import type { Metadata } from "next";
import Link from "next/link";

import { NoteBanner } from "@/components/auth/parts";
import { ProfileScreen } from "@/components/creator/profile/profile-screen";
import { ProfileSkeleton } from "@/components/creator/profile/profile-skeleton";
import { Button } from "@/components/ui/button";
import { isStaff, parseRoleClaim } from "@/lib/auth/routes";
import { demoPayoutDetails, demoProfile, demoReferrals } from "@/lib/creators/demo";
import { referralLink } from "@/lib/creators/display";
import { getMyPayoutDetails, getMyProfile, getMyReferrals } from "@/lib/creators/queries";
import { getSupabaseEnv } from "@/lib/supabase/env";

export const metadata: Metadata = { title: "Profile" };

/**
 * The creator's own profile, payout details and referral link. The header
 * prerenders; everything that reads the session streams in behind it.
 */
export default function ProfilePage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="pt-2 sm:pt-4">
        <h1 className="text-h2">Profile</h1>
        <p className="mt-2 text-[15px] text-pretty text-muted-foreground sm:text-base">
          Your details, where we pay you, and your link for bringing in other creators.
        </p>
      </header>
      <Suspense fallback={<ProfileSkeleton />}>
        <Profile />
      </Suspense>
    </div>
  );
}

async function Profile() {
  const env = getSupabaseEnv();

  // A preview link without Supabase: sample data, and the forms say nothing is saved.
  if (!env) {
    return (
      <div className="flex flex-col gap-8">
        <NoteBanner
          note={{ tone: "info", text: "Preview: this is sample data. Accounts aren't connected yet, so nothing you change here is saved." }}
        />
        <ProfileScreen
          profile={demoProfile}
          payout={demoPayoutDetails}
          referrals={demoReferrals}
          referralUrl={demoProfile.referralCode ? referralLink(demoProfile.referralCode) : null}
          supabaseUrl={null}
          mode="preview"
        />
      </div>
    );
  }

  const [profile, payout, referrals] = await Promise.all([getMyProfile(), getMyPayoutDetails(), getMyReferrals()]);

  if (!profile) {
    return (
      <div className="flex flex-col items-start gap-4">
        <NoteBanner
          className="w-full"
          note={{ tone: "error", text: "We couldn't load your profile. Refresh the page, or sign in again if it keeps happening." }}
        />
        <Button asChild size="lg" variant="secondary">
          <Link href={`/login?next=${encodeURIComponent("/dashboard/profile")}`}>Sign in again</Link>
        </Button>
      </div>
    );
  }

  const creator = profile.role === "creator";
  const staff = isStaff(parseRoleClaim(profile.role));

  return (
    <div className="flex flex-col gap-8">
      {creator ? null : (
        <NoteBanner
          note={{
            tone: "info",
            text: staff
              ? "This page is for creators. You're signed in as staff, so you can look around but not change anything."
              : "This page is for approved creators, so nothing here can be changed yet.",
          }}
        />
      )}
      <ProfileScreen
        profile={profile}
        payout={payout}
        referrals={referrals}
        referralUrl={profile.referralCode ? referralLink(profile.referralCode) : null}
        supabaseUrl={env.url}
        mode={creator ? "edit" : "look"}
        staff={staff}
      />
    </div>
  );
}

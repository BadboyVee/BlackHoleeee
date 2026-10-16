import { Link2 } from "lucide-react";

import type { CreatorProfile, PayoutDetails } from "@/lib/creators/queries";

import { AvatarPicker } from "./avatar-picker";
import { PayoutForm } from "./payout-form";
import { PayoutSummary } from "./payout-summary";
import { ProfileForm, type ProfileFormProfile } from "./profile-form";
import { ProfilePanel } from "./profile-panel";
import { ReferralLink } from "./referral-link";

/**
 * How the page can be used:
 *   edit     an approved creator, their own profile
 *   look     staff (or anyone who isn't a creator) opening the creator app: everything shows, nothing changes
 *   preview  no Supabase yet: sample data, the forms can be tried, nothing is saved
 */
export type ProfileMode = "edit" | "look" | "preview";

/** The three sections of the creator's profile page, in order: profile, payout details, referral link. */
export function ProfileScreen({
  profile,
  payout,
  referrals,
  referralUrl,
  supabaseUrl,
  mode,
  staff = false,
}: {
  profile: CreatorProfile;
  payout: PayoutDetails | null;
  referrals: { applied: number; approved: number } | null;
  /** The full referral link, built on the server (the site's address is server config). */
  referralUrl: string | null;
  /** The Supabase project's address, for the photo upload. Null on a preview. */
  supabaseUrl: string | null;
  mode: ProfileMode;
  /** Staff looking: the referral section explains links are for creators. */
  staff?: boolean;
}) {
  const locked = mode === "look";
  const previewOnly = mode === "preview";
  // Only what the form needs crosses to the browser.
  const details: ProfileFormProfile = {
    displayName: profile.displayName,
    xHandle: profile.xHandle,
    tiktokUrl: profile.tiktokUrl,
    youtubeUrl: profile.youtubeUrl,
    instagramUrl: profile.instagramUrl,
    linkedinUrl: profile.linkedinUrl,
    niches: profile.niches,
    followers: profile.followers,
    avgViews: profile.avgViews,
    country: profile.country,
    bio: profile.bio,
    ratePerPost: profile.ratePerPost,
    rateCurrency: profile.rateCurrency,
  };

  return (
    <div className="flex flex-col gap-10">
      <ProfilePanel id="profile-details" title="Photo and profile" description="How you show up to the agency. Keep it up to date.">
        <AvatarPicker
          userId={profile.id}
          name={profile.displayName}
          handle={profile.xHandle}
          avatarUrl={profile.avatarUrl}
          supabaseUrl={supabaseUrl}
          locked={locked}
          lockedNote={previewOnly ? "Photos can be changed once accounts are connected." : undefined}
        />
        <div className="my-7 border-t sm:my-8" />
        <ProfileForm profile={details} locked={locked} previewOnly={previewOnly} />
      </ProfilePanel>

      <ProfilePanel id="payout-details" title="Payout details" description="Where we send your earnings.">
        <div className="grid gap-6">
          {payout ? (
            <PayoutSummary payout={payout} />
          ) : locked ? null : (
            <p className="text-sm text-pretty text-muted-foreground">
              No payout details yet. Add them below so we know where to send your earnings.
            </p>
          )}
          <PayoutForm payout={payout} locked={locked} previewOnly={previewOnly} />
        </div>
      </ProfilePanel>

      <ProfilePanel id="referral-link" title="Referral link" description="Your personal link for bringing in other creators.">
        {profile.referralCode && referralUrl ? (
          <ReferralLink link={referralUrl} counts={referrals} />
        ) : (
          <div className="flex items-start gap-3.5">
            <span
              aria-hidden
              className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-muted-foreground"
            >
              <Link2 className="size-[18px]" />
            </span>
            <div className="min-w-0 text-sm leading-relaxed">
              <p className="font-medium text-foreground">
                {staff ? "Referral links are for creators" : "Your link appears once you're approved"}
              </p>
              <p className="mt-0.5 text-pretty text-muted-foreground">
                {staff
                  ? "Each creator gets a personal link here once they're approved."
                  : "Every approved creator gets a personal link to share. Applications through it show you sent them."}
              </p>
            </div>
          </div>
        )}
      </ProfilePanel>
    </div>
  );
}

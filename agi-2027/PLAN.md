# AGI 2027 build plan

**Status:** proposed, waiting for OK · 10 Oct 2026

What we're building is in [SPEC.md](SPEC.md). This file covers how it gets built, and it's
updated at the end of every milestone.

## Working setup

- **Code:** this folder, `agi-2027/` (see [open question 1](#open-questions) about a private
  repo).
- **Testing on your phone:** Vercel builds a preview link for every push. Each milestone ends with
  a link and a short list of things to test. That's why Vercel gets connected in Milestone 1
  instead of at launch.
- **Two Supabase projects:** *dev* now (demo data; this build environment can reach it) and
  *production* at launch (only Vercel holds its keys, so real creator data never sits in a dev
  environment).
- **Database changes are code:** SQL migrations in `supabase/migrations/`, never clicks in the
  dashboard. I apply them to dev; at launch a GitHub Action applies them to production.
- **This build environment** currently can't reach Supabase, Resend, Telegram or X. Everything
  that doesn't need them gets built and tested here (database logic runs against a local
  Postgres). Opening just the hosts we need is part of the walkthrough for each milestone.

## Stack

As specified, no changes proposed: Next.js 16 (App Router, TypeScript, React 19), Supabase
(`@supabase/ssr`), Tailwind CSS 4, shadcn/ui, Motion (Framer Motion's new name), Lucide, React
Three Fiber, React Hook Form and Zod, Resend with React Email, react-tweet, next-themes, Vitest,
and Playwright.

## Key decisions

1. **The database enforces the rules, not just the screens.** RLS on every table. Every step of
   the loop (claim, accept, submit a draft or proof, approve, reject, expire, mark paid) is one
   Postgres function running in one transaction. It checks who is calling and whether the move is
   allowed, then writes the status timeline and the activity log. Nobody can skip a step by
   calling the API directly.
2. **Claiming is race-safe.** The claim function locks the campaign row, counts the slots, and
   inserts the claim in one transaction. A unique key blocks a second claim by the same creator.
   If 40 creators tap Claim on a 10-slot campaign at the same moment, exactly 10 get it and 30
   see "Full".
3. **Hidden fields live in separate tables.** RLS hides rows, not columns. So budget, admin notes,
   audience rules, tier payouts and the report token are in `campaign_internal`. Tiers, tags and
   private notes on creators are in `creator_internal`. Creators read slot counts from a counter
   on the campaign, never from other creators' claims. The public `/campaigns` board reads through
   a function that returns only safe fields (no payout).
4. **Nobody can promote themselves.** Users can update only their own profile fields. Role,
   status and referral code are locked at the database level (column privileges), so even a
   hand-crafted request can't make someone team or admin.
5. **Scheduler: Supabase Cron, every minute.** It drops scheduled campaigns, expires claims past
   the proof deadline, and queues reminders. (Vercel's free plan runs cron jobs only once a day.)
6. **Email and Telegram go through an outbox.** An action writes a message row, and a worker
   sends it with retries. If Resend or Telegram is down, the alert is delayed instead of lost, and
   the action that triggered it still succeeds.
7. **Live updates** come through Supabase Realtime on claims, the review queue and
   notifications. RLS also limits what each person receives.
8. **Proof links are normalized to platform + post ID.** That way `twitter.com/a/status/1` and
   `x.com/a/status/1?s=20` count as the same post in the duplicate check. X post data (author,
   time, text, links) comes free from the public endpoint react-tweet uses. Failed checks show as
   flags on the review card, never as automatic rejections. If X doesn't answer, the card says
   "check manually".
9. **Money** is stored as exact decimals, never floats, with a currency on every row. Every total
   is grouped by currency. Earnings are append-only: a correction is a deduction, not an edit.
   Each claim freezes its payout at claim time, so editing a campaign later never changes what
   someone already signed up for. A payout records the wallet or bank details it was sent to.
10. **Times** are stored in UTC and shown in the viewer's local time plus UTC. Each profile keeps
    a time zone (detected automatically) so emails can show local time too.
11. **Files:** a public bucket for avatars and brand logos. Campaign assets and proof screenshots
    go in private buckets with short-lived links; asset links go only to creators who can see the
    campaign.
12. **Abuse protection:** rate limits are stored in Postgres (no extra account), on top of
    Supabase Auth's own sign-in limits. Public forms get a honeypot and a minimum fill time.
    Turnstile can be switched on later.
13. **Tests:** the database functions are tested against a real Postgres: simultaneous claims,
    every allowed and forbidden status move, expiry, payouts, and per-currency totals. There are
    also unit tests for link parsing and money math, plus a Playwright run through the whole loop.
    All of them run on GitHub Actions on every push. Each test is written in the milestone that
    builds the logic, not saved for the end.

## Pages

**Public**

- `/` home: the 10 sections, in order
- `/campaigns` open campaigns teaser, payout hidden
- `/book` Book a campaign
- `/apply` the creator pitch, then sign up and the application form (`?ref=CODE` carries a
  referral)
- `/invite/[code]` invite landing: sign up and skip the queue
- `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/auth/callback`
- `/terms`, `/privacy`
- `/report/[token]` client report, no login
- `sitemap.xml`, `robots.txt`, Open Graph images

**Applicant**

- `/application`: the form until it's submitted, then its live status

**Creator portal** (bottom tab bar on mobile, sidebar on desktop)

- `/dashboard` home
- `/dashboard/campaigns` board and `/dashboard/campaigns/[id]` campaign page (brief, claim, draft,
  proof, metrics, timeline)
- `/dashboard/my-campaigns` with Active, Submitted, Approved, Paid and Past tabs
- `/dashboard/earnings`
- `/dashboard/notifications`
- `/dashboard/profile`: profile, payout details, referral link, email preferences

**Admin** (team can open everything except the ★ pages)

- `/admin` overview
- `/admin/campaigns`, `/admin/campaigns/new`, `/admin/campaigns/[id]` (roster and bulk actions),
  `/admin/campaigns/[id]/edit`
- `/admin/review`
- `/admin/creators` and `/admin/creators/[id]`
- `/admin/applications`
- `/admin/invites` ★
- `/admin/payouts` ★
- `/admin/clients` and `/admin/clients/[id]`
- `/admin/leads`
- `/admin/content` (site content)
- `/admin/team` ★
- `/admin/settings` ★
- `/admin/activity`
- `/admin/notifications`

## Database

The spec's tables, plus a few additions (marked **+**). RLS on all of them.

| Area      | Table                  | Holds                                                                                                                                                                                         |
| --------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| People    | `profiles`             | user id, role (admin, team, creator, applicant), status, name, avatar, X handle, other socials, niches, followers, average views, country, time zone, bio, rate per post, referral code, referred by, email preferences, empty Phase 2 fields for a verified X account |
|           | `creator_internal` +   | tier, tags, private admin notes (staff only)                                                                                                                                                  |
|           | `payout_details`       | method, network, wallet address or bank details (the creator and admin only)                                                                                                                 |
|           | `applications`         | answers, status, referred by, invite used, reviewer, notes                                                                                                                                    |
|           | `invites`              | code, kind (creator link or team invite), created by, uses, max uses, expiry, revoked                                                                                                         |
| Campaigns | `clients`              | name, logo, website, X handle, contacts                                                                                                                                                       |
|           | `campaigns`            | what creators may see: brief, angles, deliverable, platform, links, required tags, base payout and currency, slots and slots taken, claim mode, draft required, label required, times, status |
|           | `campaign_internal` +  | budget, admin notes, audience rules, tier payouts, report token and on/off (staff only)                                                                                                       |
|           | `campaign_targets` +   | hand-picked creators and per-creator payout overrides                                                                                                                                         |
|           | `campaign_assets`      | files and their type, in a private bucket                                                                                                                                                     |
| The loop  | `claims`               | status, frozen payout, assigned angle, post time, request note, deadline override, a timestamp for each status                                                                                |
|           | `claim_events` +       | every status change with who made it and their comment (powers the timeline)                                                                                                                  |
|           | `drafts`               | each version: text, media, status, feedback                                                                                                                                                   |
|           | `submissions`          | each proof attempt: post URL, platform and post ID, screenshot, confirmations, check flags, status, review note                                                                               |
|           | `post_metrics` +       | views, likes, reposts, replies, screenshot, source (manual now, X API in Phase 2), captured at                                                                                                |
| Money     | `earnings`             | creator, claim, type (campaign, bonus, deduction), amount, currency, note, status, payout                                                                                                     |
|           | `payouts`              | creator, amount, currency, method, where it was sent, reference, paid at, recorded by                                                                                                         |
| Comms     | `notifications`        | user, type, message, link, read at                                                                                                                                                            |
|           | `outbox` +             | queued emails and Telegram posts with attempts and errors                                                                                                                                     |
|           | `leads`                | Book a campaign submissions, status (New, Contacted, Won, Lost), notes                                                                                                                        |
| Admin     | `site_content`         | homepage stats, logos, featured posts, services, FAQ                                                                                                                                          |
|           | `settings` +           | agency name, currencies, default campaign rules, reminder timing, email sender, Telegram group (the bot token stays in an environment variable)                                               |
|           | `activity_log`         | who, what, when, details (insert-only)                                                                                                                                                        |
|           | `rate_limits` +        | counters for sign in, applications and the Book form                                                                                                                                          |

**Phase 2 is designed in, not built:** platforms already include TikTok, Instagram, LinkedIn and
YouTube; metrics record their source; profiles have empty fields for a verified X account;
earning types and payout methods can grow (referral bonuses, automatic USDC); the outbox has a
channel field ready for personal Telegram and push alerts.

## Status flows

**Campaign**

```
draft ──publish now──────────────────────────▶ live
draft ──schedule──▶ scheduled ──drop time──▶ live
live ⇄ paused                       admin
live ⇄ full                         automatic, when slots fill up or one reopens
live / full / paused ──▶ closed     no new claims; claims in progress carry on
closed ──▶ completed                admin, once every claim is settled
```

**Claim**

```
tap Claim ─┬─ apply mode ──▶ requested ──accept──▶ claimed
           │                     └──────decline──▶ cancelled
           └─ instant mode ──────────────────────▶ claimed

claimed ──(draft required)──▶ draft submitted ──approve──▶ draft approved ──▶ proof submitted
                                  ▲          └──changes──▶ changes requested
                                  └────────── edit and resubmit ◀──┘
claimed ──(no draft)────────────────────────────────────────────────────────▶ proof submitted

proof submitted ──approve──▶ approved  (earning created as Unpaid) ──payout──▶ paid
proof submitted ──reject with reason──▶ rejected ──fix and resubmit──▶ proof submitted

before the post window: claimed, draft states ──creator drops──▶ cancelled   (slot reopens)
at the proof deadline:  anything without proof in ──────────────▶ expired     (slot reopens)
```

How I read the rules:

- A slot is held from **claimed** until **expired** or **cancelled**. Apply-mode requests don't
  hold a slot, and accepting one fails if the campaign is already full.
- A declined request becomes **cancelled** with a reason. **Rejected** always means "proof
  rejected, fix it before the deadline". Requests still pending at the claim deadline are
  declined automatically.
- Proof submitted before the deadline never expires, even if it hasn't been reviewed yet.
  Rejected proof that isn't fixed by the deadline does expire.
- "Claim each campaign only once": a creator who drops a claim, or lets it expire, can't claim
  that campaign again on their own. Admin can reinstate them.
- Admin can extend one claim's deadline, reinstate an expired claim, cancel any claim, and set
  each creator's angle and post time.

## Milestones

| #  | Milestone          | What you'll be able to test                                                                                                                      | Accounts we set up                                              | Status      |
| -- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- | ----------- |
| 1  | Setup              | Preview link on your phone: light/dark toggle, the design system page (colors, type, buttons, badges, cards, forms, skeletons), empty public, portal and admin layouts | Supabase (dev), Vercel, build environment access                | Not started |
| 2  | Public website     | Full home page with the 3D hero, the open campaigns board from demo data, Book a campaign saving to the database and emailing you                 | Resend (its test sender works until your domain is verified)   | Not started |
| 3  | Accounts           | Google and email sign up, email verification, password reset, log out, routing by role, private pages sending you to login and back, your admin account | Google Cloud OAuth                                              | Not started |
| 4  | Creator onboarding | Apply and watch the status screen; approve or reject; invite links that skip the queue; referral links; profile and payout details with the confirmation email | —                                                               | Not started |
| 5  | Campaigns          | Create, schedule, drop, duplicate, edit, pause and close; creators see only the campaigns meant for them, with local time and UTC                 | —                                                               | Not started |
| 6  | The loop           | Claim (instant and apply), drop a claim, drafts and changes, proof with free checks and the embedded post, review queue with bulk approve, expiry; changes show live on both sides | —                                                               | Not started |
| 7  | Earnings, payouts  | Earnings appear on approval; mark one or many paid with a reference; bonuses and deductions; totals per currency; CSV export                       | —                                                               | Not started |
| 8  | Notifications      | The live bell, every email as a branded template, reminders, email preferences, drops posted to your Telegram group                               | Telegram bot                                                    | Not started |
| 9  | Admin extras       | Overview and chart, creators directory with stats and notes, clients, leads pipeline, site content editor, team invites, activity log            | —                                                               | Not started |
| 10 | Client reports     | Send a private report link, turn it off or regenerate it, print it to PDF                                                                         | —                                                               | Not started |
| 11 | Polish and launch  | Install the portal on your phone, final animation pass, link previews, Lighthouse and accessibility checks, full test suite, production on your domain | Domain, Resend domain, production Supabase and Vercel          | Not started |

Demo data grows with each milestone: one admin, a few creators and applicants, and campaigns
and claims in every status.

## Small calls I made (tell me to change any)

- **Accent: acid lime** on near-black. Violet is what most AI brands already use; lime is more
  memorable and keeps very strong contrast on dark. Light mode uses a deeper lime for text.
  Switching to violet means changing one token.
- **Fonts:** Geist Sans for headings and body, Geist Mono for labels, numbers and the wordmark.
  One free family that loads with no layout shift.
- **Currencies to start:** USD, USDC, USDT and NGN, editable in Settings.
- **Services:** the three from the spec, as placeholders until you confirm the list.
- **Homepage content** (stats, logos, featured posts, FAQ) is seeded with placeholders in M2. The
  editor arrives in M9.
- **Admin only:** payouts, team, settings and invite links, plus suspending or removing creators.
  Team can do everything else, but never sees payout details.
- **Your admin account** comes from a one-time setup step in M3, tied to your email.

## Open questions

1. **Where should the code live?** This repo (BlackHoleeee) is public, and GitHub Pages publishes
   it, so anyone can read the platform's code and this plan. No secrets ever go in the code, so
   it's safe either way. Still, I'd recommend a private repo for the agency. If you agree, create
   an empty private repo (for example `agi-2027`) and I'll move everything there. Otherwise I'll
   keep building in `agi-2027/` here.

## Running costs (at launch, not now)

Development fits the free plans. Launch needs three upgrades:

- **Vercel:** the free plan is for non-commercial use, so the agency site needs Pro.
- **Supabase:** free projects pause when idle and have no backups, so production should be Pro.
- **Resend:** the free plan caps at 100 emails a day. A single drop to a few hundred creators
  would go over that.

Each upgrade costs roughly $20–25 a month. Check current pricing when we get there.

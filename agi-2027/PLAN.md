# AGI 2027 build plan

**Status:** Milestone 3 built 13 Oct 2026 (accounts: Google and email sign in, email
confirmation, password reset, log out, private pages and routing by role, your admin account).
Milestone 2 built 13 Oct 2026 and in review (the public website). Milestone 1 merged 11 Oct
2026. Plan approved 10 Oct 2026.

What we're building is in [SPEC.md](SPEC.md). This file covers how it gets built, and it's
updated at the end of every milestone.

## Working setup

- **Code:** this folder, `agi-2027/`, in the BlackHoleeee repo (decided 10 Oct 2026). The host
  builds from this folder.
- **Hosting: Netlify or Vercel** (you asked about Netlify, 13 Oct 2026). The site runs on both
  and works out which one it's on while building (`src/lib/deploy.ts`). I recommend Netlify: its
  free plan allows a business site, while Vercel's free plan is for non-commercial use only. On
  Netlify, make a new site from this repo with the base directory set to `agi-2027`; the
  `netlify.toml` here does the rest. The repo-root `netlify.toml` belongs to the bmw-m5-cs site
  and stays as it is.
- **Testing on your phone:** the host builds a preview link for every pull request. Each
  milestone ends with a link and a short list of things to test.
- **One pull request per milestone** (agreed 10 Oct 2026). Each milestone arrives as a pull
  request into `main` with its preview link. You test it and merge it; merging updates the live
  site.
- **Two Supabase projects:** *dev* now (demo data) and *production* at launch (only the host and
  GitHub hold its keys, so real creator data never sits in a dev environment).
- **Database changes are code:** SQL migrations in `supabase/migrations/`, never clicks in the
  dashboard. GitHub Actions applies them to dev on every branch push (repository secret
  `DEV_DATABASE_URL`); at launch a second job applies them to production from `main`.
- **Checks on every push:** GitHub Actions runs lint, typecheck, unit tests, database tests
  against a real Postgres, and a production build (`.github/workflows/agi-2027.yml`).
- **This build environment** can't reach Supabase, Resend, Telegram or X, and doesn't need to:
  database logic is tested here against a local Postgres, and the hosted services are checked
  on the preview link. If end-to-end tests against the dev project become worth it (around
  Milestone 6), opening those hosts is a two-minute settings change.

## Stack

As specified: Next.js 16.4 (App Router, TypeScript, React 19), Supabase (`@supabase/ssr`),
Tailwind CSS 4, shadcn/ui-style components on Radix, Motion (Framer Motion's new name), Lucide,
React Hook Form and Zod, Resend with React Email, react-tweet, Vitest, and Playwright. React Three
Fiber is back for two of the three looks (the living painting and Echo, the felt host). It only
loads when that look is showing, after the page has painted, and pauses when scrolled away.

Settled while building Milestone 1:

- **Cache Components and Partial Prefetching are on** (the Next.js 16.4 default). Pages ship a
  static shell instantly and stream personal data in, which makes navigation feel instant.
  The rule that comes with it: anything that reads cookies, the session or the clock sits
  inside a `<Suspense>` boundary.
- **shadcn/ui components are written into the repo by hand.** That's how shadcn works anyway
  (you own the source); the CLI just can't reach its registry from this build environment. Same
  Radix primitives and the same component API.
- **No next-themes.** The theme follows the pattern from the Next.js 16.4 docs: a tiny inline
  script applies the saved choice before first paint, so there's never a flash of the wrong
  theme. Dark is the default and each visitor's choice is remembered on their device.
- **Dates are formatted from parts, never Intl's own pattern.** The server and browsers
  punctuate dates differently ("Tue 12 Jan" vs "Tue, 12 Jan"), which breaks hydration.

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
| 1  | Setup              | Preview link on your phone: light/dark toggle, the design system page (colors, type, buttons, badges, cards, forms, skeletons), empty public, portal and admin layouts | Supabase (dev), Vercel, one GitHub secret                       | Done, merged 11 Oct 2026 |
| 2  | Public website     | Full home page with the 3D hero, the open campaigns board from demo data, Book a campaign saving to the database and emailing you                 | Resend (its test sender works until your domain is verified)   | Built 13 Oct 2026, in review |
| 3  | Accounts           | Google and email sign up, email verification, password reset, log out, routing by role, private pages sending you to login and back, your admin account | Google Cloud OAuth                                              | Built 13 Oct 2026, in review |
| 4  | Creator onboarding | Apply and watch the status screen; approve or reject; invite links that skip the queue; referral links; profile and payout details with the confirmation email | —                                                               | Not started |
| 5  | Campaigns          | Create, schedule, drop, duplicate, edit, pause and close; creators see only the campaigns meant for them, with local time and UTC                 | —                                                               | Not started |
| 6  | The loop           | Claim (instant and apply), drop a claim, drafts and changes, proof with free checks and the embedded post, review queue with bulk approve, expiry; changes show live on both sides | —                                                               | Not started |
| 7  | Earnings, payouts  | Earnings appear on approval; mark one or many paid with a reference; bonuses and deductions; totals per currency; CSV export                       | —                                                               | Not started |
| 8  | Notifications      | The live bell, every email as a branded template, reminders, email preferences, drops posted to your Telegram group                               | Telegram bot                                                    | Not started |
| 9  | Admin extras       | Overview and chart, creators directory with stats and notes, clients, leads pipeline, site content editor, team invites, activity log            | —                                                               | Not started |
| 10 | Client reports     | Send a private report link, turn it off or regenerate it, print it to PDF                                                                         | —                                                               | Not started |
| 11 | Polish and launch  | Install the portal on your phone, final animation pass, link previews, Lighthouse and accessibility checks, full test suite, production on your domain | Domain, Resend domain, production Supabase and hosting         | Not started |

Demo data grows with each milestone: one admin, a few creators and applicants, and campaigns
and claims in every status.

## Small calls I made (tell me to change any)

- **Looks** (your references, 11 Oct 2026): Renaissance, Agent and Drop, switchable from the
  header. **Drop is the default** (you asked me to pick, 11 Oct 2026): it shows what the agency
  does at a glance, a creator's launch post on X, and it loads fastest on phones because it needs
  no 3D. The switcher stays so visitors can find Echo and the painting. Each look has a light and
  a dark mode; light is the default. Changing the default is one line in `src/lib/theme.ts`.
- **Fonts:** Geist for body text and UI, Geist Mono for small labels. Headings follow the look:
  bold Geist (Renaissance), soft Geist (Agent), Anton capitals (Drop).
- **Art:** the paintings are public-domain works from The Met's open-access collection (Poussin,
  Claude Lorrain, Thomas Cole), credited on the page. Echo and the glossy 3D icons are rendered
  from our own code. No artwork, text or logos from the reference sites are used.
- **Currencies to start:** USD, USDC, USDT and NGN, editable in Settings.
- **Services:** the three from the spec, as placeholders until you confirm the list.
- **Featured posts are real** (12 Oct 2026): the five launch posts you sent (Kled, micro1,
  Maincode, Ali Ansari, Hedwig) fill the Drop hero's phone and the proof section, most viewed
  first. Text, numbers and pictures come from your screenshots, each post links to the real one on
  X, and a number that couldn't be read is left out. They live in `src/lib/showcase-posts.ts`
  until the content editor (M9) takes over. The numbers are a snapshot and say so on the page.
  The hero labels each one "Example", because you haven't said whether these were AGI 2027
  campaigns. Confirm it and the labels can say so.
- **Other homepage content** (stats, brand names, FAQ) is still placeholder. The editor arrives in
  M9; send real numbers and client names whenever you have them.
- **Admin only:** payouts, team, settings and invite links, plus suspending or removing creators.
  Team can do everything else, but never sees payout details.
- **Your admin account** comes from a one-time setup step (M3): sign up, then run one line in
  Supabase's SQL editor. It only works while there's no admin, so it can't be used to add a
  second one later. Team members join by invite (M9).
- **Staff can open the creator app** (M3) to see what creators see. Creators and applicants
  can't open the admin.
- **Contact email** (12 Oct 2026): joshhthepluggg@gmail.com is for visitors only, on every "email
  us" link. Nothing automated is sent there; booking alerts go to the inbox you set as
  `LEADS_NOTIFY_EMAIL`.
- **Book a campaign:** name, work email, company and what's launching are required; website, X
  handle, launch date, budget range and a message are optional. Budget ranges: under $5k, $5k to
  $10k, $10k to $25k, $25k+, not sure yet. Each connection can send 5 an hour.
- **Privacy and Terms** are written in plain words from what the site actually does today. They
  name no country's law. Have a lawyer read them before launch.

## Open questions

- Netlify or Vercel? I recommend Netlify (see Working setup). Sign in needs the live address
  for its email links (Milestone 3 setup, step 1).
- Which inbox gets booking alerts (`LEADS_NOTIFY_EMAIL`)? It can't be the contact email.
- Were the five showcase posts AGI 2027 campaigns? If so, the "Example" labels can go.
- Real stats and client names for the home page, whenever you have them.

Decided on 10 Oct 2026: the code stays in this repo. On 11 Oct 2026 the acid lime accent was
replaced by the three looks, with Drop as the default and the switcher kept.

## Running costs (at launch, not now)

Development fits the free plans. Launch needs two or three upgrades:

- **Hosting:** Netlify's free plan allows a business site within a monthly allowance (300
  credits; each live update and visitor traffic use some, and the site pauses if it runs out).
  Vercel's free plan is for non-commercial use, so on Vercel the agency site needs Pro.
- **Supabase:** free projects pause when idle and have no backups, so production should be Pro.
- **Resend:** the free plan caps at 100 emails a day. A single drop to a few hundred creators
  would go over that.

Each upgrade costs roughly $20 to $25 a month. Check current pricing when we get there.

## Milestone 1 · Setup (built 10 Oct 2026)

What's in it:

- **Project:** Next.js 16.4 app in `agi-2027/` with TypeScript, Tailwind CSS 4, ESLint, Vitest,
  security headers, and a README.
- **Design system:** color tokens for dark and light (every text color checked for WCAG AA
  contrast), Geist Sans and Geist Mono, a fluid type scale, grid and grain textures, and soft
  glows. Components: button, badge, status badge, card, input, textarea, field, select,
  checkbox, switch, avatar, dropdown menu, dialog (a bottom sheet on phones), sheet, tabs,
  tooltip, skeleton, toast, empty state, count-up number, live countdown, local time plus UTC,
  and a first campaign card. All of it is on show at `/styleguide`.
- **Light and dark:** dark by default, toggle on every page, remembered per device, no flash.
- **Layouts:** public site (header, mobile menu, footer), creator portal and agency admin (bottom
  tab bar on phones, sidebar on desktop, a "More" sheet for every admin section), sign-in
  pages, and a 404. Every route in the plan exists, and the ones later milestones build say
  which milestone fills them in.
- **Supabase:** browser, server, anonymous and admin clients; the first migration (roles,
  profiles, row level security, column-level grants so nobody can promote themselves, role
  helpers, and a `health()` check); a live connection check on `/styleguide`.
- **Tests:** 19 unit tests (money, time, statuses) and 15 database tests that run every
  migration on a real Postgres and act as real signed-in and signed-out users.
- **CI:** GitHub Actions runs every check on each push and applies migrations to the dev
  project once its secret is set.

Not in it yet, by design: sign in (M3), real data in the portal (M4 onward), and the 3D hero
(M2).

### Redesign after review (10 Oct 2026)

You found the first pass ugly and shared tasteskill.dev as the look you want. What changed:

- **Theme:** light by default, warm stone and paper-white, soft natural shadows; dark mode is a
  warm charcoal version of the same.
- **Hero:** a generated, sunlit plaster wall with floating product objects (a Telegram drop
  alert, a creator's post, a campaign report, a payout slip, the logo pressed into stone),
  drifting gently and following the pointer. No WebGL needed.
- **Type:** headlines pair Geist with an Instrument Serif italic accent ("on every *timeline*").
- **Home page:** the full design is in now, with placeholder content: hero, numbers, brand
  tiles, featured posts, services, how it works, for creators (with a phone showing the real
  campaign card), FAQ and the closing call to action. Milestone 2 connects it to editable
  content and builds the open campaigns board and the Book a campaign form.
- **Portal and admin:** the creator home, campaign board and admin overview show clearly
  labelled sample data, so the product can be judged before real data exists.

### Three looks, and an owner app and a creator app (11 Oct 2026)

You asked for your three references copied closely, as options, plus different interfaces for
you and your creators, and a detailed guide to listing a campaign. What changed:

- **Three looks, switchable from the header** (the swatch button, remembered on each device).
  Add `?look=renaissance`, `?look=agent` or `?look=drop` to any link to open it in that look.
  - **Renaissance** (after Shopify Editions): a living painting fills the hero. Poussin's
    *Blind Orion Searching for the Rising Sun* moves in depth with the pointer, with drifting
    clouds and swaying trees, and other paintings carry the sections.
  - **Agent** (after Mainframe): Echo, a felt 3D host on a red field, follows your pointer,
    blinks, talks while the greeting types out and reacts to the buttons. The FAQ is a chat with
    Echo.
  - **Drop** (after the juice-bottle hero): a carousel of five color slides. Each has a giant
    word behind a phone showing a creator's post, with glossy 3D icons floating around it.
  - Every section has a version per look, with scroll reveals, counting numbers, a claim demo on
    a phone, and page transitions. Slow phones, saved-data mode and reduced motion get still
    images instead of 3D, and nothing breaks without WebGL.
- **Your app, at `/admin`:** a calm control room. A sidebar with New campaign on top, ⌘K or
  Ctrl K search, the overview, the campaigns list, the six-step campaign builder (new, duplicate
  and edit) and each campaign's page with its roster. On phones: tabs at the bottom and a round
  New campaign button.
- **Your creators' app, at `/dashboard`:** playful and phone-first. Home with what needs them
  and new drops, the campaign board with filters, the campaign page with the full claim flow
  (instant and apply), My campaigns, Earnings and Notifications.
- **[docs/listing-a-campaign.md](docs/listing-a-campaign.md):** how to list a campaign, every
  field explained, plus what happens after (the drop, claiming, drafts, proof, review, paying,
  edits). The builder has the same guide built in ("How listing works").

How to test it on the preview link:

1. Open `/` and switch looks from the header. Try it on your phone and a computer, light and dark.
2. Open `/admin/campaigns/new` and list a campaign. Close the tab halfway; it picks up where you
   left off. The last step says it's a preview and nothing is saved.
3. Open `/dashboard/campaigns`, claim a campaign, and click through to Paid with the "Simulate
   agency review" panel. The avatar menu has "Reset the demo".

What's demo-only today: everything in both apps runs on demo data kept in your browser. Saving
campaigns arrives in Milestone 5, real claiming in 6, earnings and payouts in 7, notifications in
8. There's no sign-in yet (Milestone 3), so anyone with the preview link can open `/admin`; it
only holds demo data.

## Milestone 2 · Public website (built 13 Oct 2026)

What's in it:

- **Book a campaign** at `/book` and at the bottom of the home page, in every look. Instant
  checks as you type, the same checks again on the server, and a thank-you that says what
  happens next. One database function (`public.submit_lead`) rate limits, saves the lead, queues
  your email and writes the activity log in a single step, so a lead is never half saved.
- **Spam protection:** a hidden field only bots fill, a minimum fill time, and 5 requests an
  hour per connection. The connection is stored as a salted one-way hash of the IP, never the
  address, and hashes over two days old are cleared.
- **Your email:** each new lead emails `LEADS_NOTIFY_EMAIL` through Resend, sent just after the
  visitor's thank-you so the form stays fast. If sending fails, the email waits in the outbox
  and `POST /api/outbox` (protected by `CRON_SECRET`) sends it later, with retries.
- **Open campaigns** at `/campaigns`: live and full campaigns that are open to every creator,
  from demo data, with no payouts or budgets. Each card leads to sign up.
- **Privacy** and **Terms** in plain words, written from what the site does today.
- **Search and link previews:** a title and description on every page, a link-preview image for
  the home page, Book a campaign and Open campaigns, canonical links, `sitemap.xml` and
  `robots.txt`.
- **Safe to go live:** on the live site, `/admin`, `/dashboard` and `/styleguide` send visitors
  home until sign in exists (M3), and "Built in Milestone N" notes are hidden. Preview links
  still show everything. Apply, Sign in and password reset offer an email link meanwhile.
- **Netlify or Vercel:** see Working setup. On Netlify the rate limit reads the visitor's IP
  from the header Netlify itself sets, so nobody can fake a new address per request.
- **Tests:** 294 unit tests and 74 database tests, including every database rule above.

Set up before it works for real (each takes a few minutes, and I'll walk you through them):

1. **Supabase dev project:** create it, then add its connection string as the
   `DEV_DATABASE_URL` repository secret so GitHub applies the migrations.
2. **Resend:** create an account and an API key. Its test sender works until your domain is
   verified, but it only delivers to your Resend account's own email.
3. **Host settings:** add these environment variables in Netlify (or Vercel), never in the code:
   `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`,
   `RESEND_API_KEY`, `EMAIL_FROM`, `LEADS_NOTIFY_EMAIL` and `CRON_SECRET`. `RATE_LIMIT_SALT` is
   optional. `.env.example` says what each one is.

Until then the site still works: the form says bookings aren't connected yet and offers your
contact email.

How to test it on the preview link:

1. Open `/book`, send a booking, and check the email at `LEADS_NOTIFY_EMAIL`.
2. Send six bookings within an hour; the sixth is refused with a friendly message.
3. Open `/campaigns`, `/privacy` and `/terms` in each look, light and dark, on your phone.
4. Paste the home page link into X or WhatsApp to see its preview card.

What's left for later milestones:

- **Retrying failed emails on a schedule:** `POST /api/outbox` is ready; the scheduler that
  calls it arrives with Supabase Cron (key decision 5).
- **Leads in your admin:** the Leads page shows demo data until sign in (M3) and the leads
  pipeline (M9). New leads reach you by email meanwhile.
- **Profiles grants:** the M1 `profiles` table still relies on Supabase's default grants for
  the service key; M3 makes them explicit like the M2 tables.

## Milestone 3 · Accounts (built 13 Oct 2026)

What's in it:

- **Sign in and sign up** with email and password, or with Google. The Google button appears by
  itself once Google is switched on in Supabase (checked about once a minute), so nobody meets a
  half-set-up button. New accounts confirm their email before they can sign in.
- **Forgot password:** the link in the email opens a page to pick a new password, and you're
  signed in. The answer never says whether an address has an account.
- **Log out** from the account menu in the admin and in the creator app, and on the application
  page. If Supabase can't be reached, the sign-in cookies are cleared anyway.
- **Private pages:** signed-out visitors go to sign in, then straight back to the page they
  wanted. Links can only point back into this site.
- **Routing by role:** admin and team land in the admin, creators in the creator app, and new
  accounts on the application page (its form arrives in M4). Team can't open Invites, Payouts,
  Team or Settings. Staff can also open the creator app. A suspended account sees a note on the
  sign-in page instead of the apps.
- **Fast, and never stale where it matters:** a database hook writes each person's role into
  their sign-in token, so pages don't ask the database every time. Before turning anyone away,
  the site asks the database, so a promotion counts at once.
- **Your admin account:** sign up, then one line in Supabase's SQL editor (setup step 7).
- **Abuse protection** on top of Supabase's own limits: per hour, 30 sign-in tries per
  connection and 10 per account, 10 sign ups per connection, and 10 reset or confirmation
  emails per connection and 3 per inbox. Counted by salted hashes, never addresses.
- **Email links that work on any device:** the project's own email templates
  (`supabase/templates`) link back through `/auth/confirm`, so confirming on your phone works even
  if you signed up on a laptop. Supabase's standard links work too, in the same browser.
- **Privacy and Terms** now cover accounts: what an account stores, Google sign in, the sign-in
  cookie and how long account details are kept.
- **Database:** the role hook, the sign-in rate limits, the first-admin step, and explicit
  service-key grants on profiles (the M2 follow-up).
- **Tests:** 382 unit tests and 90 database tests, including every routing rule, the proxy, each
  sign-in action and both email-link routes.

Set up before it works for real (I'll walk you through each one):

1. **Addresses:** Supabase > Authentication > URL Configuration. Set Site URL to the live address
   (for example `https://agi2027.netlify.app`). Under Redirect URLs add `https://agi2027.netlify.app/**`,
   the preview links (`https://*--agi2027.netlify.app/**` on Netlify) and `http://localhost:3000/**`.
2. **Email sending:** Supabase > Authentication > Emails > SMTP Settings. Host `smtp.resend.com`,
   port 465, username `resend`, password your Resend API key, sender the `EMAIL_FROM` address.
   Supabase's built-in sender only reaches your own team and sends a couple of emails an hour.
   Until your domain is verified in Resend, emails only reach your Resend account's address.
3. **Email templates:** Supabase > Authentication > Emails > Templates. Paste
   `supabase/templates/confirmation.html` into "Confirm signup" (subject: Confirm your AGI 2027
   account) and `supabase/templates/recovery.html` into "Reset password" (subject: Set a new AGI
   2027 password).
4. **Passwords:** Supabase > Authentication > Sign In / Providers > Email. Keep "Confirm email"
   on, and set the minimum password length to 8.
5. **Role hook:** Supabase > Authentication > Hooks > Customize Access Token (JWT) Claims, pick
   the Postgres function `public.custom_access_token_hook` and enable it.
6. **Google:** in Google Cloud, create an OAuth client (Web application) with the authorized
   redirect URI `https://<your project>.supabase.co/auth/v1/callback`. Then in Supabase >
   Authentication > Sign In / Providers > Google, paste its client ID and secret and switch it on.
7. **Your admin account:** sign up on the site with your email and confirm it. Then in Supabase >
   SQL Editor run `select private.make_first_admin('your@email');`, sign out and sign in again.

How to test it on the preview link:

1. Open `/admin` signed out: you land on sign in, and after signing in you're back on `/admin`.
2. Sign up with a second email and confirm it from your phone: you land on the application
   page. Try `/admin` and `/dashboard`: you're sent back.
3. Use "Forgot your password?", open the link, pick a new password: you're signed in.
4. Log out from the account menu: the sign-in page says you're signed out.
5. Once Google is set up: "Continue with Google".
6. Get your password wrong 11 times within an hour: the 11th try is refused.

What's left for later milestones:

- **The application itself:** the form, approval and invite links (M4). The application page is
  a placeholder that offers the contact email meanwhile.
- **Team invites** (M9). Until then the admin is the only staff account.
- **The public site's header** still says "Sign in" to signed-in people; the sign-in page sends
  them straight on to their app.

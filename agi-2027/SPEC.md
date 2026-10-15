# AGI 2027 Build Spec

10 Oct 2026 · @Alexander

> This is the source of truth for what we are building. It is updated whenever we change
> something; see [Change log](#change-log) at the bottom. The build plan lives in
> [PLAN.md](PLAN.md).

## Read this first

You are building AGI 2027, a full web platform for an AI creator agency. Read this whole spec
before you write any code.

- Start with a short plan: the pages, the database tables, and the milestones. Wait for my OK,
  then begin Milestone 1.
- Build in the milestones under Build order. After each one, stop, tell me what you built, and
  tell me how to test it.
- Save this spec in the project as SPEC.md and update it whenever we change something.
- When a step needs an account, a key, or a setting outside the code, walk me through it step by
  step.
- If something big is not covered here, ask me. For small choices, pick the sensible option and
  keep going.
- Build mobile first. Most creators will use this on their phones.
- It must look premium, far above a basic template. See Design direction.
- doomers.ai and unfair.so are references for structure only. Do not copy their text, images, or
  branding.

## What AGI 2027 is

AGI 2027 is a creator marketing agency for AI startups and tech projects. Startups pay us to get
attention for launches, funding news, and product drops. We brief our creators, they post about
it on X, and they get paid per post.

The platform has two sides:

- **Public website:** sells the agency to startups and invites creators to apply.
- **Private portal:** where the agency runs campaigns and creators claim them, post, submit proof,
  and get paid.

The core loop: we drop a campaign and creators claim it. They post, paste the post link as proof,
we approve it, and we mark them paid. Some campaigns need a draft approved before posting.

Everyone sees each status change live. This replaces running campaigns by hand in Telegram
groups. We start with about 15 creators, but it must handle hundreds.

## Tech stack

Use this stack. If you have a strong reason to change any part, tell me first.

- App: Next.js (App Router) with TypeScript
- Database, sign in, files, live updates: Supabase (Postgres, Auth with Google and email, Storage,
  Realtime)
- Styling and UI: Tailwind CSS, shadcn/ui, Framer Motion, Lucide icons
- Hero: three switchable looks (changed 11 Oct 2026). React Three Fiber draws the living
  painting and the felt 3D host; the Drop look uses pre-rendered 3D icons and plain DOM motion
- Forms and validation: React Hook Form and Zod
- Email: Resend with React Email templates
- Telegram: Telegram Bot API for campaign drop alerts
- Hosting: Vercel or Netlify, with a custom domain (Netlify added 13 Oct 2026; the site runs on
  both)

## Roles

Four roles sign in. Clients never sign in; they see their report through a private link.

| Role      | Who                             | What they can do                                                                                                                           |
| --------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Admin     | Me, the agency owner            | Everything, including payouts, team, and settings                                                                                          |
| Team      | Agency staff I invite           | Create and run campaigns, review applications and submissions. No payouts, team, or settings                                               |
| Creator   | Approved creators               | See campaigns open to them, claim, submit drafts and proof, track their own earnings. Never see other creators' claims or earnings |
| Applicant | Signed up, not approved yet     | See their application status only                                                                                                          |
| Client    | Startups we work for, no login  | View a read only report for their campaign through a private link                                                                         |

## Public website

The public site sells AGI 2027 to startups and pulls in new creators. Write original copy in a
confident, simple voice.

Home page sections, in order:

1. **Hero:** a bold headline about launches going viral through creators people already follow.
   Two buttons: Book a campaign and Apply as a creator. Animated background (see Design
   direction).
2. **Stats strip:** network followers, monthly views, campaigns run, and creators. Numbers count
   up on scroll. I can edit them or hide the strip from the admin.
3. **Logo marquee:** brands we have worked with, uploaded from the admin.
4. **Proof:** featured posts from past campaigns, each with its numbers (views, likes, reposts).
   Managed from the admin.
5. **Services:** what we offer. Start with launch campaigns, monthly always on posting, and
   founder content. I will confirm the final list.
6. **How it works:** our process in 4 or 5 short steps, from matching creators to the final
   report.
7. **For creators:** why join, how campaigns and payment work, and an Apply button.
8. **FAQ:** editable from the admin.
9. **Final call to action:** the Book a campaign form, plus an email link.
10. **Footer:** links, socials, terms, and privacy.

Other public pages:

- **Open campaigns (/campaigns):** a public teaser of live campaigns with brand, title, short
  description, platform, and post date. The payout stays hidden behind a Sign up to see payout
  button. This pulls new creators in.
- **Book a campaign (/book):** inquiry form with name, company, website, X handle, what they are
  launching, launch date, budget range, and message. It saves to the database, shows in the admin
  Leads page, and emails me.
- **Also:** Apply (/apply), Sign in (/login), Forgot password, Terms, and Privacy.
- **SEO:** page titles, descriptions, Open Graph images for link previews, a sitemap, and robots
  rules.

## Accounts and sign in

Creators and team sign in with Google in one tap, or with email and password.

- Sign up and sign in with Google, or with email and password. Email sign ups must verify their
  email.
- Forgot password and reset password by email.
- Log out from the avatar menu on every page.
- Sessions stay signed in across visits. Middleware protects every private page. Signed out users
  go to /login and return to where they were after signing in.
- After sign in, route by role: admin and team to /admin, approved creators to /dashboard,
  applicants to their application status page.
- Team members join only by invite from the admin. Nobody can make themselves team or admin.
- The first admin account is mine. Set it up with a seed script or a one time setup step.
- Light and dark mode toggle on every page. Dark is the default.

## Creator onboarding

New creators apply and wait for approval. Creators I invite skip the wait.

### Apply as a creator

1. Create an account with Google or email.
2. Fill the application: display name, X handle, other socials (TikTok, YouTube, Instagram,
   LinkedIn, all optional), niches (AI, tech, crypto, startups, design, and so on), follower
   count, average views per post, country, links to their 3 best posts, and why they want to
   join.
3. See an Application received screen with their status. When we approve or reject, they get an
   email and the screen updates.

### Invite links

- Admin creates invite links, with an optional limit on uses and an expiry date.
- Anyone who signs up through an invite link is approved straight away. I will use this to move
  my current Telegram creators in fast.

### Referral links

- Every approved creator gets a personal referral link. Applications through it show who referred
  them.

### Creator profile

- Photo, display name, handles, niches, short bio, follower and view numbers (self reported for
  now), and an optional rate per post.
- Admin sets tiers and tags on each creator, for example Tier 1, Tier 2, AI builders, or Crypto.
  Campaigns can target these.

### Payout details

- Preferred method: crypto wallet with its network (for example USDC on Base or Solana), bank
  transfer, or other.
- Wallet address or bank details. Only the creator and the admin can see these.
- Any change to payout details sends the creator a confirmation email, so nobody can quietly swap
  them.

## Campaigns

Admin creates campaigns, then drops them to creators now or at a scheduled time.

### Campaign fields

- **Brand:** pick an existing client or add one (name, logo, website, X handle).
- **Title and summary:** a clear title and a one line summary.
- **Brief:** about the company, what the post should say, the key message, and do's and don'ts.
- **Angles:** a list of suggested angles or hooks. Admin can assign one angle to each creator so
  posts don't all sound the same.
- **Deliverable:** original post, quote post, reply, thread, video, or other.
- **Platform:** X first. Also TikTok, Instagram, LinkedIn, and YouTube.
- **Links:** the post to quote or reply to, plus any tracking or referral link creators must
  include.
- **Required tags:** mentions, hashtags, and keywords that must appear.
- **Assets:** images, videos, and a brand kit link, uploaded to storage for creators to download.
- **Payout:** amount per creator and currency (USD, USDC, NGN, and so on). Allow a custom amount
  per creator or per tier.
- **Slots:** how many creators can take part.
- **Audience:** all creators, chosen tiers or tags, or hand picked creators.
- **Claim mode:** instant (first come, first served) or apply (admin accepts each request).
- **Draft required:** yes or no.
- **Timing:** drop time, post window (start and end), claim deadline, and proof deadline. Admin can
  also give each creator their own post time inside the window.
- **Paid partnership label:** required by default. Creators must use X's paid partnership label on
  every paid post.
- **Internal:** admin notes and campaign budget. Creators never see these.

Campaign statuses: Draft, Scheduled, Live, Paused, Full, Closed, Completed.

### Dropping a campaign

- Publish now, or schedule a drop time.
- On drop, it appears in the portal for the right creators. They get an in app notification and
  an email, and the Telegram bot posts it in the creators group with a link.
- Show the post window in each creator's local time and in UTC.

### Other actions

- Duplicate a campaign to rerun a similar one fast.
- Edit a live campaign. Creators on it get notified that the brief changed.
- Pause, close, or mark complete.

## The campaign loop

Every claim moves through the same steps, and both sides see its status live.

Campaigns without a draft step go straight from claim to post. Rejected proof loops back until
the proof deadline.

### Creator steps

1. **Browse:** open campaigns show as cards (see Creator portal screens).
2. **Claim:** in instant mode the slot is reserved at once. In apply mode the creator adds a short
   note and waits for the agency to accept.
3. **Read the brief:** full brief, their angle, post time, assets, required tags and links, and a
   status timeline.
4. **Draft (only if required):** write the draft in the portal and attach media. The agency
   approves it or asks for changes with a comment, and the creator edits and resubmits.
5. **Post:** post on the platform inside the post window.
6. **Submit proof:** paste the post link and tick a box confirming the paid partnership label and
   the brief were followed. A screenshot is optional.
7. **Add metrics (optional):** 24 to 48 hours later, add views, likes, reposts, and replies with
   an analytics screenshot. These feed the client report.
8. **Get paid:** once proof is approved, an earning shows as Unpaid, then Paid with the payment
   reference.

Claim statuses: Requested, Claimed, Draft submitted, Changes requested, Draft approved, Proof
submitted, Approved, Rejected, Paid, Expired, Cancelled.

### Rules

- A creator can claim each campaign only once.
- A creator can drop a claim before their post window starts, and the slot opens again.
- If proof isn't in by the proof deadline, the claim expires and the slot reopens. Admin can
  extend a deadline or override.
- Rejected proof can be fixed and resubmitted until the proof deadline.
- Reminders go out before the post window and before the proof deadline.

## Review and approval

Everything waiting on the agency sits in one Review queue, and each item takes one tap to
approve.

- The queue holds claim requests, drafts, and proof links, oldest first, with a filter by
  campaign.
- Approve or reject each item, with an optional comment. Rejecting a draft or proof needs a
  reason, and the creator can fix it and resubmit.
- Bulk approve for campaigns with many creators.

### Free checks on every proof link (no paid X API)

- The link must be a real post link for the campaign's platform.
- For X, the username in the link must match the creator's X handle.
- The same link can't be submitted twice, across all campaigns.
- Show the post embedded so I can check it fast. For X, use the react-tweet package or X's oEmbed,
  which work without the paid API.
- If the post data loads for free this way, also check that it went out inside the post window
  and contains the required tags and link. Flag anything that fails instead of rejecting it
  automatically.
- If the data can't load, fall back to manual review.

## Payouts and earnings

Money moves outside the platform for now (wallet or bank), and the platform tracks every payment.

- When proof is approved, an earning is created for that creator with status Unpaid.
- Payouts page (admin only): unpaid totals grouped by creator, with their payout method and
  wallet or bank details. Select one or many and mark them Paid with the date, amount, method,
  and a reference (transaction hash or bank reference).
- Admin can add bonuses or deductions with a note.
- Creators see their Earnings: total earned, unpaid, paid, and a history with the reference for
  every payment.
- Keep totals per currency. Never add USD and NGN together.
- Export earnings and payouts to CSV.
- Every payout action goes into the activity log.

## Creator portal screens

The creator portal works like an app: a bottom tab bar on mobile and a sidebar on desktop.

- **Home:** new drops, active claims with countdowns, an earnings summary, and anything that needs
  action (draft changes, proof due).
- **Campaigns:** a card for every open campaign showing brand logo, title, payout, slots left,
  post window, platform, deliverable, and a countdown. Filters for platform, payout, and date. New
  drops are highlighted.
- **Campaign page:** the full brief, their assigned angle and post time, assets, required tags and
  links, the draft and proof forms, and a status timeline.
- **My campaigns:** tabs for Active, Submitted, Approved, Paid, and Past.
- **Earnings:** totals and payment history.
- **Notifications:** everything that happened, newest first.
- **Profile:** profile details, payout details, and their referral link.

## Agency admin screens

The admin is where I run the whole agency from one place.

- **Overview:** live campaigns, posts due today, items waiting for review, unpaid total, paid this
  month, new applications, and new leads. A chart of posts and payouts over time.
- **Campaigns:** list with filters. Create, edit, duplicate, schedule, and drop. Each campaign
  shows every creator on it with status, post time, draft, post link, metrics, and paid or not,
  plus bulk actions.
- **Review queue:** see Review and approval.
- **Creators:** searchable directory with filters (tier, niche, followers). Each profile shows
  history, approval rate, on time rate, total earned, and private admin notes. Approve, suspend,
  or remove.
- **Applications:** approve or reject, with notes.
- **Invites:** create and track invite links.
- **Payouts:** see Payouts and earnings.
- **Clients:** the startups we work with, their contacts, campaigns, and total spend.
- **Leads:** Book a campaign submissions, each with a status (New, Contacted, Won, Lost).
- **Site content:** edit the homepage stats, logos, featured posts, and FAQ.
- **Team:** invite team members and set their role.
- **Settings:** agency name, Telegram bot connection, currencies, default campaign rules, and
  email sender.
- **Activity log:** who did what and when, for claims, approvals, payouts, and setting changes.

## Notifications

Creators and the agency hear about every important change in the app, by email, and on Telegram.

- **In app:** a bell with an unread count that updates live (Supabase Realtime).
- **Email to creators:** application approved or rejected, new campaign drop, claim accepted,
  draft approved or changes requested, proof approved or rejected, payout sent, and reminders
  before the post window and the proof deadline.
- **Email to admin:** new application, new lead, and new drafts or proofs waiting.
- **Telegram:** the bot posts every campaign drop to the creators group with a link to claim it.
  Admin connects the bot and picks the group in Settings.
- **Templates:** branded emails that match the site.
- **Preferences:** creators can turn off email types they don't want, except payment emails.

## Client reports

Every campaign gets a private report link I can send to the startup, with no login needed.

- A clean, branded page: campaign summary, every approved post shown embedded, and totals (posts,
  views, likes, reposts, replies) from the metrics collected.
- Never show payouts, budgets, or creator payment details on it.
- Admin can turn the link off or make a new one at any time.
- Download the report as a PDF (nice to have).

## Design direction

It should feel like a top AI lab built a creator agency: premium, futuristic, and fast. It must
look clearly better than doomers.ai and unfair.so.

- **Three looks, switchable** (changed 11 Oct 2026): the owner asked for each of three reference
  sites, copied closely, as options. A **Look** picker in the header switches the whole site, the
  choice is remembered per device, and `?look=agent` in a link opens a specific look. Layout,
  color, type and motion follow the references; the art, words and logos are AGI 2027's own
  (copying the references' artwork, text or branding would be using other companies' property).
  - **Renaissance** (after Shopify Editions): a full-bleed old-master painting that moves (Poussin's
    Blind Orion, 1658, The Met, public domain) with a spark of light ahead of Orion's reaching hand,
    small bold white type, an index of the page down the left edge, a hot pink signal. Sections use
    painting details and an editorial vellum and forest-green palette.
  - **Agent** (after Mainframe): a warm red field, Echo (a felt 3D host who watches the pointer,
    blinks, talks while the greeting streams in), a chatty greeting with white pill answers, a
    comma-separated nav. Sections are introduced by Echo in speech bubbles; the FAQ is a chat.
  - **Drop** (after the classic juice-bottle product hero): one giant condensed word behind the
    product (a phone showing a creator's post), glossy 3D icons floating around it, a juicy color
    per slide, dots and a counter. Sections are color blocks with giant condensed headings.
- **Light and dark** still work inside every look and are remembered per device.
- **Type:** Geist for body text and UI everywhere, Geist Mono for small labels. The display face
  follows the look: bold Geist (Renaissance), soft Geist (Agent), Anton capitals (Drop).
- **Motion:** one personality across the site: springs for things that arrive, a smoother spring
  for moving between states, a fast snap for hover and press. Headings rise word by word, cards
  and lists arrive in sequence, numbers count up, the creator phone demonstrates a claim, dividers
  draw themselves. Reduced motion turns all of it into simple fades.
- **Portal:** the owner's admin is a dense, calm "control room"; the creator portal is a playful,
  mobile-first app. Both use the active look's colors and type.
- **Installable:** the portal installs on phones like an app (PWA with an icon and splash screen).
- **Accessible:** strong contrast, keyboard navigation, and visible focus states.

## Data model

Suggested tables. Adjust where it makes sense, and put Row Level Security on every table.

| Table           | What it holds                                                                                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| profiles        | user id, role, status, name, avatar, X handle, other socials, niches, followers, average views, country, bio, tier, tags, referral code, referred by                                                 |
| payout_details  | creator, method, wallet address and network or bank details (creator and admin only)                                                                                                                |
| applications    | creator, answers, status, reviewer, notes                                                                                                                                                            |
| invites         | code, created by, uses, max uses, expiry                                                                                                                                                             |
| clients         | name, logo, website, X handle, contacts                                                                                                                                                              |
| campaigns       | client, title, summary, brief, angles, deliverable, platform, links, required tags, payout, currency, slots, audience, claim mode, draft required, drop time, post window, deadlines, status, budget, notes, report token |
| campaign_assets | campaign, file, type                                                                                                                                                                                 |
| claims          | campaign, creator, status, assigned angle, post time, note, a timestamp for each status                                                                                                              |
| drafts          | claim, text, media, status, feedback                                                                                                                                                                 |
| submissions     | claim, post URL, screenshot, confirmations, metrics, status, review note                                                                                                                             |
| earnings        | creator, claim, amount, currency, type (campaign, bonus, deduction), status                                                                                                                          |
| payouts         | creator, earnings included, amount, currency, method, reference, paid at                                                                                                                             |
| notifications   | user, type, message, link, read                                                                                                                                                                      |
| leads           | Book a campaign submissions and their status                                                                                                                                                         |
| site_content    | homepage stats, logos, featured posts, FAQ                                                                                                                                                           |
| activity_log    | who, what, when, details                                                                                                                                                                             |

## Security and quality rules

These rules are not optional.

- Row Level Security on every table. Creators only read their own claims, drafts, submissions,
  earnings, and payout details. Applicants can't see campaigns. Team can't see payout details.
- Claim slots inside one database function or transaction, so a campaign can never be overfilled,
  even when many creators tap Claim at once.
- Validate every form on the server with Zod.
- Rate limit sign in, applications, and the Book a campaign form. Add a spam check (honeypot or
  Cloudflare Turnstile) on public forms.
- Keep every secret in environment variables, never in the code. Never expose the Supabase service
  key to the browser.
- Store all times in UTC. Show local time plus UTC.
- Log important actions to the activity log.
- Write tests for the core logic: claiming, status changes, expiry, and payouts.
- Seed demo data (one admin, a few creators, campaigns in every status) so everything can be
  tested.
- Keep it fast: optimized images, lazy loaded 3D, and a high Lighthouse score on mobile.

## Build order

Build in this order, and show me a working result at the end of each milestone.

1. **Setup:** project, Supabase, design system (colors, fonts, components), light and dark mode,
   and base layouts.
2. **Public website:** home page, open campaigns board, and the Book a campaign form.
3. **Accounts:** Google and email sign in, sign up, forgot password, log out, roles, and protected
   routes.
4. **Creator onboarding:** applications, approval, invites, referral links, profiles, and payout
   details.
5. **Campaigns:** create, edit, schedule, drop, the campaign board, and the campaign page.
6. **The loop:** claiming, drafts, proof links, the review queue, free checks, and expiry.
7. **Earnings and payouts.**
8. **Notifications:** in app, email, and Telegram drops.
9. **Admin extras:** overview stats, creators directory, clients, leads, site content, team, and
   activity log.
10. **Client reports.**
11. **Polish and launch:** animations, PWA, SEO, speed, accessibility, and tests. Then deploy to
    Vercel on my domain.

## Accounts and keys to set up

You can't create these for me, so walk me through each one when we reach the milestone that
needs it.

- [ ] Supabase project (database, auth, storage)
- [ ] Google Cloud OAuth client for Google sign in, connected to Supabase
- [ ] Resend account with a verified sending domain
- [ ] Telegram bot from BotFather, added to my creators group as an admin
- [ ] GitHub repository for the code
- [ ] Netlify or Vercel account connected to the GitHub repository
- [ ] A domain for AGI 2027

## Phase 2 (after launch)

Leave these out of the first build, but design the database so they can be added later.

- Automatic post tracking and metrics through the paid X API
- Creators connect their X account so their handle is verified automatically
- Personal Telegram alerts and phone push notifications
- Automatic payouts, for example in USDC
- A client portal with logins for startups
- Case study pages managed from the admin
- Referral bonuses, leaderboards, and creator badges
- Rate cards and pricing suggestions for creators
- Tracking for TikTok, Instagram, LinkedIn, and YouTube posts

## Change log

| Date        | Change                                                                                                                                                                                                   |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 10 Oct 2026 | Spec saved as received. The campaign loop section reads as if it had a diagram; if so, it did not come through in the paste. The claim and campaign status flows are written out from the text in [PLAN.md](PLAN.md#status-flows). |
| 10 Oct 2026 | Plan approved. The code lives in `agi-2027/` in the BlackHoleeee repo. The signature accent is acid lime (`#C6FF3A`); light mode uses `#3F6600` for lime text. Fonts are Geist Sans and Geist Mono. |
| 10 Oct 2026 | Milestone 1 built. shadcn/ui components are written into the repo by hand on Radix (same components, same API). The theme uses an inline script instead of next-themes. Database migrations reach Supabase through GitHub Actions. Details in PLAN.md. |
| 10 Oct 2026 | Design direction changed after review of Milestone 1: light, warm and tactile instead of dark and neon (reference: tasteskill.dev, for feel only). Light is the default theme, dark is a warm charcoal alternative, headlines get an italic serif accent, the hero is floating product objects on a generated plaster wall instead of a WebGL particle field, and acid lime is a small signal only. The full home page design moved forward from Milestone 2 with placeholder content. |
| 11 Oct 2026 | Design direction replaced at the owner's request: three switchable looks copied closely from three references (Shopify Editions, Mainframe, a juice-bottle product hero), with AGI 2027's own art, words and logos. Every section animates. The owner's admin and the creator portal now have clearly different interfaces, and the campaign builder and claim flow are built against demo data ahead of Milestones 5 and 6. The plaster wall, the floating-object hero and the serif accent are gone. |
| 11 Oct 2026 | Milestone 1 merged. Drop is the default look (the owner asked me to choose); Renaissance and Agent stay one tap away in the header switcher. |
| 12 Oct 2026 | Placeholder posts replaced with five real launch posts the owner sent (snapshot from their screenshots, linked to X). The last Drop slide became "Hype" to fit Hedwig's post. X is unreachable from the build environment and its free embed data has no view or repost counts, so posts are stored, not fetched live. Until the owner confirms they were AGI 2027 campaigns, the hero labels each as an example. |
| 12 Oct 2026 | The contact email (joshhthepluggg@gmail.com) is for visitors only: every "email us" link uses it, and nothing automated is sent there. Booking alerts go to a separate inbox set as `LEADS_NOTIFY_EMAIL`. |
| 13 Oct 2026 | Milestone 2 built. Hosting can be Netlify or Vercel (the owner asked about Netlify); the site works out which while building, and Netlify is recommended because its free plan allows a business site. Until sign in exists, the live site hides the demo admin, creator portal and styleguide. Privacy and Terms are written in plain words from what the site does, for legal review before launch. Rate limit records (salted IP hashes) are cleared after two days. Details in PLAN.md. |
| 13 Oct 2026 | Milestone 2 review fixes: the form's hidden spam trap has a name browser autofill and password managers never fill (a filled trap would have thrown away a real booking), a website link that grows too long once cleaned up gets a clear message, and `RATE_LIMIT_SALT` is optional (the salt comes from the Supabase secret key when it isn't set). |

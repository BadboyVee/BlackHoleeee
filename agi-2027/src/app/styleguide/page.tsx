import { Suspense } from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Megaphone, Plus, Sparkles, Wallet } from "lucide-react";

import { Logo, LogoMark } from "@/components/brand/logo";
import { CampaignCard, type CampaignCardData } from "@/components/campaign/campaign-card";
import { SkipLink } from "@/components/layout/skip-link";
import { StatusBadge, StatusDot } from "@/components/status-badge";
import { SupabaseStatus } from "@/components/system/supabase-status";
import { LookPicker } from "@/components/theme/look-picker";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CountUp } from "@/components/ui/count-up";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { statusMeta, type StatusKind } from "@/lib/statuses";
import { FeedbackDemo, FormDemo, OverlayDemo, TabsDemo } from "./demos";

export const metadata: Metadata = {
  title: "Design system",
  description: "Colors, type, components and patterns used across AGI 2027.",
  robots: { index: false, follow: false },
};

const sections = [
  { id: "status", label: "System" },
  { id: "color", label: "Color" },
  { id: "type", label: "Type" },
  { id: "buttons", label: "Buttons" },
  { id: "badges", label: "Statuses" },
  { id: "forms", label: "Forms" },
  { id: "cards", label: "Cards" },
  { id: "feedback", label: "Feedback" },
  { id: "overlays", label: "Overlays" },
];

const surfaceTokens = [
  { name: "background", note: "Page" },
  { name: "surface", note: "Cards" },
  { name: "surface-2", note: "Raised, hover" },
  { name: "surface-3", note: "Pressed, tracks" },
  { name: "popover", note: "Menus, dialogs" },
];

const textTokens = [
  { name: "foreground", note: "Primary text" },
  { name: "muted-foreground", note: "Secondary text" },
  { name: "subtle-foreground", note: "Labels, hints" },
  { name: "brand", note: "Acid lime accent" },
  { name: "brand-text", note: "Accent as text" },
  { name: "destructive", note: "Danger actions" },
];

const exampleCampaign: CampaignCardData = {
  href: "/dashboard/campaigns",
  brand: { name: "Nebula AI", initials: "NA" },
  title: "Nebula 2.0 launch day",
  summary: "Quote the launch post with your honest first take on Nebula's new agent builder.",
  payout: { amount: "250", currency: "USDC" },
  slots: { total: 20, taken: 13 },
  platform: "x",
  deliverable: "Quote post",
  postWindow: { start: "2027-01-12T17:00:00Z", end: "2027-01-12T21:00:00Z" },
  status: "live",
  isNew: true,
};

const fullCampaign: CampaignCardData = {
  ...exampleCampaign,
  brand: { name: "Vector Labs", initials: "VL" },
  title: "Series A announcement",
  summary: "A short thread on what Vector's funding means for open-source AI tooling.",
  payout: { amount: "180000", currency: "NGN" },
  slots: { total: 12, taken: 12 },
  deliverable: "Thread",
  status: "full",
  isNew: false,
};

export default function StyleguidePage() {
  return (
    <div className="min-h-dvh">
      <SkipLink />
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4 sm:px-6">
          <Link href="/" aria-label="AGI 2027 home">
            <Logo />
          </Link>
          <Badge variant="outline" className="font-mono text-[11px] tracking-wide">
            Design system
          </Badge>
          <div className="ml-auto flex items-center gap-1">
            <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
              <Link href="/dashboard">Creator portal</Link>
            </Button>
            <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
              <Link href="/admin">Admin</Link>
            </Button>
            <LookPicker />
            <ThemeToggle />
          </div>
        </div>
        <nav
          aria-label="Sections"
          className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 pb-3 [scrollbar-width:none] sm:px-6"
        >
          {sections.map((section) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className="shrink-0 rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground"
            >
              {section.label}
            </a>
          ))}
        </nav>
      </header>

      <main id="main" tabIndex={-1} className="mx-auto max-w-6xl px-4 pb-24 outline-none sm:px-6">
        <section className="relative isolate overflow-hidden py-14 sm:py-20">
          <p className="text-label text-subtle-foreground">Milestone 1</p>
          <h1 className="mt-4 max-w-3xl text-h1 text-balance">
            The building blocks of AGI 2027.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-pretty text-muted-foreground">
            Every screen is built from these tokens and components, so the public site, the creator
            portal and the admin feel like one product. Switch the look and the light or dark mode in
            the top right to check every combination.
          </p>
        </section>

        <Section id="status" title="System status" description="Whether this deployment can reach its Supabase database.">
          <Card>
            <CardContent className="pt-5 sm:pt-6">
              <Suspense
                fallback={
                  <div className="flex items-start gap-3">
                    <Skeleton className="mt-1 size-2 rounded-full" />
                    <div className="grid flex-1 gap-2">
                      <Skeleton className="h-4 w-28" />
                      <Skeleton className="h-3.5 w-64 max-w-full" />
                    </div>
                  </div>
                }
              >
                <SupabaseStatus />
              </Suspense>
            </CardContent>
          </Card>
        </Section>

        <Section id="color" title="Color" description="A warm, sunlit stone palette with paper-white cards. Acid lime is a signal only. Dark mode is a warm charcoal version of every token.">
          <div className="grid gap-8">
            <SwatchRow title="Surfaces" tokens={surfaceTokens} />
            <SwatchRow title="Text and accent" tokens={textTokens} />
            <div>
              <p className="mb-3 text-label text-subtle-foreground">Status tones</p>
              <div className="flex flex-wrap gap-2">
                {(["gray", "blue", "violet", "amber", "orange", "teal", "green", "red", "brand"] as const).map(
                  (tone) => (
                    <Badge key={tone} tone={tone} className="capitalize">
                      <StatusDot tone={tone} />
                      {tone}
                    </Badge>
                  ),
                )}
              </div>
            </div>
          </div>
        </Section>

        <Section id="type" title="Type" description="The display face follows the look: bold Geist for Renaissance, soft Geist for Agent, condensed Anton capitals for Drop. Geist for body text and Geist Mono for small labels.">
          <div className="grid gap-8">
            <TypeSample label="Display · hero headlines">
              <p className="text-display">
                Launch loud.
              </p>
            </TypeSample>
            <TypeSample label="H1 · page titles">
              <p className="text-h1">Creators people already follow.</p>
            </TypeSample>
            <TypeSample label="H2 · section titles">
              <p className="text-h2">How a campaign runs</p>
            </TypeSample>
            <TypeSample label="H3 · card titles">
              <p className="text-h3">Nebula 2.0 launch day</p>
            </TypeSample>
            <TypeSample label="Body">
              <p className="max-w-2xl text-pretty">
                We brief our creators, they post about it on X, and they get paid per post. Every
                status change shows up live for both sides.
              </p>
            </TypeSample>
            <TypeSample label="Label · mono caps">
              <p className="text-label text-muted-foreground">Post window · Proof due</p>
            </TypeSample>
            <TypeSample label="Numbers · mono, tabular">
              <p className="text-figure text-4xl">$12,480.50</p>
            </TypeSample>
            <TypeSample label="Wordmark">
              <div className="flex items-center gap-6">
                <Logo />
                <LogoMark className="size-10" />
              </div>
            </TypeSample>
          </div>
        </Section>

        <Section id="buttons" title="Buttons" description="Compact pills: black for the main action, white for the alternative.">
          <div className="grid gap-6">
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="brand">
                Claim slot
                <ArrowRight />
              </Button>
              <Button>Approve</Button>
              <Button variant="secondary">Save draft</Button>
              <Button variant="outline">Duplicate</Button>
              <Button variant="ghost">Cancel</Button>
              <Button variant="destructive">Reject</Button>
              <Button variant="link">View brief</Button>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button size="sm">Small</Button>
              <Button>Default</Button>
              <Button size="lg">Large</Button>
              <Button size="xl" variant="brand">
                Extra large
              </Button>
              <Button size="icon" variant="secondary" aria-label="Add">
                <Plus />
              </Button>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button loading>Submitting proof</Button>
              <Button disabled variant="secondary">
                Disabled
              </Button>
            </div>
          </div>
        </Section>

        <Section id="badges" title="Statuses" description="Every status in the product has one label and one color, everywhere it appears.">
          <div className="grid gap-6">
            {(Object.keys(statusMeta) as StatusKind[]).map((kind) => (
              <div key={kind}>
                <p className="mb-3 text-label text-subtle-foreground">{kindLabels[kind]}</p>
                <div className="flex flex-wrap gap-2">
                  {Object.keys(statusMeta[kind]).map((status) => (
                    <StatusBadge key={status} kind={kind} status={status as never} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="forms" title="Forms" description="Large, clear fields that don't zoom on iPhone, with inline hints and errors.">
          <Card>
            <CardContent className="pt-5 sm:pt-6">
              <FormDemo />
            </CardContent>
          </Card>
        </Section>

        <Section id="cards" title="Cards" description="Cards lift on hover. The campaign card is a first pass at what creators will see on the board.">
          <div className="grid gap-5 md:grid-cols-2">
            <CampaignCard campaign={exampleCampaign} />
            <CampaignCard campaign={fullCampaign} />
          </div>
          <div className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Network followers" value={12_400_000} />
            <StatCard label="Monthly views" value={85_000_000} />
            <StatCard label="Campaigns run" value={140} format="plain" />
            <StatCard label="Creators" value={15} format="plain" />
          </div>
          <p className="mt-3 text-xs text-subtle-foreground">
            Example numbers. Scroll this into view from the top of the page to see them count up.
          </p>
        </Section>

        <Section id="feedback" title="Feedback" description="Skeletons instead of blank screens, empty states that say what to do next, and toasts for results.">
          <div className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Loading skeleton</CardTitle>
                <CardDescription>Shown while a campaign card loads.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4">
                <div className="flex items-center gap-3">
                  <Skeleton className="size-11 rounded-xl" />
                  <div className="grid flex-1 gap-2">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-4 w-44" />
                  </div>
                </div>
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-11 w-full rounded-full" />
              </CardContent>
            </Card>
            <EmptyState
              icon={Wallet}
              title="No earnings yet"
              description="Once the agency approves your proof, the earning appears here as Unpaid, then Paid with its reference."
              action={
                <Button asChild variant="secondary" size="sm">
                  <Link href="/dashboard/campaigns">
                    <Megaphone />
                    Browse campaigns
                  </Link>
                </Button>
              }
            />
          </div>
          <div className="mt-5">
            <FeedbackDemo />
          </div>
        </Section>

        <Section id="overlays" title="Overlays and navigation" description="Dialogs rise from the bottom on phones. Menus, sheets, tooltips and tabs share one look.">
          <div className="grid gap-6">
            <OverlayDemo />
            <TabsDemo />
          </div>
        </Section>

        <div className="mt-16 flex flex-col items-start gap-4 rounded-3xl border bg-surface p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
          <div>
            <p className="flex items-center gap-2 font-semibold">
              <Sparkles className="size-4 text-brand-text" />
              See it in the app shells
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              The creator portal and admin use these components with bottom tabs on phones and a
              sidebar on desktop.
            </p>
          </div>
          <div className="flex gap-2">
            <Button asChild variant="secondary">
              <Link href="/dashboard">Creator portal</Link>
            </Button>
            <Button asChild>
              <Link href="/admin">Admin</Link>
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

const kindLabels: Record<StatusKind, string> = {
  claim: "Claims",
  campaign: "Campaigns",
  application: "Applications",
  invite: "Invite links",
  lead: "Leads",
  earning: "Earnings",
};

function Section({
  id,
  title,
  description,
  children,
}: {
  id: string;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-32 border-t py-12 sm:py-16">
      <div className="mb-8 max-w-2xl">
        <h2 className="text-h3">{title}</h2>
        <p className="mt-1.5 text-sm text-pretty text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  );
}

function SwatchRow({ title, tokens }: { title: string; tokens: { name: string; note: string }[] }) {
  return (
    <div>
      <p className="mb-3 text-label text-subtle-foreground">{title}</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {tokens.map((token) => (
          <div key={token.name} className="overflow-hidden rounded-2xl border bg-surface">
            <div className="h-16 border-b" style={{ background: `var(--${token.name})` }} />
            <div className="px-3 py-2.5">
              <p className="truncate font-mono text-xs font-medium">{token.name}</p>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{token.note}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TypeSample({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-2 sm:grid-cols-[12rem_1fr] sm:items-baseline sm:gap-6">
      <p className="text-label text-subtle-foreground">{label}</p>
      <div className="min-w-0">{children}</div>
    </div>
  );
}

function StatCard({
  label,
  value,
  format = "compact",
}: {
  label: string;
  value: number;
  format?: "compact" | "plain";
}) {
  return (
    <Card className="p-5">
      <p className="text-label text-subtle-foreground">{label}</p>
      <p className="mt-3 text-figure text-4xl">
        <CountUp value={value} format={format} />
      </p>
    </Card>
  );
}

import type { Metadata } from "next";
import Link from "next/link";

import { ContactLink, LegalList, LegalPage, LegalText, type LegalSection } from "@/components/marketing/legal-page";

const DESCRIPTION = "The terms for using the AGI 2027 site, booking a campaign and posting as a creator.";

export const metadata: Metadata = {
  title: "Terms",
  description: DESCRIPTION,
  alternates: { canonical: "/terms" },
};

/** The day this text last changed. Update it with every change. */
const UPDATED = "2026-10-13";

const linkClass = "font-medium underline underline-offset-4 hover:text-brand-text";

const SECTIONS: LegalSection[] = [
  {
    id: "these-terms",
    title: "About these terms",
    body: (
      <LegalText>
        These terms cover this website and how AGI 2027 works with the companies and creators who use it. By using
        the site, you agree to them. If you don&apos;t, please don&apos;t use it.
      </LegalText>
    ),
  },
  {
    id: "booking",
    title: "Booking a campaign",
    body: (
      <LegalList
        items={[
          <>
            The <Link href="/book" className={linkClass}>Book a campaign</Link> form asks us for a proposal. It
            isn&apos;t an order, and it commits you to nothing.
          </>,
          "A campaign starts only when we both agree its details in writing: the creators, the posts, the dates and the price.",
          "That written agreement is the one that counts. Where it differs from these terms, it wins.",
          "Tell us the truth about your product and launch. You're responsible for the claims you ask creators to make, and for having the right to share anything you send us.",
        ]}
      />
    ),
  },
  {
    id: "results",
    title: "Results",
    body: (
      <LegalText>
        Creators post to their own audiences, and nobody controls what X shows or how people react. We work hard
        for strong results, but we can&apos;t promise views, followers, sign-ups or sales.
      </LegalText>
    ),
  },
  {
    id: "open-campaigns",
    title: "Open campaigns",
    body: (
      <LegalText>
        The <Link href="/campaigns" className={linkClass}>campaigns board</Link> shows campaigns open to creators.
        Details can change, and a campaign can fill or close at any time. Seeing a campaign there isn&apos;t an offer
        of work: creators take part through an approved account, under that campaign&apos;s own brief.
      </LegalText>
    ),
  },
  {
    id: "creators",
    title: "Creators",
    body: (
      <>
        <LegalText>Creators who post for a campaign agree to:</LegalText>
        <LegalList
          items={[
            "Post what the brief allows, in their own words, and nothing misleading.",
            "Label paid posts clearly, for example with #ad or X's paid partnership label, as advertising rules require.",
            "Follow X's rules, and keep campaign details private until the brief says they can share them.",
          ]}
        />
        <LegalText>
          Each campaign says what it pays and when. Payment follows approved proof that the post went up as
          agreed.
        </LegalText>
      </>
    ),
  },
  {
    id: "using-the-site",
    title: "Using the site",
    body: (
      <LegalText>
        Please don&apos;t try to break or overload the site, get around its security, send spam through its forms, or
        copy it in bulk. We may block anyone who does.
      </LegalText>
    ),
  },
  {
    id: "content",
    title: "Names, posts and content",
    body: (
      <LegalList
        items={[
          "Company names and logos belong to their owners.",
          "The X posts we show belong to the people who posted them. We show them as examples, with links to the originals on X.",
          "The site's own words, design and code belong to AGI 2027.",
        ]}
      />
    ),
  },
  {
    id: "other-sites",
    title: "Other sites",
    body: (
      <LegalText>
        Links to X and other sites are there to help you. We don&apos;t run those sites and aren&apos;t responsible
        for them.
      </LegalText>
    ),
  },
  {
    id: "liability",
    title: "Liability",
    body: (
      <LegalText>
        We provide this site as it is. As far as the law allows, we aren&apos;t liable for indirect losses from
        using it, such as lost profits or data. Nothing here takes away rights you have by law that can&apos;t be
        taken away.
      </LegalText>
    ),
  },
  {
    id: "privacy",
    title: "Privacy",
    body: (
      <LegalText>
        How we handle information is on our <Link href="/privacy" className={linkClass}>privacy page</Link>.
      </LegalText>
    ),
  },
  {
    id: "changes",
    title: "Changes to these terms",
    body: (
      <LegalText>
        We may update these terms. The date at the top shows the latest version, and using the site after a change
        means you accept it. Questions? Email <ContactLink />.
      </LegalText>
    ),
  },
];

export default function TermsPage() {
  return (
    <LegalPage
      title="Terms"
      lead="The rules for using this site, booking a campaign and posting as a creator, in plain words."
      updated={UPDATED}
      summary={[
        "Sending a booking request costs nothing and commits you to nothing.",
        "A campaign starts only when we both agree its details in writing.",
        "Creators post honestly and label paid posts as ads.",
      ]}
      sections={SECTIONS}
      emailSubject="Question about the terms"
    />
  );
}

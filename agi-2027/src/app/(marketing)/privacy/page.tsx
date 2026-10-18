import type { Metadata } from "next";

import { ContactLink, LegalList, LegalPage, LegalText, type LegalSection } from "@/components/marketing/legal-page";

const DESCRIPTION = "What AGI 2027 collects, why, who helps us handle it, and how to have it changed or deleted.";

export const metadata: Metadata = {
  title: "Privacy",
  description: DESCRIPTION,
  alternates: { canonical: "/privacy" },
};

/** The day this text last changed. Update it with every change. */
const UPDATED = "2026-10-13";

/** Whoever hosts this deployment, baked in at build (see src/lib/deploy.ts). */
const HOSTS: Record<string, string> = { netlify: "Netlify", vercel: "Vercel" };

/*
 * Written from what the site does today: the Book a campaign form, accounts
 * (Supabase Auth, email or Google, a sign-in cookie), the hashed-IP and
 * hashed-email rate limits (private.take_rate_limit clears codes over two
 * days old on each call), look and theme choices in local storage, X posts
 * shown as local images. Applications and payouts come in later milestones;
 * add them here before they launch.
 */
function sections(): LegalSection[] {
  const host = HOSTS[process.env.AGI_DEPLOY_HOST ?? ""];
  return [
    {
      id: "who-we-are",
      title: "Who we are",
      body: (
        <LegalText>
          AGI 2027 is a creator marketing agency for AI and tech launches. We run this site and decide how the
          information on it is used. You can reach us at <ContactLink />.
        </LegalText>
      ),
    },
    {
      id: "what-we-collect",
      title: "What we collect",
      body: (
        <LegalList
          items={[
            <>
              <strong className="font-semibold">When you book a campaign:</strong> your name, work email, company
              and what you&apos;re launching. If you add them, also your website, X handle, launch date, budget
              range and message. We note which form you used.
            </>,
            <>
              <strong className="font-semibold">When you create an account:</strong> your name, email address and
              password. The password is stored scrambled, so nobody can read it, us included. If you sign in with
              Google, Google shares your name, email address and profile picture with us.
            </>,
            <>
              <strong className="font-semibold">To stop spam and password guessing:</strong> one-way codes made from
              your IP address, and from the email address you sign in with, plus a secret key. They let us limit how
              many forms and sign-in tries one connection or account gets in an hour. We never store the address
              itself, and codes over two days old are deleted whenever a form is used.
            </>,
            <>
              <strong className="font-semibold">When you email us:</strong> whatever you choose to write.
            </>,
            <>
              Creator applications and payouts aren&apos;t open yet. Before they are, this page will say what they
              collect and why.
            </>,
          ]}
        />
      ),
    },
    {
      id: "how-we-use-it",
      title: "How we use it",
      body: (
        <>
          <LegalList
            items={[
              "To reply to you and plan the campaign you asked about.",
              "To keep a record of each request, so our team can follow up.",
              "To run your account: signing you in, and emailing you links to confirm your address or reset your password.",
              "To protect the site, its forms and your account from spam and abuse.",
            ]}
          />
          <LegalText>
            We don&apos;t sell your information, use it for advertising, or add you to a mailing list.
          </LegalText>
          <LegalText>
            If you&apos;re in the UK or the EU: we use your booking details because you asked us for a proposal,
            your account details to provide the account you asked for, and the spam checks because we have a
            legitimate interest in keeping the site safe.
          </LegalText>
        </>
      ),
    },
    {
      id: "who-helps-us",
      title: "Who helps us",
      body: (
        <>
          <LegalText>A few companies handle information for us, only to provide their service:</LegalText>
          <LegalList
            items={[
              <>
                <strong className="font-semibold">Supabase</strong> stores your account and what you send in our
                database, and handles signing in.
              </>,
              <>
                <strong className="font-semibold">Resend</strong> sends our emails: the alert that tells our team
                about a new booking, and the links to confirm your email or reset your password.
              </>,
              <>
                <strong className="font-semibold">Google</strong>, only if you choose to sign in with it, confirms who
                you are.
              </>,
              host ? (
                <>
                  <strong className="font-semibold">{host}</strong> hosts this site. Like any web host, it handles
                  your connection to the site and keeps server logs for a limited time.
                </>
              ) : (
                "Our web host serves this site. Like any web host, it handles your connection and keeps server logs for a limited time."
              ),
              "Our email provider holds the emails you send us and the booking alerts our team receives.",
            ]}
          />
          <LegalText>
            They may store information outside your country. When they do, they protect it under their own
            safeguards and data protection terms.
          </LegalText>
        </>
      ),
    },
    {
      id: "in-your-browser",
      title: "In your browser",
      body: (
        <LegalList
          items={[
            "The site remembers the look you picked and light or dark mode in your browser's local storage. That stays on your device and never reaches us.",
            "When you sign in, the site keeps a sign-in cookie so you stay signed in. The site needs it to work, and it's deleted when you log out.",
            "We don't use advertising or analytics cookies, and we don't track you across other sites.",
            "The X posts on this site are pictures with links. Nothing loads from X unless you click through to it.",
          ]}
        />
      ),
    },
    {
      id: "how-long-we-keep-it",
      title: "How long we keep it",
      body: (
        <LegalList
          items={[
            "Booking details: while we're talking with you or working together, and after that only as long as we need for basic business records. Ask, and we'll delete them sooner unless the law says we must keep something.",
            "Account details: while your account is open. Ask, and we'll close it and delete them.",
            "The spam check codes: deleted once they're two days old, the next time a form is used.",
          ]}
        />
      ),
    },
    {
      id: "your-rights",
      title: "Your choices and rights",
      body: (
        <>
          <LegalText>
            Email <ContactLink /> to get a copy of what we hold about you, or to have it corrected or deleted.
            We&apos;ll reply within a month, and usually much sooner.
          </LegalText>
          <LegalText>
            Where the law gives you more rights, such as in the UK, the EU or California, you can use them the same
            way. You can also complain to your local data protection authority.
          </LegalText>
        </>
      ),
    },
    {
      id: "security",
      title: "Keeping it safe",
      body: (
        <LegalText>
          Only our server and our team can read what you send. The database checks who is asking on every table,
          and our keys stay out of the code and out of your browser. No system is perfect, so we keep what we
          collect to what we need.
        </LegalText>
      ),
    },
    {
      id: "children",
      title: "Children",
      body: (
        <LegalText>
          This site is for businesses and adults. We don&apos;t knowingly collect information from children. If you
          think a child has sent us something, email us and we&apos;ll delete it.
        </LegalText>
      ),
    },
    {
      id: "changes",
      title: "Changes to this page",
      body: (
        <LegalText>When we change this page, the date at the top changes too.</LegalText>
      ),
    },
  ];
}

export default function PrivacyPage() {
  return (
    <LegalPage
      title="Privacy"
      lead="What we collect, why we collect it, and who helps us handle it, in plain words."
      updated={UPDATED}
      summary={[
        "We collect what you type into our forms and your account details, and use them to reply, plan campaigns and run your account.",
        "We don't sell your information, show you ads, or track you around the web.",
        <>
          Email <ContactLink /> any time to see, fix or delete what we hold about you.
        </>,
      ]}
      sections={sections()}
      emailSubject="Privacy question"
    />
  );
}

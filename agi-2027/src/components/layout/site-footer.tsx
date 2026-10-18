import Link from "next/link";
import { cacheLife } from "next/cache";
import { Mail } from "lucide-react";

import { Wordmark } from "@/components/brand/wordmark";
import { XLogo } from "@/components/brand/social-icons";
import { siteConfig } from "@/lib/site";

const columns = [
  {
    title: "Brands",
    links: [
      { href: "/book", label: "Book a campaign" },
      { href: "/#how-it-works", label: "How it works" },
      { href: "/#faq", label: "FAQ" },
    ],
  },
  {
    title: "Creators",
    links: [
      { href: "/apply", label: "Apply as a creator" },
      { href: "/login", label: "Sign in" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/terms", label: "Terms" },
      { href: "/privacy", label: "Privacy" },
    ],
  },
];

async function CopyrightYear() {
  "use cache";
  cacheLife("days");
  return <>{new Date().getFullYear()}</>;
}

function SiteFooter() {
  return (
    <footer className="border-t drop:border-0 drop:bg-[#16120f] drop:text-white agent:border-0">
      <div className="mx-auto grid max-w-[84rem] gap-12 px-5 py-16 sm:px-8 md:grid-cols-[1.6fr_repeat(3,1fr)]">
        <div className="max-w-xs">
          <Wordmark />
          <p className="mt-4 text-sm leading-relaxed text-pretty text-muted-foreground drop:text-white/70">
            {siteConfig.description}
          </p>
          <div className="mt-5 flex gap-2">
            {siteConfig.xUrl ? (
              <a
                href={siteConfig.xUrl}
                target="_blank"
                rel="noreferrer"
                aria-label="AGI 2027 on X"
                className="inline-flex size-10 items-center justify-center rounded-full border text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground"
              >
                <XLogo className="size-4" />
              </a>
            ) : null}
            {siteConfig.contactEmail ? (
              <a
                href={`mailto:${siteConfig.contactEmail}`}
                aria-label="Email AGI 2027"
                className="inline-flex size-10 items-center justify-center rounded-full border text-muted-foreground transition-colors hover:border-border-strong hover:text-foreground"
              >
                <Mail className="size-4" />
              </a>
            ) : null}
          </div>
        </div>
        {columns.map((column) => (
          <div key={column.title}>
            <p className="text-sm font-medium">{column.title}</p>
            <ul className="mt-3 flex flex-col">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="inline-flex min-h-9 items-center text-sm text-muted-foreground transition-colors hover:text-foreground drop:text-white/70 drop:hover:text-white"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="look-drop">
        <p
          aria-hidden
          className="overflow-hidden px-3 font-[family-name:var(--font-anton)] text-[28.6vw] leading-[0.8] whitespace-nowrap text-white uppercase select-none"
        >
          AGI 2027
        </p>
      </div>
      <div className="border-t drop:border-white/15">
        <div className="mx-auto flex max-w-[84rem] flex-col gap-2 px-5 py-6 text-xs text-subtle-foreground sm:flex-row sm:items-center sm:justify-between sm:px-8 drop:text-white/60">
          <p>
            © <CopyrightYear /> AGI 2027. All rights reserved.
          </p>
          <p>Creator marketing for AI launches.</p>
        </div>
      </div>
    </footer>
  );
}

export { SiteFooter };

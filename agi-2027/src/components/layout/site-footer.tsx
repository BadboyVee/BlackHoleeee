import Link from "next/link";
import { cacheLife } from "next/cache";
import { Mail } from "lucide-react";

import { Logo } from "@/components/brand/logo";
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
      { href: "/campaigns", label: "Open campaigns" },
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
    <footer className="border-t">
      <div className="mx-auto grid max-w-6xl gap-12 px-5 py-16 sm:px-8 md:grid-cols-[1.6fr_repeat(3,1fr)]">
        <div className="max-w-xs">
          <Logo />
          <p className="mt-4 text-sm leading-relaxed text-pretty text-muted-foreground">
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
                    className="inline-flex min-h-9 items-center text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 text-xs text-subtle-foreground sm:flex-row sm:items-center sm:justify-between sm:px-8">
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

import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { SkipLink } from "@/components/layout/skip-link";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="relative isolate flex min-h-dvh flex-col overflow-hidden bg-wall">
      <SkipLink />
      <header className="flex h-16 items-center justify-between px-4 pt-3 sm:px-6">
        <Link
          href="/"
          aria-label="AGI 2027 home"
          className="flex h-11 items-center rounded-[14px] border bg-surface/80 px-3.5 shadow-soft backdrop-blur-xl"
        >
          <Logo />
        </Link>
        <div className="flex h-11 items-center rounded-full border bg-surface/80 p-1 shadow-soft backdrop-blur-xl">
          <ThemeToggle className="size-9" />
        </div>
      </header>
      <main
        id="main"
        tabIndex={-1}
        className="flex flex-1 items-start justify-center px-4 pt-6 pb-16 outline-none sm:items-center sm:pt-0"
      >
        <div className="w-full max-w-md">{children}</div>
      </main>
    </div>
  );
}

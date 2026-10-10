import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { SkipLink } from "@/components/layout/skip-link";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="relative isolate flex min-h-dvh flex-col overflow-hidden texture-noise">
      <SkipLink />
      <div aria-hidden className="absolute inset-0 -z-10 bg-grid mask-fade-radial" />
      <div
        aria-hidden
        className="absolute -top-48 left-1/2 -z-10 h-[30rem] w-[44rem] -translate-x-1/2 rounded-full bg-(--glow) blur-[110px]"
      />
      <header className="flex h-16 items-center justify-between px-4 sm:px-6">
        <Link href="/" aria-label="AGI 2027 home">
          <Logo />
        </Link>
        <ThemeToggle />
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

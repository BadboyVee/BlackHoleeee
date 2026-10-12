import Image from "next/image";
import Link from "next/link";

import { Wordmark } from "@/components/brand/wordmark";
import { SkipLink } from "@/components/layout/skip-link";
import { LookPicker } from "@/components/theme/look-picker";
import { ThemeToggle } from "@/components/theme/theme-toggle";

/**
 * Sign-in pages: the form on one side, the active look's art on the other
 * (a short banner on phones).
 */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="relative isolate grid min-h-dvh lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <SkipLink />
      <div className="flex min-h-dvh flex-col">
        <header className="flex h-16 items-center justify-between px-4 sm:px-6">
          <Link href="/" aria-label="AGI 2027 home" className="pressable flex items-center">
            <Wordmark />
          </Link>
          <div className="flex items-center gap-1.5">
            <LookPicker className="max-sm:pr-1.5 max-sm:[&>span:last-child]:sr-only" />
            <ThemeToggle />
          </div>
        </header>
        <AuthArt className="mx-4 h-36 rounded-[var(--radius-xl)] sm:mx-6 lg:hidden" compact />
        <main
          id="main"
          tabIndex={-1}
          className="flex flex-1 items-start justify-center px-4 pt-8 pb-16 outline-none sm:items-center sm:pt-0"
        >
          <div className="w-full max-w-md">{children}</div>
        </main>
      </div>
      <AuthArt className="sticky top-0 hidden h-dvh p-3 lg:block" />
    </div>
  );
}

function AuthArt({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div aria-hidden className={className}>
      <div className="look-renaissance">
        <div className="relative size-full overflow-hidden rounded-[var(--radius-xl)]">
          <Image
            src="/art/detail-clouds.webp"
            alt=""
            fill
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-t from-black/50 to-transparent" />
          {compact ? null : (
            <p className="absolute right-6 bottom-6 left-6 text-[clamp(1.75rem,1rem+2vw,3rem)] leading-[0.95] font-bold tracking-[-0.05em] text-white">
              Every launch deserves its legend.
            </p>
          )}
        </div>
      </div>
      <div className="look-agent">
        <div className="texture-noise relative flex size-full items-end overflow-hidden rounded-[var(--radius-xl)] bg-[radial-gradient(ellipse_80%_90%_at_60%_40%,#f0493c,#d92e24_50%,#b5170f)] p-6">
          <div className="flex items-end gap-3">
            <Image
              src="/art/echo-avatar.webp"
              alt=""
              width={compact ? 64 : 140}
              height={compact ? 64 : 140}
              className={compact ? "size-16 animate-float" : "size-32 animate-float sm:size-36"}
            />
            <p className="mb-3 rounded-[1.4rem] rounded-bl-md bg-white px-4 py-3 text-[15px] leading-snug text-[#1a1412] shadow-soft">
              Welcome back. Sign in and I&apos;ll show you today&apos;s drops.
            </p>
          </div>
        </div>
      </div>
      <div className="look-drop">
        <div className="relative flex size-full items-center justify-center overflow-hidden rounded-[var(--radius-xl)] bg-block-1">
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img src="/art/icons/heartwhite.webp" alt="" className="absolute top-[12%] left-[10%] w-[18%] -rotate-12 animate-float" />
          {/* eslint-disable-next-line @next/next/no-img-element -- decorative sprite */}
          <img src="/art/icons/bolt.webp" alt="" className="absolute right-[10%] bottom-[14%] w-[14%] rotate-12 animate-float [animation-delay:-2s]" />
          <p className="font-[family-name:var(--font-anton)] text-[clamp(4rem,12vw,11rem)] leading-none text-white uppercase">
            Hello
          </p>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import { Check, Eye, Heart, MessageCircle, MousePointerClick, Repeat2 } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { XLogo } from "@/components/brand/social-icons";
import { cn } from "@/lib/utils";

/*
 * The hero still life: real pieces of the product (a drop alert, a creator's
 * post, a campaign report, a payout slip) and the brand mark pressed into a
 * stone tile, floating off a sunlit wall. Laid out on a fixed 640×600 stage
 * and scaled per breakpoint; light comes from the upper left, so shadows fall
 * down and to the right. Each object drifts gently and follows the pointer by
 * its depth.
 */

type Placement = {
  left: number;
  top: number;
  width: number;
  rotate: string;
  depth: number;
  delay: string;
};

function FloatingObject({
  placement,
  className,
  children,
}: {
  placement: Placement;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="absolute"
      style={{
        left: placement.left,
        top: placement.top,
        width: placement.width,
        translate: `calc(var(--px, 0) * ${placement.depth}px) calc(var(--py, 0) * ${placement.depth}px)`,
        transition: "translate 600ms cubic-bezier(0.16, 1, 0.3, 1)",
      }}
    >
      <div className="animate-float motion-reduce:animate-none" style={{ animationDelay: placement.delay }}>
        <div
          className={cn("shadow-float", className)}
          style={{ transform: placement.rotate, transformStyle: "preserve-3d" }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

function DropAlert() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#161513] text-white">
      <div className="flex items-center gap-2.5 border-b border-white/8 px-4 py-3">
        <span className="flex size-6 items-center justify-center rounded-full bg-[#c6ff3a] text-[#0a0d02]">
          <LogoMark className="size-3" />
        </span>
        <span className="text-[12px] font-semibold tracking-[-0.01em]">AGI 2027 Drops</span>
        <span className="rounded-[4px] bg-white/10 px-1 py-px text-[9px] font-medium tracking-wide text-white/60 uppercase">
          bot
        </span>
        <span className="ml-auto text-[10px] text-white/45">now</span>
      </div>
      <div className="space-y-1.5 px-4 pt-3.5 pb-3 font-mono text-[11px] leading-relaxed text-white/75">
        <p className="text-white/55">New campaign dropped</p>
        <p className="text-[12px] font-medium text-white">Nebula 2.0 launch day</p>
        {["250 USDC per post", "7 of 20 slots left", "Window opens 17:00 UTC"].map((line) => (
          <p key={line}>
            <span className="text-[#c6ff3a]">›</span> {line}
          </p>
        ))}
      </div>
      <div className="px-4 pb-4">
        <span className="block rounded-lg bg-white/[0.08] py-2 text-center text-[11px] font-medium">
          Claim in the portal →
        </span>
      </div>
    </div>
  );
}

const reportRows = [
  { icon: Eye, label: "Views", value: "3.1M" },
  { icon: Heart, label: "Likes", value: "48.2K" },
  { icon: Repeat2, label: "Reposts", value: "6.1K" },
  { icon: MessageCircle, label: "Replies", value: "2.3K" },
  { icon: MousePointerClick, label: "Link clicks", value: "18.9K" },
];

function ReportPanel() {
  return (
    <div className="rounded-2xl border bg-surface text-foreground">
      <div className="px-4 pt-4 pb-2.5">
        <p className="text-[13px] font-semibold tracking-[-0.015em]">Campaign report</p>
        <p className="mt-0.5 text-[10px] text-subtle-foreground">Nebula 2.0 · 24 posts</p>
      </div>
      <ul className="px-2 pb-2">
        {reportRows.map((row) => (
          <li key={row.label} className="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
            <span className="flex size-6 items-center justify-center rounded-md border bg-surface-2">
              <row.icon className="size-3 text-muted-foreground" />
            </span>
            <span className="text-[11px] text-muted-foreground">{row.label}</span>
            <span className="ml-auto font-mono text-[11px] font-medium tabular">{row.value}</span>
          </li>
        ))}
      </ul>
      <div className="flex h-12 items-end gap-[3px] border-t px-4 pt-2.5 pb-3">
        {[22, 30, 26, 44, 70, 100, 86, 64, 52, 40, 34, 28, 24].map((height, i) => (
          <span
            key={i}
            className={cn("flex-1 rounded-[1.5px]", i === 5 ? "bg-foreground" : "bg-foreground/20")}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function StoneTile() {
  return (
    <div className="relative flex aspect-square items-center justify-center overflow-hidden rounded-[30px] bg-[radial-gradient(130%_130%_at_18%_12%,#f6f4f0,#dedad3_55%,#cfcac2)] shadow-[inset_2px_2px_2px_rgb(255_255_255/0.8),inset_-4px_-6px_12px_rgb(70_55_40/0.16)] dark:bg-[radial-gradient(130%_130%_at_18%_12%,#3a3733,#2a2825_55%,#211f1d)] dark:shadow-[inset_2px_2px_2px_rgb(255_255_255/0.08),inset_-4px_-6px_12px_rgb(0_0_0/0.4)]">
      <div aria-hidden className="absolute inset-0 opacity-60 texture-noise" />
      <LogoMark className="relative size-[46%] text-[#d9d5cd] [filter:drop-shadow(-1.5px_-1.5px_0_rgb(255_255_255/0.9))_drop-shadow(2px_3px_2.5px_rgb(70_55_40/0.38))] dark:text-[#2c2a27] dark:[filter:drop-shadow(-1px_-1px_0_rgb(255_255_255/0.08))_drop-shadow(2px_3px_2px_rgb(0_0_0/0.6))]" />
    </div>
  );
}

function PostCard() {
  return (
    <div className="rounded-2xl border bg-surface p-3.5 text-foreground">
      <div className="flex items-center gap-2">
        <span
          className="flex size-7 items-center justify-center rounded-full text-[10px] font-semibold text-white"
          style={{ background: "linear-gradient(140deg, hsl(95 32% 58%), hsl(125 30% 28%))" }}
        >
          MO
        </span>
        <div className="min-w-0 leading-tight">
          <p className="truncate text-[11px] font-semibold">Mira Okafor</p>
          <p className="truncate text-[10px] text-subtle-foreground">@mira_builds</p>
        </div>
        <XLogo className="ml-auto size-3 text-muted-foreground" />
      </div>
      <p className="mt-2.5 text-[11px] leading-relaxed">
        Nebula 2.0 shipped agents that actually finish the job. Planned and scheduled my whole week
        in four minutes.
      </p>
      <p className="mt-2 text-[9px] text-subtle-foreground">Paid partnership</p>
      <div className="mt-2.5 flex items-center gap-3 border-t pt-2.5 text-[10px] text-muted-foreground tabular">
        <span className="inline-flex items-center gap-1">
          <Eye className="size-3" /> 1.2M
        </span>
        <span className="inline-flex items-center gap-1">
          <Heart className="size-3" /> 18.4K
        </span>
        <span className="inline-flex items-center gap-1">
          <Repeat2 className="size-3" /> 2.1K
        </span>
      </div>
    </div>
  );
}

function PayoutSlip() {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#161513] p-4 text-white">
      <div className="flex items-center gap-2 text-[11px] text-white/60">
        <span className="flex size-5 items-center justify-center rounded-full bg-[#c6ff3a] text-[#0a0d02]">
          <Check className="size-3" strokeWidth={3} />
        </span>
        Payout sent
      </div>
      <p className="mt-3 flex items-baseline gap-1.5">
        <span className="font-mono text-[28px] leading-none font-medium tracking-[-0.06em]">250</span>
        <span className="text-[12px] text-white/60">USDC</span>
      </p>
      <dl className="mt-3 space-y-1 font-mono text-[10px] text-white/50">
        <div className="flex justify-between">
          <dt>to</dt>
          <dd className="text-white/75">0x4b…e1 · Base</dd>
        </div>
        <div className="flex justify-between">
          <dt>ref</dt>
          <dd className="text-white/75">0x9f…3a</dd>
        </div>
      </dl>
    </div>
  );
}

const placements = {
  drop: { left: 6, top: 26, width: 288, rotate: "rotateX(8deg) rotateY(-16deg) rotateZ(-2.5deg)", depth: 14, delay: "0s" },
  report: { left: 404, top: 0, width: 222, rotate: "rotateX(6deg) rotateY(12deg) rotateZ(2deg)", depth: 10, delay: "-3s" },
  stone: { left: 246, top: 262, width: 168, rotate: "rotateX(10deg) rotateY(-8deg) rotateZ(-6deg)", depth: 22, delay: "-6s" },
  post: { left: 34, top: 300, width: 196, rotate: "rotateX(6deg) rotateY(-10deg) rotateZ(3deg)", depth: 18, delay: "-1.5s" },
  payout: { left: 440, top: 352, width: 188, rotate: "rotateX(8deg) rotateY(14deg) rotateZ(-3deg)", depth: 12, delay: "-4.5s" },
} satisfies Record<string, Placement>;

function HeroObjects({ className }: { className?: string }) {
  const stage = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = stage.current;
    if (!element) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce), (pointer: coarse)").matches) return;
    const onMove = (event: PointerEvent) => {
      const x = (event.clientX / window.innerWidth) * 2 - 1;
      const y = (event.clientY / window.innerHeight) * 2 - 1;
      element.style.setProperty("--px", x.toFixed(3));
      element.style.setProperty("--py", y.toFixed(3));
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <div
      aria-hidden
      className={cn(
        "relative w-full [--s:0.56] sm:[--s:0.82] lg:[--s:0.84] xl:[--s:1]",
        "h-[calc(600px*var(--s))]",
        className,
      )}
    >
      <div
        ref={stage}
        className="absolute top-0 left-1/2 h-[600px] w-[640px] origin-top select-none [perspective:1800px]"
        style={{ transform: "translateX(-50%) scale(var(--s))" }}
      >
        <FloatingObject placement={placements.report}>
          <ReportPanel />
        </FloatingObject>
        <FloatingObject placement={placements.drop}>
          <DropAlert />
        </FloatingObject>
        <FloatingObject placement={placements.payout}>
          <PayoutSlip />
        </FloatingObject>
        <FloatingObject placement={placements.post}>
          <PostCard />
        </FloatingObject>
        <FloatingObject placement={placements.stone} className="rounded-[30px]">
          <StoneTile />
        </FloatingObject>
      </div>
    </div>
  );
}

export { HeroObjects };

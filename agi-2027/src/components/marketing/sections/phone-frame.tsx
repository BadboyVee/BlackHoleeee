import type { ReactNode, Ref } from "react";

import { cn } from "@/lib/utils";

/*
 * The phone both creator mockups sit in, so they match to the pixel. It is
 * drawn at one fixed size (288 by 600) and scaled as a whole: set
 * `--phone-scale` on it (for example `[--phone-scale:0.6] lg:[--phone-scale:0.8]`)
 * and the box it takes in the layout scales with it, so placing two phones
 * never needs magic margins.
 *
 * The screen is a picture of the creator app, so it keeps the app's own light
 * colors in every look and mode. The whole phone is one image for screen
 * readers: `label` says what it shows, everything inside is hidden from them
 * (not every screen reader skips the inside of an image on its own), and
 * nothing inside is focusable.
 */

const SIDE_BUTTON = "absolute w-[3px] bg-[linear-gradient(90deg,#1c1c1e,#4a4a4d)]";

function PhoneFrame({
  label,
  className,
  children,
  ref,
}: {
  label: string;
  className?: string;
  children: ReactNode;
  ref?: Ref<HTMLDivElement>;
}) {
  return (
    <div
      ref={ref}
      role="img"
      aria-label={label}
      data-phone
      className={cn(
        "relative h-[calc(600px*var(--phone-scale,1))] w-[calc(288px*var(--phone-scale,1))] shrink-0 select-none",
        className,
      )}
    >
      <div aria-hidden className="absolute top-0 left-0 h-[600px] w-[288px] origin-top-left [scale:var(--phone-scale,1)]">
        {/* Side buttons: action and volume on the left, power on the right. */}
        <span className={cn(SIDE_BUTTON, "top-[104px] -left-[2px] h-[26px] rounded-l-[2px]")} />
        <span className={cn(SIDE_BUTTON, "top-[150px] -left-[2px] h-[46px] rounded-l-[2px]")} />
        <span className={cn(SIDE_BUTTON, "top-[206px] -left-[2px] h-[46px] rounded-l-[2px]")} />
        <span className={cn(SIDE_BUTTON, "top-[168px] -right-[2px] h-[72px] rounded-r-[2px] rotate-180")} />

        <div className="relative h-full rounded-[2.85rem] bg-[linear-gradient(145deg,#4a4a4d,#121213_42%,#2c2c2e_78%,#545457)] p-[3px] shadow-[0_50px_90px_-30px_rgb(0_0_0/0.55),0_24px_40px_-18px_rgb(0_0_0/0.35)]">
          <div className="h-full rounded-[2.7rem] bg-[#0b0b0c] p-[7px] shadow-[0_1px_0_0_rgb(255_255_255/0.14)_inset]">
            <div className="relative flex h-full flex-col overflow-hidden rounded-[2.25rem] bg-[#f7f5f2] text-[#16120f] antialiased">
              <span className="absolute top-[9px] left-1/2 z-20 h-[25px] w-[31%] -translate-x-1/2 rounded-full bg-black" />
              <StatusBar />
              <div className="relative flex min-h-0 flex-1 flex-col">{children}</div>
              <span className="absolute bottom-[7px] left-1/2 z-20 h-[4px] w-[36%] -translate-x-1/2 rounded-full bg-[#16120f]/85" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** 9:41, signal, wifi and a battery, like every phone in an ad. */
function StatusBar() {
  return (
    <div className="flex h-[46px] shrink-0 items-end justify-between px-[26px] pb-[3px] text-[12.5px] font-semibold tracking-[-0.01em]">
      <span>9:41</span>
      <span className="flex items-center gap-[5px]">
        <span className="flex items-end gap-[1.5px]">
          {[4, 6, 8, 10].map((height) => (
            <span key={height} className="w-[3px] rounded-[1px] bg-current" style={{ height }} />
          ))}
        </span>
        <svg viewBox="0 0 16 12" className="h-[10px] w-[14px]" fill="currentColor">
          <path d="M8 2.2c2.3 0 4.4.9 6 2.4l1.3-1.4A10.6 10.6 0 0 0 8 .3 10.6 10.6 0 0 0 .7 3.2L2 4.6a8.6 8.6 0 0 1 6-2.4Zm0 3.7c1.3 0 2.5.5 3.4 1.3l1.3-1.4A6.7 6.7 0 0 0 8 4a6.7 6.7 0 0 0-4.7 1.8l1.3 1.4c.9-.8 2.1-1.3 3.4-1.3Zm0 3.7c-.5 0-1 .2-1.4.5L8 11.6l1.4-1.5c-.4-.3-.9-.5-1.4-.5Z" />
        </svg>
        <span className="flex items-center gap-px">
          <span className="h-[11px] w-[22px] rounded-[3.5px] border border-current/45 p-[1.5px]">
            <span className="block h-full w-[78%] rounded-[1.5px] bg-current" />
          </span>
          <span className="h-[4px] w-[1.5px] rounded-r-full bg-current/45" />
        </span>
      </span>
    </div>
  );
}

export { PhoneFrame };

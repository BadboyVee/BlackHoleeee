import { LogoMark } from "@/components/brand/logo";

/** The wordmark takes on each look's voice. */
function Wordmark() {
  return (
    <>
      <span className="look-renaissance">
        <span className="flex items-center gap-2">
          <LogoMark className="size-[18px]" />
          <span className="text-[15px] font-bold tracking-[-0.04em]">AGI 2027</span>
          <span className="hidden text-[13px] font-medium opacity-70 sm:inline">Creator Edition</span>
        </span>
      </span>
      <span className="look-agent">
        <span className="flex items-center gap-1.5">
          <span className="text-[16px] font-medium tracking-[-0.04em]">AGI 2027</span>
          <span className="-ml-1 self-start pt-0.5 text-[9px] font-medium">®</span>
          <LogoMark className="size-[15px]" />
        </span>
      </span>
      <span className="look-drop">
        <span className="flex items-center gap-2">
          <span className="font-[family-name:var(--font-anton)] text-[22px] leading-none tracking-[0.01em] uppercase">
            AGI 2027
          </span>
        </span>
      </span>
    </>
  );
}

export { Wordmark };

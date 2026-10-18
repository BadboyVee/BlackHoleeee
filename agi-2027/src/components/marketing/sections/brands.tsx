import { BrandMark } from "@/components/marketing/brand-mark";
import { brands, type Brand } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";

/**
 * How many times the client list repeats inside each half of the track. A
 * half has to be wider than the widest screen, or the loop shows a gap before
 * it starts over: the four names take about 740px in Renaissance and Agent
 * (920px in Drop), so six rounds make about 4,400px, past a 4K screen's
 * 3,840.
 */
const ROUNDS = 6;

/** Seconds per name, so the strip moves at the same pace however many clients there are. */
const SECONDS_PER_NAME = 5;

/** The logo's size in each look, so a name without a logo can keep the same space. */
const MARK_SIZE = "drop:size-8 drop:sm:size-10";

/**
 * One client: logo and name. A client without a logo keeps an empty space
 * the logo's size in front of its name, so every name sits the same distance
 * from the one before it and micro1 never reads as part of "Kled AI".
 */
function BrandName({ brand, className }: { brand: Brand; className?: string }) {
  return (
    <span
      className={cn(
        "flex shrink-0 items-center gap-2.5 text-foreground/75 drop:text-white",
        "text-[22px] font-bold tracking-[-0.045em] sm:text-[26px]",
        "agent:font-medium agent:text-foreground/80",
        // The client's own spelling, so no capitals in Drop: "micro1" stays "micro1".
        "drop:font-[family-name:var(--font-anton)] drop:text-[34px] drop:font-normal drop:tracking-[0.02em] drop:sm:text-[44px]",
        // Standing still on a phone, two by two: a little smaller in Drop so two fit across.
        "drop:max-sm:motion-reduce:text-[clamp(22px,7.5vw,28px)]",
        className,
      )}
    >
      {brand.logo ? (
        <BrandMark brand={brand} className={cn(MARK_SIZE, "drop:ring-2 drop:ring-white/40")} />
      ) : (
        <span aria-hidden className={cn("size-6 shrink-0", MARK_SIZE)} />
      )}
      {brand.name}
    </span>
  );
}

/**
 * The one marquee on the page: the clients we've launched, by name, with
 * their own logo where they have one (src/lib/marketing-content.ts). It
 * pauses on hover. With reduced motion it stands still and shows each name
 * once, centered (two by two on a phone).
 *
 * The track is two identical halves and slides left by exactly one half, so
 * the loop never jumps. Each half carries its own trailing space (padding,
 * not a gap between the halves), which keeps one half exactly 50% of the track.
 */
function BrandsMarquee() {
  const half = Array.from({ length: ROUNDS }, () => brands).flat();
  return (
    // Drop tilts the band; it runs a little past both edges and is clipped
    // here so the corners never leave a gap or make the page scroll sideways.
    <div className="overflow-x-clip">
      <section
        aria-label="Brands we've worked with"
        className="group/marquee relative overflow-hidden py-10 sm:py-14 drop:-mx-4 drop:my-10 drop:-rotate-[1.6deg] drop:bg-block-4 drop:py-6 drop:text-white drop:sm:py-8"
      >
        <ul className="sr-only">
          {brands.map((brand) => (
            <li key={brand.name}>{brand.name}</li>
          ))}
        </ul>
        <div aria-hidden className="mask-fade-x drop:[mask-image:none] motion-reduce:[mask-image:none]">
          <div
            className="flex w-max animate-marquee group-hover/marquee:[animation-play-state:paused] motion-reduce:w-auto motion-reduce:animate-none"
            style={{ animationDuration: `${half.length * SECONDS_PER_NAME}s` }}
          >
            {[0, 1].map((copy) => (
              <div
                key={copy}
                className={cn(
                  "flex shrink-0 items-center gap-12 pr-12 sm:gap-16 sm:pr-16 drop:gap-10 drop:pr-10",
                  // Still, the names center: the same space both sides, beating the loop's trailing space at every size.
                  "motion-reduce:w-full motion-reduce:shrink motion-reduce:flex-wrap motion-reduce:justify-center motion-reduce:gap-y-4 motion-reduce:px-5!",
                  copy === 0
                    ? // On a phone the still names make an even two by two grid, not rows of two, one and one.
                      "max-sm:motion-reduce:grid max-sm:motion-reduce:grid-cols-[repeat(2,auto)] max-sm:motion-reduce:gap-x-8 drop:max-sm:motion-reduce:gap-x-6"
                    : "motion-reduce:hidden",
                )}
              >
                {half.map((brand, index) => (
                  <BrandName
                    key={`${brand.name}-${index}`}
                    brand={brand}
                    className={index >= brands.length ? "motion-reduce:hidden" : undefined}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export { BrandsMarquee };

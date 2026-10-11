import { BrandGlyph } from "@/components/marketing/brand-glyph";
import { brands } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";

/**
 * The one marquee on the page: brands we've worked with (placeholder marks
 * until real logos are uploaded from the admin in Milestone 9). It pauses on
 * hover and stands still for reduced motion.
 */
function BrandsMarquee() {
  const row = [...brands, ...brands];
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
            <li key={brand}>{brand}</li>
          ))}
        </ul>
        <div aria-hidden className="mask-fade-x drop:[mask-image:none]">
          <div className="flex w-max animate-marquee items-center gap-12 group-hover/marquee:[animation-play-state:paused] motion-reduce:animate-none sm:gap-16 drop:gap-10">
            {row.map((brand, index) => (
              <span
                key={`${brand}-${index}`}
                className={cn(
                  "flex shrink-0 items-center gap-2.5 text-foreground/75 drop:text-white",
                  "text-[22px] font-bold tracking-[-0.045em] sm:text-[26px]",
                  "agent:font-medium agent:text-foreground/80",
                  "drop:font-[family-name:var(--font-anton)] drop:text-[34px] drop:font-normal drop:tracking-[0.02em] drop:uppercase drop:sm:text-[44px]",
                )}
              >
                <BrandGlyph
                  index={index % brands.length}
                  className="size-6 agent:text-brand drop:size-8 drop:text-[#ffd23f]"
                />
                {brand}
              </span>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export { BrandsMarquee };

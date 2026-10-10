import { CountUp } from "@/components/ui/count-up";
import { stats } from "@/lib/marketing-content";
import { cn } from "@/lib/utils";

const cellBorders = ["", "border-l", "border-t lg:border-t-0 lg:border-l", "border-l border-t lg:border-t-0"];

function StatsStrip() {
  return (
    <section aria-label="AGI 2027 in numbers" className="border-y">
      <div className="mx-auto grid max-w-6xl grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <div key={stat.label} className={cn("px-5 py-10 sm:px-8 sm:py-14", cellBorders[index])}>
            <p className="text-figure text-[2.75rem] leading-none sm:text-6xl">
              <CountUp value={stat.value} format={stat.format} suffix={stat.suffix} />
            </p>
            <p className="mt-4 text-sm text-muted-foreground">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export { StatsStrip };

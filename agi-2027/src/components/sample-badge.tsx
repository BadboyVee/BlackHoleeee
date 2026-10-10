/** Marks a screen that shows sample data until the real thing is built. */
function SampleBadge({ milestone }: { milestone: number }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-dashed border-border-strong px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
      Sample data · real in Milestone {milestone}
    </span>
  );
}

export { SampleBadge };

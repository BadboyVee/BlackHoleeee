import { cn } from "@/lib/utils";

import { panel, SectionHeading } from "../ui";

/**
 * One section of the profile page: a heading, a line on what it's for, and
 * the panel. The id doubles as an anchor, so other screens can link to
 * /dashboard/profile#payout-details.
 */
export function ProfilePanel({
  id,
  title,
  description,
  children,
  className,
}: {
  id: string;
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const headingId = `${id}-heading`;
  return (
    <section id={id} aria-labelledby={headingId} className="min-w-0 scroll-mt-24">
      <SectionHeading id={headingId} title={title} className="mb-1" />
      {description ? <p className="mb-4 max-w-prose text-sm text-pretty text-muted-foreground">{description}</p> : null}
      <div className={cn(panel, "p-4 sm:p-6", className)}>{children}</div>
    </section>
  );
}

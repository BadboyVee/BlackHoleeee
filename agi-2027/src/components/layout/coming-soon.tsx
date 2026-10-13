import { EmptyState } from "@/components/ui/empty-state";
import { isLiveSite } from "@/lib/deploy";

type ComingSoonProps = {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: React.ReactNode;
  milestone: number;
  action?: React.ReactNode;
};

/**
 * Placeholder for a screen a later milestone builds. Says which one on
 * preview links and in development, but never on the live site, where
 * visitors shouldn't see build-plan words.
 */
function ComingSoon({ icon, title, description, milestone, action }: ComingSoonProps) {
  const showMilestone = !isLiveSite();
  return (
    <EmptyState
      icon={icon}
      title={title}
      description={
        <>
          <p>{description}</p>
          {showMilestone ? <p className="mt-3 text-xs text-subtle-foreground">Built in Milestone {milestone}</p> : null}
        </>
      }
      action={action}
    />
  );
}

export { ComingSoon };

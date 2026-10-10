import { EmptyState } from "@/components/ui/empty-state";

type ComingSoonProps = {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: React.ReactNode;
  milestone: number;
  action?: React.ReactNode;
};

/** Placeholder for a screen a later milestone builds. Says which one. */
function ComingSoon({ icon, title, description, milestone, action }: ComingSoonProps) {
  return (
    <EmptyState
      icon={icon}
      title={title}
      description={
        <>
          <p>{description}</p>
          <p className="mt-3 text-xs text-subtle-foreground">Built in Milestone {milestone}</p>
        </>
      }
      action={action}
    />
  );
}

export { ComingSoon };

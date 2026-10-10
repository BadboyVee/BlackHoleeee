import { Badge } from "@/components/ui/badge";
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
          {description}
          <span className="mt-4 flex justify-center">
            <Badge variant="outline" className="font-mono text-[11px] tracking-wide">
              Arrives in Milestone {milestone}
            </Badge>
          </span>
        </>
      }
      action={action}
    />
  );
}

export { ComingSoon };

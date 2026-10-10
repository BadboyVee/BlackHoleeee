import { Fragment } from "react";

import { cn } from "@/lib/utils";

function Section({
  id,
  className,
  children,
}: {
  id?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className={cn("relative scroll-mt-24 py-20 sm:py-28", className)}>
      <div className="mx-auto max-w-6xl px-5 sm:px-8">{children}</div>
    </section>
  );
}

/** Renders *words* in the italic serif accent: "Posts that *moved* launches." */
function Accented({ text }: { text: string }) {
  return (
    <>
      {text.split(/\*(.+?)\*/).map((part, index) =>
        index % 2 === 1 ? (
          <em key={index} className="accent-serif">
            {part}
          </em>
        ) : (
          <Fragment key={index}>{part}</Fragment>
        ),
      )}
    </>
  );
}

function SectionHeader({
  kicker,
  title,
  description,
  align = "left",
  className,
}: {
  kicker?: string;
  /** Wrap words in *asterisks* for the serif accent. */
  title: string;
  description?: React.ReactNode;
  align?: "left" | "center";
  className?: string;
}) {
  return (
    <div className={cn("max-w-2xl", align === "center" && "mx-auto text-center", className)}>
      {kicker ? (
        <p
          className={cn(
            "flex items-center gap-2 text-label text-subtle-foreground",
            align === "center" && "justify-center",
          )}
        >
          <span aria-hidden className="size-1.5 rounded-full bg-(--tone-brand)" />
          {kicker}
        </p>
      ) : null}
      <h2 className="mt-5 text-h2 text-balance">
        <Accented text={title} />
      </h2>
      {description ? (
        <p className="mt-5 text-lead text-pretty text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}

export { Accented, Section, SectionHeader };

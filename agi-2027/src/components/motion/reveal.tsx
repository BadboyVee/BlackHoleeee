"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";

/**
 * The site's one reveal: things rise into place with a spring and a quick
 * de-blur as they scroll into view, once. Reduced motion gets a plain fade.
 */

const arrive = { type: "spring", stiffness: 400, damping: 30 } as const;

type Tag = "div" | "li" | "p" | "section" | "span" | "h2" | "h3" | "ul" | "ol" | "article" | "figure";

function Reveal({
  as = "div",
  delay = 0,
  y = 24,
  className,
  children,
}: {
  as?: Tag;
  delay?: number;
  y?: number;
  className?: string;
  children: React.ReactNode;
}) {
  const reduce = useReducedMotion();
  const Component = motion[as];
  return (
    <Component
      className={className}
      initial={reduce ? { opacity: 0 } : { opacity: 0, y, filter: "blur(6px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{
        ...arrive,
        delay,
        opacity: { duration: 0.45, delay },
        filter: { duration: 0.5, delay },
      }}
    >
      {children}
    </Component>
  );
}

const groupVariants: Variants = {
  hidden: {},
  shown: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
};

/** A list whose items arrive one after another (at most 6 to 8 staggered). */
function RevealGroup({
  as = "div",
  className,
  children,
  amount = 0.15,
}: {
  as?: Tag;
  className?: string;
  children: React.ReactNode;
  amount?: number;
}) {
  const Component = motion[as];
  return (
    <Component
      className={className}
      variants={groupVariants}
      initial="hidden"
      whileInView="shown"
      viewport={{ once: true, amount }}
    >
      {children}
    </Component>
  );
}

function RevealItem({ as = "div", className, children }: { as?: Tag; className?: string; children: React.ReactNode }) {
  const reduce = useReducedMotion();
  const Component = motion[as];
  const variants: Variants = reduce
    ? { hidden: { opacity: 0 }, shown: { opacity: 1 } }
    : {
        hidden: { opacity: 0, y: 24, filter: "blur(6px)" },
        shown: {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          transition: { ...arrive, opacity: { duration: 0.45 }, filter: { duration: 0.5 } },
        },
      };
  return (
    <Component className={className} variants={variants}>
      {children}
    </Component>
  );
}

/** A heading whose words rise out of a mask, one after another. */
function WordReveal({
  text,
  as = "h2",
  className,
  delay = 0,
}: {
  text: string;
  as?: "h1" | "h2" | "h3" | "p";
  className?: string;
  delay?: number;
}) {
  const reduce = useReducedMotion();
  const Component = motion[as];
  const words = text.split(" ");
  return (
    <Component
      className={className}
      initial="hidden"
      whileInView="shown"
      viewport={{ once: true, amount: 0.4 }}
      transition={{ staggerChildren: 0.06, delayChildren: delay }}
      aria-label={text}
    >
      {words.map((word, i) => (
        <span key={i} aria-hidden className="-mt-[0.14em] inline-block overflow-hidden pt-[0.14em] pb-[0.08em] align-bottom">
          <motion.span
            className="inline-block"
            variants={
              reduce
                ? { hidden: { opacity: 0 }, shown: { opacity: 1 } }
                : { hidden: { y: "105%" }, shown: { y: "0%", transition: arrive } }
            }
          >
            {word}
            {i < words.length - 1 ? " " : null}
          </motion.span>
        </span>
      ))}
    </Component>
  );
}

/** A hairline that draws itself from the left when its group arrives. */
function RuleDraw({ className }: { className?: string }) {
  return (
    <motion.span
      aria-hidden
      className={className}
      style={{ originX: 0 }}
      variants={{
        hidden: { scaleX: 0 },
        shown: { scaleX: 1, transition: { type: "spring", stiffness: 200, damping: 24 } },
      }}
    />
  );
}

export { Reveal, RevealGroup, RevealItem, RuleDraw, WordReveal };

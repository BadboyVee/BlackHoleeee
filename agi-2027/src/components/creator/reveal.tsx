"use client";

import { motion } from "motion/react";

import { useHydrated } from "./hooks";
import { springArrive } from "./motion";

/**
 * Springs content in when it appears. Content the server already painted
 * stays put on first load (nothing blinks out and back in); anything that
 * mounts later, like a page you navigate to, arrives with the spring.
 */
function Reveal({
  children,
  delay = 0,
  y = 14,
  className,
  inView = false,
}: {
  children: React.ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  /** Wait until it scrolls into view. */
  inView?: boolean;
}) {
  const hydrated = useHydrated();
  const hidden = { opacity: 0, y };
  const shown = { opacity: 1, y: 0 };
  return (
    <motion.div
      className={className}
      initial={hydrated ? hidden : false}
      {...(inView ? { whileInView: shown, viewport: { once: true, margin: "0px 0px -8% 0px" } } : { animate: shown })}
      transition={{ ...springArrive, delay }}
    >
      {children}
    </motion.div>
  );
}

export { Reveal };

"use client";

import { motion, useReducedMotion } from "motion/react";

import { cn } from "@/lib/utils";

import { springPop } from "./motion";

/* A fixed spread (golden-angle spiral) so the burst looks hand-placed and never random-ugly. */
const PARTICLES = Array.from({ length: 26 }, (_, index) => {
  const angle = (index * 137.508 * Math.PI) / 180;
  const distance = 64 + ((index * 37) % 70);
  return {
    x: Math.cos(angle) * distance,
    y: Math.sin(angle) * distance * 0.85 - 14,
    size: 5 + (index % 4) * 2,
    shape: index % 3,
    rotate: ((index * 67) % 300) - 150,
    tint: [100, 72, 48][index % 3],
    delay: (index % 6) * 0.018,
  };
});

/**
 * A short burst of particles in a brand's colors. Change `burstKey` to fire
 * it again. Nothing renders for people who ask for reduced motion.
 */
function Burst({ color, burstKey, className }: { color: string; burstKey: number; className?: string }) {
  const reduce = useReducedMotion();
  if (reduce || burstKey === 0) return null;
  return (
    <div aria-hidden className={cn("pointer-events-none absolute inset-0 flex items-center justify-center", className)}>
      {PARTICLES.map((particle, index) => (
        <motion.span
          key={`${burstKey}-${index}`}
          className="absolute"
          style={{
            width: particle.size,
            height: particle.shape === 2 ? particle.size * 1.9 : particle.size,
            borderRadius: particle.shape === 0 ? 999 : 2,
            background: `color-mix(in oklab, ${color} ${particle.tint}%, white)`,
          }}
          initial={{ x: 0, y: 0, scale: 0.2, opacity: 1, rotate: 0 }}
          animate={{ x: particle.x, y: particle.y, scale: 1, opacity: 0, rotate: particle.rotate }}
          transition={{
            x: { ...springPop, delay: particle.delay },
            y: { ...springPop, delay: particle.delay },
            scale: { ...springPop, delay: particle.delay },
            rotate: { duration: 0.9, ease: "easeOut", delay: particle.delay },
            opacity: { duration: 0.5, ease: "easeIn", delay: 0.42 + particle.delay },
          }}
        />
      ))}
    </div>
  );
}

export { Burst };

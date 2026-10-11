import type { Transition } from "motion/react";

/*
 * One motion personality for the creator app. Springs everywhere, three of them:
 *   arrive  things that appear (reveals, cards, sheets)
 *   move    things that go from one state to another (indicators, counters, tabs)
 *   pop     small celebrations only (a claim, a payment)
 * MotionConfig in the shell turns transforms off for people who ask for
 * reduced motion, so every animation falls back to a plain fade.
 */

export const springArrive = { type: "spring", stiffness: 400, damping: 30 } as const satisfies Transition;
export const springMove = { type: "spring", stiffness: 200, damping: 24 } as const satisfies Transition;
export const springPop = { type: "spring", stiffness: 500, damping: 18 } as const satisfies Transition;

/** Press feedback for anything tappable. */
export const pressed = { scale: 0.97 } as const;

/** Delay for the nth item of a staggered list, capped so long lists still feel quick. */
export function stagger(index: number, step = 0.045, max = 0.4) {
  return Math.min(index * step, max);
}

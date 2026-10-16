import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// Our type-scale utilities (text-h1, text-label, ...) set font size, not color,
// so tailwind-merge must not treat them as clashing with text-{color}.
// text-figure sets no size (it's paired with one, like text-figure text-xl),
// so it gets a group of its own.
const twMerge = extendTailwindMerge<"text-figure">({
  extend: {
    classGroups: {
      "font-size": [{ text: ["display", "h1", "h2", "h3", "lead", "label"] }],
      "text-figure": ["text-figure"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

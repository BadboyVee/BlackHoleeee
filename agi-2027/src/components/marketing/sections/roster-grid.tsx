"use client";

import { createContext, use, useEffect, useRef, useState, type ReactNode } from "react";

import { Reveal } from "@/components/motion/reveal";

/** How many cards fit across right now, read from the list's own `--cols`. */
const Columns = createContext(1);

/**
 * The roster's list. Set `--cols` on it per breakpoint (the CSS decides the
 * layout); the items read it back so each row ripples in from the left at
 * every width, not only at seven across.
 */
function RosterGrid({ className, children }: { className?: string; children: ReactNode }) {
  const list = useRef<HTMLUListElement>(null);
  const [columns, setColumns] = useState(1);

  useEffect(() => {
    const el = list.current;
    if (!el) return;
    const read = () => setColumns(Math.max(1, Number.parseInt(getComputedStyle(el).getPropertyValue("--cols"), 10) || 1));
    read();
    // A breakpoint always changes the list's width, so this catches every change of columns.
    const observer = new ResizeObserver(read);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <Columns value={columns}>
      <ul ref={list} className={className}>
        {children}
      </ul>
    </Columns>
  );
}

/** One card's slot: it arrives as it scrolls in, a beat after the card to its left. */
function RosterItem({ index, className, children }: { index: number; className?: string; children: ReactNode }) {
  const columns = use(Columns);
  return (
    <Reveal as="li" delay={(index % columns) * 0.05} className={className}>
      {children}
    </Reveal>
  );
}

export { RosterGrid, RosterItem };

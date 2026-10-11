"use client";

import { lazy, useCallback, useRef, useState } from "react";
import { useScroll } from "motion/react";

import { cn } from "@/lib/utils";
import { SceneGate } from "./scene-gate";

const RenaissanceCanvas = lazy(() => import("./renaissance-canvas"));

/** Loads the living painting over the static one and fades it in when ready. */
function RenaissanceStage({ position }: { position: [number, number] }) {
  const host = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const { scrollYProgress } = useScroll({ target: host, offset: ["start start", "end start"] });
  const onReady = useCallback(() => setReady(true), []);

  return (
    <div ref={host} aria-hidden className="absolute inset-0">
      <div
        className={cn(
          "absolute inset-0 transition-opacity duration-700 ease-snap",
          ready ? "opacity-100" : "opacity-0",
        )}
      >
        <SceneGate
          look="renaissance"
          scene={RenaissanceCanvas}
          props={{ position, progress: scrollYProgress, onReady }}
        />
      </div>
    </div>
  );
}

export { RenaissanceStage };

"use client";

import { lazy, useCallback, useState } from "react";

import { cn } from "@/lib/utils";
import { SceneGate } from "./scene-gate";

const EchoCharacter = lazy(() => import("./echo-character"));

/**
 * Echo, the felt host. A still of Echo shows straight away (and stays on
 * devices without WebGL); the live 3D Echo loads behind it and takes over
 * once its first frame is drawn. The stills are placed with container units
 * so they line up with the 3D framing at any screen size: on the right and
 * sized to the height on wide screens, centred at the bottom and sized to the
 * width on tall ones.
 */
function AgentStage() {
  const [ready, setReady] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  return (
    <div className="absolute inset-0 overflow-hidden [container-type:size]">
      <div
        data-echo-poster
        aria-hidden
        className={cn(
          "absolute inset-0 transition-opacity duration-700 ease-snap",
          ready ? "opacity-0" : "animate-fade-in opacity-100",
        )}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- positioned with container units */}
        <img
          src="/art/echo-poster.webp"
          alt=""
          loading="lazy"
          className="absolute top-[10.83cqh] left-[calc(73cqw-28.47cqh)] hidden w-[58.33cqh] max-w-none [@media(min-aspect-ratio:9/10)]:block"
        />
        {/* eslint-disable-next-line @next/next/no-img-element -- positioned with container units */}
        <img
          src="/art/echo-poster-phone.webp"
          alt=""
          loading="lazy"
          className="absolute bottom-0 left-[9.74cqw] block w-[81.15cqw] max-w-none [@media(min-aspect-ratio:9/10)]:hidden"
        />
      </div>
      <div className={cn("absolute inset-0 transition-opacity duration-700 ease-snap", ready ? "opacity-100" : "opacity-0")}>
        <SceneGate look="agent" scene={EchoCharacter} props={{ onReady }} />
      </div>
    </div>
  );
}

export { AgentStage };

"use client";

import { Suspense, useEffect, useState, type ComponentType, type LazyExoticComponent } from "react";

import { useLook } from "@/components/theme/look-picker";
import type { Look } from "@/lib/theme";

function webglAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

/**
 * Mounts a heavy WebGL scene only when its look is active, the browser can
 * draw it, and the page has painted (so it never competes with the first
 * paint). The static art underneath stays as the fallback.
 */
function SceneGate<P extends object>({
  look,
  scene: Scene,
  props,
}: {
  look: Look;
  scene: LazyExoticComponent<ComponentType<P>>;
  props: P;
}) {
  const active = useLook() === look;
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!active) return;
    const connection = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    if (connection?.saveData || !webglAvailable()) return;
    let cancelled = false;
    const start = () => {
      if (!cancelled) setReady(true);
    };
    const hasIdle = typeof window.requestIdleCallback === "function";
    const handle = hasIdle
      ? window.requestIdleCallback(start, { timeout: 900 })
      : window.setTimeout(start, 250);
    return () => {
      cancelled = true;
      if (hasIdle) window.cancelIdleCallback(handle);
      else window.clearTimeout(handle);
    };
  }, [active]);

  if (!active || !ready) return null;
  return (
    <Suspense fallback={null}>
      <Scene {...props} />
    </Suspense>
  );
}

export { SceneGate };

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useReducedMotion, type MotionValue } from "motion/react";
import * as THREE from "three";

/**
 * The living painting. One full-screen shader over Poussin's "Blind Orion
 * Searching for the Rising Sun" (1658, The Met, public domain):
 * - pointer parallax from a hand-made depth map, so the trees sit in front of
 *   the valley and Orion steps out of the canvas,
 * - clouds that churn slowly and treetops that sway,
 * - a spark of light just ahead of Orion's reaching hand (the sun he walks
 *   towards), which ignites on load and breathes.
 * The crop matches the static <img> underneath exactly (CSS object-fit:
 * cover with the same object-position), so the hand-over is invisible.
 */

export type RenaissanceCanvasProps = {
  /** CSS object-position of the art, as fractions (x from left, y from top). */
  position: [number, number];
  /** Scroll progress through the hero, 0 at the top and 1 when it has left. */
  progress?: MotionValue<number>;
  onReady?: () => void;
};

const IMAGE_ASPECT = 3630 / 2365;
/** Just ahead of Orion's outstretched hand, in image coordinates from the top left. */
const SPARK: [number, number] = [0.566, 0.522];

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;
  uniform sampler2D uImage;
  uniform sampler2D uMaps;
  uniform vec2 uResolution;
  uniform float uImageAspect;
  uniform vec2 uPosition;
  uniform vec2 uPointer;
  uniform vec2 uSpark;
  uniform float uTime;
  uniform float uIntro;
  uniform float uScroll;
  varying vec2 vUv;

  vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
  }
  float hash1(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
  }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(dot(hash2(i), f), dot(hash2(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0)), u.x),
      mix(dot(hash2(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)), dot(hash2(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  void main() {
    float canvasAspect = uResolution.x / uResolution.y;
    // object-fit: cover. "span" is how much of the image is visible on each axis.
    vec2 span = canvasAspect > uImageAspect
      ? vec2(1.0, uImageAspect / canvasAspect)
      : vec2(canvasAspect / uImageAspect, 1.0);
    // object-position semantics; texture v runs bottom to top.
    vec2 pos = vec2(uPosition.x, 1.0 - uPosition.y);
    // Zoom about the screen centre, like a CSS scale on the <img>: a breath of
    // room for parallax (matched by scale(1.0152) on the static image) and a
    // slow push in as the hero scrolls away.
    float zoom = 0.985 - 0.06 * uScroll;
    vec2 uv = pos * (1.0 - span) + (0.5 + (vUv - 0.5) * zoom) * span;
    vec2 s = span * zoom;

    vec3 maps = texture2D(uMaps, uv).rgb;
    float depth = maps.r;
    uv += uPointer * vec2(0.012, 0.007) * (depth - 0.3) * s;

    maps = texture2D(uMaps, uv).rgb;
    float t = uTime;
    // Clouds churn.
    vec2 flow = vec2(
      noise(uv * vec2(3.0, 5.0) + vec2(t * 0.045, 0.0)),
      noise(uv * vec2(3.0, 5.0) + vec2(5.2, t * 0.035))
    );
    uv += maps.g * flow * 0.004;
    // Treetops sway, more towards the top.
    float sway = sin(t * 1.15 + uv.y * 17.0 + uv.x * 7.0) * 0.55 + noise(uv * 9.0 + t * 0.25) * 0.45;
    uv.x += maps.b * sway * 0.0016 * smoothstep(0.2, 0.95, uv.y);

    vec3 col = texture2D(uImage, uv).rgb;

    // A gentle lift so the varnish reads less brown on screens.
    col = pow(col, vec3(0.9));
    float luma = dot(col, vec3(0.299, 0.587, 0.114));
    col = mix(vec3(luma), col, 1.12);

    // The spark.
    vec2 spark = vec2(uSpark.x, 1.0 - uSpark.y);
    vec2 dv = (uv - spark) * vec2(uImageAspect, 1.0) / s.y;
    float d = length(dv);
    float ignite = smoothstep(0.0, 1.0, uIntro);
    float breathe = 0.86 + 0.14 * sin(t * 1.7) + 0.05 * sin(t * 4.3);
    float core = exp(-d * d * 5200.0) * 1.6;
    float halo = exp(-d * 30.0) * 0.6;
    float bloom = exp(-d * 6.5) * 0.22;
    float angle = atan(dv.y, dv.x);
    float rays = pow(max(0.0, 0.5 + 0.5 * sin(angle * 9.0 + t * 0.12)), 7.0) * exp(-d * 11.0) * 0.4;
    rays += pow(max(0.0, 0.5 + 0.5 * sin(angle * 5.0 - t * 0.08 + 1.3)), 9.0) * exp(-d * 8.0) * 0.25;
    float flare = exp(-abs(dv.y) * 190.0) * exp(-abs(dv.x) * 5.5) * 0.4;
    vec3 white = vec3(1.0, 0.98, 0.94);
    vec3 warm = vec3(1.0, 0.82, 0.62);
    vec3 pink = vec3(1.0, 0.45, 0.72);
    vec3 glow = white * (core + halo * 0.8 + flare) + mix(warm, pink, 0.25) * (rays + halo * 0.4) + warm * bloom;
    col = col * (1.0 + bloom * 0.9 * ignite) + glow * ignite * breathe;

    // Vignette, scroll fade and a fine film grain to tie it together.
    vec2 q = vUv - 0.5;
    col *= 1.0 - dot(q * vec2(0.85, 1.15), q * vec2(0.85, 1.15)) * 0.5;
    col *= 1.0 - 0.35 * uScroll;
    col += (hash1(vUv * uResolution + fract(t * 7.0) * 91.0) - 0.5) * 0.03;

    gl_FragColor = vec4(col, 1.0);
  }
`;

function loadTexture(url: string) {
  return new Promise<THREE.Texture>((resolve, reject) => {
    new THREE.TextureLoader().load(
      url,
      (texture) => {
        texture.colorSpace = THREE.NoColorSpace;
        texture.minFilter = THREE.LinearMipmapLinearFilter;
        texture.magFilter = THREE.LinearFilter;
        texture.anisotropy = 4;
        texture.wrapS = THREE.ClampToEdgeWrapping;
        texture.wrapT = THREE.ClampToEdgeWrapping;
        resolve(texture);
      },
      undefined,
      reject,
    );
  });
}

function Painting({ position, progress, onReady }: RenaissanceCanvasProps) {
  const reduceMotion = useReducedMotion();
  const size = useThree((state) => state.size);
  const dpr = useThree((state) => state.viewport.dpr);
  const [textures, setTextures] = useState<{ image: THREE.Texture; maps: THREE.Texture } | null>(null);
  const material = useRef<THREE.ShaderMaterial>(null);
  const pointer = useRef(new THREE.Vector2());
  const target = useRef(new THREE.Vector2());
  const start = useRef<number | null>(null);
  const announced = useRef(false);

  useEffect(() => {
    let cancelled = false;
    const wide = window.innerWidth * Math.min(window.devicePixelRatio, 2) > 1700;
    Promise.all([
      loadTexture(wide ? "/art/orion-2400.webp" : "/art/orion-1600.webp"),
      loadTexture("/art/orion-maps.webp"),
    ])
      .then(([image, maps]) => {
        if (cancelled) {
          image.dispose();
          maps.dispose();
          return;
        }
        setTextures({ image, maps });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(
    () => () => {
      textures?.image.dispose();
      textures?.maps.dispose();
    },
    [textures],
  );

  useEffect(() => {
    if (reduceMotion) return;
    const coarse = window.matchMedia("(pointer: coarse)").matches;
    if (coarse) return;
    function onMove(event: PointerEvent) {
      target.current.set(
        (event.clientX / window.innerWidth) * 2 - 1,
        -((event.clientY / window.innerHeight) * 2 - 1),
      );
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [reduceMotion]);

  const uniforms = useMemo(
    () => ({
      uImage: { value: null as THREE.Texture | null },
      uMaps: { value: null as THREE.Texture | null },
      uResolution: { value: new THREE.Vector2(1, 1) },
      uImageAspect: { value: IMAGE_ASPECT },
      uPosition: { value: new THREE.Vector2(...position) },
      uPointer: { value: new THREE.Vector2() },
      uSpark: { value: new THREE.Vector2(...SPARK) },
      uTime: { value: 0 },
      uIntro: { value: 0 },
      uScroll: { value: 0 },
    }),
    // The position never changes after mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  useFrame((state) => {
    const shader = material.current;
    if (!shader || !textures) return;
    const u = shader.uniforms;
    u.uImage.value = textures.image;
    u.uMaps.value = textures.maps;
    (u.uResolution.value as THREE.Vector2).set(size.width * dpr, size.height * dpr);

    const now = state.clock.elapsedTime;
    if (start.current === null) start.current = now;
    const since = now - start.current;

    if (reduceMotion) {
      u.uIntro.value = 1;
      u.uTime.value = 0;
    } else {
      u.uIntro.value = Math.min(1, Math.max(0, (since - 0.25) / 1.4));
      u.uTime.value = now;
      // Touch screens get a slow, automatic drift instead of following a finger.
      if (window.matchMedia("(pointer: coarse)").matches) {
        target.current.set(Math.sin(now * 0.21) * 0.6, Math.sin(now * 0.17 + 1.2) * 0.4);
      }
      pointer.current.lerp(target.current, 0.045);
      (u.uPointer.value as THREE.Vector2).copy(pointer.current);
    }
    u.uScroll.value = progress ? Math.min(1, Math.max(0, progress.get())) : 0;

    if (!announced.current) {
      announced.current = true;
      // Wait one frame so the first real frame is on screen before fading in.
      requestAnimationFrame(() => onReady?.());
    }
  });

  return (
    <mesh frustumCulled={false}>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        ref={material}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        depthTest={false}
        depthWrite={false}
      />
    </mesh>
  );
}

function RenaissanceCanvas(props: RenaissanceCanvasProps) {
  const [visible, setVisible] = useState(true);
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = host.current;
    if (!element) return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={host} className="absolute inset-0">
      <Canvas
        flat
        linear
        dpr={[1, 1.75]}
        frameloop={visible ? "always" : "never"}
        gl={{ antialias: false, alpha: false, powerPreference: "high-performance" }}
        style={{ pointerEvents: "none" }}
        aria-hidden
      >
        <Painting {...props} />
      </Canvas>
    </div>
  );
}

export default RenaissanceCanvas;

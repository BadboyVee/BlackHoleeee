"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer } from "@react-three/drei";
import { useReducedMotion } from "motion/react";
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

/**
 * Echo, the Agent look's host: a felt character built from simple shapes and
 * a soft fabric material. Echo watches the pointer, blinks, breathes, talks
 * while the greeting streams in, and perks up when someone hovers a button
 * (the greeting dispatches "agi:echo" events).
 */

export type EchoCharacterProps = {
  onReady?: () => void;
};

type Mood = "idle" | "talk" | "curious" | "happy";

const SKIN = "#eaa47c";
const SKIN_SHEEN = "#ffd6bf";
const CHEEK = "#f07a6e";
const NOSE = "#ec8a70";
const HAIR = "#6a3720";
const HAIR_SHEEN = "#c88a5a";
const BROW = "#552a17";
const SHIRT = "#7d8b36";
const SHIRT_SHEEN = "#d9e391";
const COLLAR = "#97a748";

/* ------------------------------------------------------------- textures */

/** A tileable felt texture: thousands of short fibres, used as a bump map. */
function makeFeltTexture(size: number, fibres: number, strength: number, repeat: number) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#808080";
  ctx.fillRect(0, 0, size, size);
  ctx.lineCap = "round";
  const rand = mulberry32(size + fibres);
  for (let i = 0; i < fibres; i++) {
    const x = rand() * size;
    const y = rand() * size;
    const length = 2 + rand() * 7;
    const angle = rand() * Math.PI * 2;
    const alpha = 0.05 + rand() * strength;
    ctx.strokeStyle = rand() > 0.5 ? `rgba(255,255,255,${alpha})` : `rgba(0,0,0,${alpha})`;
    ctx.lineWidth = 0.6 + rand() * 1.1;
    for (const [dx, dy] of [
      [0, 0],
      [size, 0],
      [-size, 0],
      [0, size],
      [0, -size],
    ]) {
      ctx.beginPath();
      ctx.moveTo(x + dx, y + dy);
      ctx.lineTo(x + dx + Math.cos(angle) * length, y + dy + Math.sin(angle) * length);
      ctx.stroke();
    }
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(repeat, repeat);
  texture.colorSpace = THREE.NoColorSpace;
  return texture;
}

/** Iris and pupil, painted on a small canvas. */
function makeIrisTexture() {
  const size = 256;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const c = size / 2;
  const iris = ctx.createRadialGradient(c, c, size * 0.08, c, c, size * 0.5);
  iris.addColorStop(0, "#2b160b");
  iris.addColorStop(0.3, "#2b160b");
  iris.addColorStop(0.36, "#6b3d1c");
  iris.addColorStop(0.75, "#94602e");
  iris.addColorStop(0.9, "#3a1e0e");
  iris.addColorStop(1, "#24120a");
  ctx.fillStyle = iris;
  ctx.fillRect(0, 0, size, size);
  const rand = mulberry32(11);
  for (let i = 0; i < 180; i++) {
    const a = (i / 180) * Math.PI * 2;
    ctx.strokeStyle = `rgba(${rand() > 0.5 ? "255,210,150" : "40,20,10"},${0.08 + rand() * 0.12})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(c + Math.cos(a) * size * 0.17, c + Math.sin(a) * size * 0.17);
    ctx.lineTo(c + Math.cos(a) * size * 0.44, c + Math.sin(a) * size * 0.44);
    ctx.stroke();
  }
  ctx.fillStyle = "#0b0605";
  ctx.beginPath();
  ctx.arc(c, c, size * 0.16, 0, Math.PI * 2);
  ctx.fill();
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ------------------------------------------------------------- geometry */

/** The head: a sphere with fuller cheeks and a slightly flatter back. */
const HEAD = { sx: 1, sy: 1, sz: 0.94, cheeks: 0.12 };

function widthAt(y: number) {
  return y < 0 ? 1 + HEAD.cheeks * Math.min(1, -y / HEAD.sy) : 1;
}

/** How far forward the face is at (x, y), plus an outward offset. */
function faceZ(x: number, y: number, out = 0) {
  const k = widthAt(y);
  const u = x / (HEAD.sx * k);
  const v = y / HEAD.sy;
  return HEAD.sz * k * Math.sqrt(Math.max(0, 1 - u * u - v * v)) + out;
}

function makeHeadGeometry() {
  const geometry = new THREE.SphereGeometry(1, 72, 54);
  const p = geometry.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const y = p.getY(i) * HEAD.sy;
    const k = widthAt(y);
    const z = p.getZ(i);
    p.setXYZ(i, p.getX(i) * HEAD.sx * k, y, z * HEAD.sz * (z > 0 ? k : 0.97));
  }
  geometry.computeVertexNormals();
  return geometry;
}

/** A lumpy felt puff for the hair (indexed, so it shades smoothly). */
function makePuffGeometry() {
  const geometry = new THREE.SphereGeometry(1, 36, 26);
  const p = geometry.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).normalize();
    const lump =
      1 +
      0.07 * Math.sin(v.x * 5.1 + v.y * 2.3) * Math.cos(v.z * 4.7) +
      0.05 * Math.sin(v.y * 9.3 + v.z * 3.1) +
      0.03 * Math.cos(v.x * 13.7 - v.z * 7.9);
    v.multiplyScalar(lump);
    p.setXYZ(i, v.x, v.y, v.z);
  }
  geometry.computeVertexNormals();
  return geometry;
}

type Puff = { position: [number, number, number]; scale: [number, number, number]; rotation: [number, number, number] };

/** Hair: a cloud of felt puffs over the crown, and a fringe swept to one side. */
function makeHair(): Puff[] {
  const rand = mulberry32(27);
  const puffs: Puff[] = [];
  let tries = 0;
  while (puffs.length < 62 && tries < 2000) {
    tries++;
    const theta = rand() * Math.PI * 2;
    const phi = Math.acos(1 - rand() * 1.15);
    const x = Math.sin(phi) * Math.cos(theta);
    const z = Math.sin(phi) * Math.sin(theta);
    const y = Math.cos(phi);
    // Keep the face and the ears clear.
    if (z > 0.2 && y < 0.6) continue;
    if (Math.abs(x) > 0.75 && y < 0.25 && z > -0.35) continue;
    if (y < -0.15) continue;
    const r = 0.17 + rand() * 0.15;
    const reach = 1.0 + r * 0.25;
    puffs.push({
      position: [x * reach * HEAD.sx, y * reach * HEAD.sy + 0.03, z * reach * HEAD.sz],
      scale: [r * (0.9 + rand() * 0.3), r * (0.85 + rand() * 0.3), r * (0.9 + rand() * 0.3)],
      rotation: [rand() * 6, rand() * 6, rand() * 6],
    });
  }
  // The fringe: a swoop from the left temple up over the right brow.
  const fringe: [number, number, number, number][] = [
    [-0.56, 0.76, 0.46, 0.2],
    [-0.32, 0.9, 0.5, 0.23],
    [-0.04, 0.97, 0.5, 0.25],
    [0.26, 0.94, 0.5, 0.23],
    [0.5, 0.8, 0.44, 0.2],
    [0.1, 1.08, 0.3, 0.3],
    [-0.28, 1.06, 0.28, 0.27],
    [0.38, 1.02, 0.25, 0.26],
  ];
  for (const [x, y, z, r] of fringe) {
    puffs.push({ position: [x, y, z], scale: [r * 1.1, r * 0.9, r], rotation: [rand() * 6, rand() * 6, rand() * 6] });
  }
  return puffs;
}

/* ------------------------------------------------------------- materials */

function useMaterials() {
  return useMemo(() => {
    const felt = makeFeltTexture(512, 9000, 0.24, 3);
    const fuzz = makeFeltTexture(512, 16000, 0.42, 4);
    const make = (color: string, sheen: string, bump: THREE.Texture, bumpScale: number) =>
      new THREE.MeshPhysicalMaterial({
        color,
        roughness: 0.94,
        sheen: 1,
        sheenRoughness: 0.45,
        sheenColor: new THREE.Color(sheen),
        bumpMap: bump,
        bumpScale,
      });
    return {
      skin: make(SKIN, SKIN_SHEEN, felt, 1.8),
      neck: make("#cf8460", SKIN_SHEEN, felt, 1.8),
      cheek: make(CHEEK, "#ffc0b2", felt, 1.8),
      nose: make(NOSE, "#ffc8b2", felt, 1.6),
      hair: make(HAIR, HAIR_SHEEN, fuzz, 3.4),
      brow: make(BROW, "#a8724a", fuzz, 2.4),
      shirt: make(SHIRT, SHIRT_SHEEN, felt, 2.2),
      collar: make(COLLAR, SHIRT_SHEEN, felt, 2.2),
      lip: new THREE.MeshPhysicalMaterial({ color: "#5a1b12", roughness: 0.75, sheen: 0.5, sheenColor: new THREE.Color("#b0544a") }),
      mouth: new THREE.MeshPhysicalMaterial({ color: "#3b0f0b", roughness: 0.6 }),
      tongue: new THREE.MeshPhysicalMaterial({ color: "#d4625a", roughness: 0.55 }),
      sclera: new THREE.MeshPhysicalMaterial({ color: "#f7f1ea", roughness: 0.25, clearcoat: 1, clearcoatRoughness: 0.08 }),
      iris: new THREE.MeshPhysicalMaterial({ map: makeIrisTexture(), roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.05 }),
      glint: new THREE.MeshBasicMaterial({ color: "#ffffff" }),
    };
  }, []);
}

function damp(current: number, target: number, lambda: number, dt: number) {
  return THREE.MathUtils.damp(current, target, lambda, dt);
}

/* ------------------------------------------------------------- Echo */

function Echo({ onReady }: EchoCharacterProps) {
  const m = useMaterials();
  const headGeometry = useMemo(() => makeHeadGeometry(), []);
  // All the hair puffs as one mesh: one draw call instead of sixty.
  const hairGeometry = useMemo(() => {
    const puff = makePuffGeometry();
    const matrix = new THREE.Matrix4();
    const parts = makeHair().map(({ position, scale, rotation }) =>
      puff
        .clone()
        .applyMatrix4(
          matrix.compose(
            new THREE.Vector3(...position),
            new THREE.Quaternion().setFromEuler(new THREE.Euler(...rotation)),
            new THREE.Vector3(...scale),
          ),
        ),
    );
    const merged = mergeGeometries(parts) ?? puff;
    parts.forEach((part) => part.dispose());
    return merged;
  }, []);
  const reduceMotion = useReducedMotion();
  const viewport = useThree((state) => state.viewport);
  const size = useThree((state) => state.size);

  const root = useRef<THREE.Group>(null);
  const head = useRef<THREE.Group>(null);
  const body = useRef<THREE.Group>(null);
  const eyeL = useRef<THREE.Group>(null);
  const eyeR = useRef<THREE.Group>(null);
  const lidL = useRef<THREE.Mesh>(null);
  const lidR = useRef<THREE.Mesh>(null);
  const browL = useRef<THREE.Mesh>(null);
  const browR = useRef<THREE.Mesh>(null);
  const mouthOpen = useRef<THREE.Group>(null);
  const smile = useRef<THREE.Mesh>(null);

  const pointer = useRef(new THREE.Vector2(-0.4, 0.05));
  const hasPointer = useRef(false);
  const mood = useRef<Mood>("idle");
  const moodUntil = useRef(0);
  const nextBlink = useRef(1.6);
  const blink = useRef(0);
  const squash = useRef(0);
  const announced = useRef(false);

  useEffect(() => {
    function onMove(event: PointerEvent) {
      hasPointer.current = true;
      pointer.current.set((event.clientX / window.innerWidth) * 2 - 1, -((event.clientY / window.innerHeight) * 2 - 1));
    }
    function onEcho(event: Event) {
      const detail = (event as CustomEvent<{ mood: Mood; ms?: number }>).detail;
      mood.current = detail.mood;
      moodUntil.current = performance.now() + (detail.ms ?? 1600);
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("agi:echo", onEcho);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("agi:echo", onEcho);
    };
  }, []);

  // Desktop: Echo stands on the right. Phones: lower and centred, under the text.
  const portrait = size.width / size.height < 0.9;
  const scale = portrait ? Math.min(1.05, viewport.width / 3.2) : Math.min(1.3, viewport.height / 4.6);
  const x = portrait ? 0 : viewport.width * 0.23;
  const headY = portrait ? -viewport.height * 0.5 + 2.05 * scale : 0.32;

  useFrame((state, delta) => {
    const dt = Math.min(delta, 1 / 30);
    const t = state.clock.elapsedTime;
    if (mood.current !== "idle" && performance.now() > moodUntil.current) mood.current = "idle";
    const animate = !reduceMotion;

    // Where to look: the pointer, or the greeting on the left when nobody's pointing.
    const px = hasPointer.current ? pointer.current.x : -0.55 + Math.sin(t * 0.3) * 0.08;
    const py = hasPointer.current ? pointer.current.y : 0.02 + Math.sin(t * 0.23) * 0.05;
    const ex = THREE.MathUtils.clamp(px - (x / viewport.width) * 2, -1.5, 1.5);
    const ey = THREE.MathUtils.clamp(py - (headY / viewport.height) * 2, -1.3, 1.3);

    if (head.current && animate) {
      head.current.rotation.y = damp(head.current.rotation.y, ex * 0.4, 4, dt);
      head.current.rotation.x = damp(head.current.rotation.x, -ey * 0.2, 4, dt);
      const tilt = mood.current === "curious" ? 0.15 : Math.sin(t * 0.7) * 0.03;
      head.current.rotation.z = damp(head.current.rotation.z, tilt, 3, dt);
      head.current.position.y = Math.sin(t * 1.6) * 0.012;
    }
    for (const eye of [eyeL, eyeR]) {
      if (eye.current && animate) {
        eye.current.rotation.y = damp(eye.current.rotation.y, ex * 0.36, 12, dt);
        eye.current.rotation.x = damp(eye.current.rotation.x, -ey * 0.3, 12, dt);
      }
    }
    if (body.current && animate) {
      body.current.scale.y = 1 + Math.sin(t * 1.6) * 0.012;
      body.current.rotation.y = damp(body.current.rotation.y, ex * 0.08, 2, dt);
    }

    // Blinks every few seconds, sometimes twice in a row.
    if (animate) {
      nextBlink.current -= dt;
      if (nextBlink.current <= 0) {
        blink.current = 1;
        nextBlink.current = Math.random() < 0.18 ? 0.3 : 2.4 + Math.random() * 3.2;
      }
      blink.current = Math.max(0, blink.current - dt * 6.5);
    }
    const close = Math.max(Math.sin(Math.min(1, blink.current) * Math.PI), mood.current === "happy" ? 0.4 : 0);
    for (const lid of [lidL, lidR]) {
      if (lid.current) lid.current.rotation.x = THREE.MathUtils.lerp(-1.3, 0.12, close);
    }

    // Brows lift when Echo is curious or pleased.
    const lift = mood.current === "curious" ? 0.08 : mood.current === "happy" ? 0.05 : 0;
    for (const [brow, side] of [
      [browL, -1],
      [browR, 1],
    ] as const) {
      if (!brow.current) continue;
      brow.current.position.y = damp(brow.current.position.y, 0.47 + lift, 8, dt);
      brow.current.rotation.z = damp(brow.current.rotation.z, Math.PI / 2 + side * (0.1 + lift * 1.6), 8, dt);
    }

    // Talking: the mouth opens and closes with a little noise.
    const talking = mood.current === "talk" && animate;
    const open = talking
      ? Math.max(0, Math.sin(t * 13) * 0.55 + Math.sin(t * 7.3) * 0.45)
      : mood.current === "happy"
        ? 0.55
        : 0;
    if (mouthOpen.current) {
      const s = mouthOpen.current.scale;
      s.y = damp(s.y, 0.05 + open, 18, dt);
      s.x = damp(s.x, 1 - open * 0.12, 18, dt);
      mouthOpen.current.visible = s.y > 0.08;
    }
    if (smile.current) smile.current.visible = open < 0.25;

    // A springy squash when clicked.
    if (root.current) {
      squash.current = damp(squash.current, 0, 5, dt);
      const k = Math.sin(t * 22) * squash.current;
      root.current.scale.set(scale * (1 + k * 0.05), scale * (1 - k * 0.06), scale);
    }

    if (!announced.current) {
      announced.current = true;
      requestAnimationFrame(() => onReady?.());
    }
  });

  const eye = { x: 0.31, y: 0.2, r: 0.2 };
  const mouth = { y: -0.37, r: 0.15 };
  const smileArc = Math.PI * 0.72;

  return (
    <group ref={root} position={[x, headY, 0]} scale={scale}>
      {/* Shirt and shoulders. */}
      <group ref={body} position={[0, -1.98, -0.12]}>
        <mesh material={m.shirt} scale={[1.3, 0.92, 0.76]} castShadow receiveShadow>
          <sphereGeometry args={[1, 48, 32]} />
        </mesh>
        {[-1, 1].map((side) => (
          <mesh
            key={side}
            material={m.collar}
            position={[side * 0.2, 0.74, 0.36]}
            rotation={[0.95, side * -0.3, side * -0.75]}
            scale={[0.24, 0.05, 0.19]}
            castShadow
          >
            <sphereGeometry args={[1, 24, 16]} />
          </mesh>
        ))}
      </group>

      {/* Neck. */}
      <mesh material={m.neck} position={[0, -1.0, -0.08]} castShadow receiveShadow>
        <cylinderGeometry args={[0.27, 0.31, 0.5, 32]} />
      </mesh>

      <group
        ref={head}
        onClick={(event) => {
          event.stopPropagation();
          squash.current = 1;
          mood.current = "happy";
          moodUntil.current = performance.now() + 1400;
        }}
      >
        <mesh geometry={headGeometry} material={m.skin} castShadow receiveShadow />

        {/* Ears. */}
        {[-1, 1].map((side) => (
          <mesh key={side} material={m.skin} position={[side * 0.99, -0.04, -0.04]} scale={[0.13, 0.22, 0.17]} castShadow>
            <sphereGeometry args={[1, 24, 16]} />
          </mesh>
        ))}

        {/* Hair. */}
        <mesh geometry={hairGeometry} material={m.hair} castShadow receiveShadow />

        {/* Brows. */}
        <mesh ref={browL} material={m.brow} position={[-0.32, 0.47, faceZ(0.32, 0.47, 0.05)]} rotation={[0.45, -0.32, Math.PI / 2 - 0.1]} castShadow>
          <capsuleGeometry args={[0.062, 0.24, 8, 16]} />
        </mesh>
        <mesh ref={browR} material={m.brow} position={[0.32, 0.47, faceZ(0.32, 0.47, 0.05)]} rotation={[0.45, 0.32, Math.PI / 2 + 0.1]} castShadow>
          <capsuleGeometry args={[0.062, 0.24, 8, 16]} />
        </mesh>

        {/* Eyes: white, an iris that follows the pointer, a lid that blinks, a glint that stays put. */}
        {(
          [
            [-1, eyeL, lidL],
            [1, eyeR, lidR],
          ] as const
        ).map(([side, eyeRef, lidRef]) => (
          <group key={side} position={[side * eye.x, eye.y, faceZ(eye.x, eye.y, -0.09)]} rotation={[0, side * 0.18, 0]}>
            <mesh material={m.sclera} scale={[1, 1.14, 0.8]}>
              <sphereGeometry args={[eye.r, 40, 28]} />
            </mesh>
            <group ref={eyeRef}>
              <mesh material={m.iris} position={[0, 0, eye.r * 0.66]} scale={[1, 1, 0.42]}>
                <sphereGeometry args={[eye.r * 0.64, 40, 28]} />
              </mesh>
            </group>
            <mesh ref={lidRef} material={m.skin} rotation={[-1.3, 0, 0]} scale={[1.07, 1.18, 0.88]}>
              <sphereGeometry args={[eye.r * 1.03, 36, 18, 0, Math.PI * 2, 0, Math.PI / 2]} />
            </mesh>
            <mesh material={m.glint} position={[-0.055, 0.075, eye.r * 0.92]}>
              <sphereGeometry args={[0.027, 12, 8]} />
            </mesh>
            <mesh material={m.glint} position={[0.04, -0.03, eye.r * 0.95]}>
              <sphereGeometry args={[0.012, 10, 6]} />
            </mesh>
          </group>
        ))}

        {/* Nose and cheeks. */}
        <mesh material={m.nose} position={[0, -0.04, faceZ(0, -0.04, 0.04)]} scale={[1.05, 0.88, 0.9]} castShadow>
          <sphereGeometry args={[0.16, 32, 24]} />
        </mesh>
        {[-1, 1].map((side) => (
          <mesh
            key={side}
            material={m.cheek}
            position={[side * 0.56, -0.16, faceZ(0.56, -0.16, -0.03)]}
            rotation={[0.1, side * 0.62, 0]}
            scale={[0.19, 0.14, 0.07]}
          >
            <sphereGeometry args={[1, 24, 16]} />
          </mesh>
        ))}

        {/* Mouth: a smile at rest, opening while Echo talks. */}
        <mesh
          ref={smile}
          material={m.lip}
          position={[0, mouth.y + mouth.r, faceZ(0, mouth.y, 0.016 + mouth.r * Math.sin(0.15))]}
          rotation={[0.15, 0, -Math.PI / 2 - smileArc / 2]}
        >
          <torusGeometry args={[mouth.r, 0.026, 12, 32, smileArc]} />
        </mesh>
        <group ref={mouthOpen} position={[0, mouth.y + 0.03, faceZ(0, mouth.y, -0.015)]} rotation={[0.3, 0, 0]} scale={[1, 0.05, 1]}>
          <mesh material={m.mouth} scale={[0.17, 0.14, 0.08]}>
            <sphereGeometry args={[1, 24, 16]} />
          </mesh>
          <mesh material={m.tongue} position={[0, -0.06, 0.03]} scale={[0.1, 0.06, 0.05]}>
            <sphereGeometry args={[1, 16, 12]} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

function EchoCharacter(props: EchoCharacterProps) {
  const host = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

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
        shadows
        dpr={[1, 1.75]}
        frameloop={visible ? "always" : "never"}
        camera={{ position: [0, 0.1, 9], fov: 30 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        aria-hidden
      >
        <hemisphereLight args={["#ffe6dc", "#a3150d", 0.9]} />
        <directionalLight
          position={[-3.2, 4.2, 5]}
          intensity={2.6}
          color="#fff1e4"
          castShadow
          shadow-mapSize={[1024, 1024]}
          shadow-bias={-0.0004}
          shadow-normalBias={0.02}
        />
        <directionalLight position={[4.5, 1.5, -4]} intensity={2.2} color="#ffd6c8" />
        <directionalLight position={[4, -1, 3]} intensity={0.7} color="#ff7a68" />
        <Environment resolution={128}>
          <Lightformer form="rect" intensity={2.2} color="#fff4ea" position={[-4, 3, 4]} scale={[5, 4, 1]} />
          <Lightformer form="rect" intensity={1.4} color="#ff5a48" position={[4, -1, 2]} scale={[6, 6, 1]} />
          <Lightformer form="ring" intensity={1.2} color="#ffffff" position={[3, 4, -4]} scale={3} />
        </Environment>
        <Echo {...props} />
      </Canvas>
    </div>
  );
}

export default EchoCharacter;

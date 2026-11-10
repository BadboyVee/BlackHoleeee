import { Environment, Float, Lightformer, PerspectiveCamera, RoundedBox, View } from '@react-three/drei'
import { Canvas, useFrame } from '@react-three/fiber'
import { useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import * as THREE from 'three'
import { site, type Project } from '../content/site'
import { clamp, damp, smoothstep } from '../lib/math'
import { quality } from '../lib/quality'
import { scroll } from '../lib/scroll'
import { useLoad } from '../lib/store'

/* ------------------------------------------------------------------ */
/* Shared canvas: every 3D model on the page renders through one WebGL */
/* context, scissored into the DOM element each <View> tracks.         */
/* ------------------------------------------------------------------ */

export function SceneCanvas() {
  return (
    <div className="gl-layer" style={{ zIndex: -1 }} aria-hidden="true">
      <Canvas
        frameloop="never"
        dpr={quality.sceneDpr}
        eventSource={document.getElementById('root')!}
        eventPrefix="client"
        resize={{ scroll: false, debounce: { scroll: 0, resize: 120 } }}
        style={{ pointerEvents: 'none' }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        onCreated={() => useLoad.getState().report('scene', 1)}
      >
        <View.Port />
      </Canvas>
    </div>
  )
}

const pointer = { x: 0, y: 0 }
if (typeof window !== 'undefined') {
  window.addEventListener(
    'pointermove',
    (e) => {
      pointer.x = e.clientX
      pointer.y = e.clientY
    },
    { passive: true },
  )
}

/** Pointer position in [-1, 1] relative to an element. */
function localPointer(el: HTMLElement | null) {
  if (!el) return { x: 0, y: 0, inside: false }
  const r = el.getBoundingClientRect()
  const x = ((pointer.x - r.left) / r.width) * 2 - 1
  const y = -(((pointer.y - r.top) / r.height) * 2 - 1)
  return { x, y, inside: Math.abs(x) <= 1 && Math.abs(y) <= 1 }
}

/** Studio light rig baked into an environment map, so no HDR download is needed. */
function Studio({ warm = 1 }: { warm?: number }) {
  return (
    <>
      <ambientLight intensity={0.25} />
      <directionalLight position={[3, 6, 5]} intensity={1.6} />
      <Environment resolution={256} frames={1}>
        <Lightformer form="rect" intensity={4} position={[0, 6, 0]} rotation-x={Math.PI / 2} scale={[12, 4, 1]} />
        <Lightformer form="rect" intensity={3 * warm} color="#ff6a2b" position={[-6, 1, 2]} rotation-y={Math.PI / 2} scale={[4, 8, 1]} />
        <Lightformer form="rect" intensity={1.6} color="#a9bcff" position={[6, 2, 1]} rotation-y={-Math.PI / 2} scale={[4, 8, 1]} />
        <Lightformer form="ring" intensity={2} position={[0, 2, 7]} scale={4} />
      </Environment>
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Laptop                                                              */
/* ------------------------------------------------------------------ */

export type WorkState = { progress: number; active: number }

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, r)
}

/** Paints a mock website for a project onto a canvas. */
function drawScreen(p: Project, W = 1024, H = 640) {
  const c = document.createElement('canvas')
  c.width = W
  c.height = H
  const ctx = c.getContext('2d')!
  const s = p.screen
  ctx.fillStyle = s.bg
  ctx.fillRect(0, 0, W, H)

  // Visual per layout.
  ctx.save()
  if (s.layout === 'finance') {
    const g = ctx.createRadialGradient(760, 260, 10, 760, 260, 420)
    g.addColorStop(0, s.accent + 'aa')
    g.addColorStop(0.5, s.accent2 + '55')
    g.addColorStop(1, s.bg + '00')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, W, H)
    ctx.strokeStyle = s.accent
    ctx.lineWidth = 4
    ctx.shadowColor = s.accent
    ctx.shadowBlur = 18
    ctx.beginPath()
    for (let i = 0; i <= 40; i++) {
      const x = 520 + i * 11
      const y = 430 - i * 4.2 - Math.sin(i * 0.7) * 26 - Math.sin(i * 0.23) * 30
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.stroke()
  } else if (s.layout === 'music') {
    for (let i = 0; i < 14; i++) {
      ctx.strokeStyle = i % 3 === 0 ? s.accent : s.fg + '33'
      ctx.lineWidth = i % 3 === 0 ? 3 : 1.5
      ctx.beginPath()
      ctx.arc(760, 330, 40 + i * 17, 0, Math.PI * 2)
      ctx.stroke()
    }
    ctx.fillStyle = s.accent2
    ctx.beginPath()
    ctx.arc(760, 330, 30, 0, Math.PI * 2)
    ctx.fill()
    for (let i = 0; i < 48; i++) {
      const h = 12 + Math.abs(Math.sin(i * 0.9) * 60) + (i % 5) * 6
      ctx.fillStyle = s.accent + 'cc'
      ctx.fillRect(60 + i * 9, 560 - h, 5, h)
    }
  } else if (s.layout === 'commerce') {
    const g = ctx.createRadialGradient(740, 330, 20, 740, 330, 230)
    g.addColorStop(0, s.accent)
    g.addColorStop(1, s.accent2)
    ctx.fillStyle = g
    roundRect(ctx, 600, 150, 280, 360, 120)
    ctx.fill()
    ctx.fillStyle = s.fg
    ctx.fillRect(650, 250, 180, 10)
    ;[s.accent, s.accent2, s.fg, '#c9b68f'].forEach((col, i) => {
      ctx.fillStyle = col
      ctx.beginPath()
      ctx.arc(620 + i * 40, 560, 13, 0, Math.PI * 2)
      ctx.fill()
    })
  } else if (s.layout === 'type') {
    ctx.fillStyle = s.fg
    ctx.font = '900 300px "Archivo Variable", sans-serif'
    ctx.fillText('Aa', 520, 470)
    ctx.strokeStyle = s.fg + '55'
    for (let i = 0; i < 10; i++) {
      ctx.beginPath()
      ctx.moveTo(0, 120 + i * 52)
      ctx.lineTo(W, 120 + i * 52)
      ctx.stroke()
    }
  } else {
    for (let r = 0; r < 3; r++)
      for (let k = 0; k < 3; k++) {
        ctx.fillStyle = '#ffffff'
        ctx.shadowColor = 'rgba(0,0,0,0.08)'
        ctx.shadowBlur = 20
        roundRect(ctx, 560 + k * 140, 150 + r * 130, 120, 110, 16)
        ctx.fill()
        ctx.shadowBlur = 0
        ctx.fillStyle = (r + k) % 2 ? s.accent : s.accent2
        roundRect(ctx, 578 + k * 140, 170 + r * 130, 50, 18, 9)
        ctx.fill()
        ctx.fillStyle = s.fg + '22'
        ctx.fillRect(578 + k * 140, 205 + r * 130, 84, 8)
        ctx.fillRect(578 + k * 140, 222 + r * 130, 60, 8)
      }
  }
  ctx.restore()

  // Browser chrome.
  ctx.fillStyle = s.fg + '14'
  ctx.fillRect(0, 0, W, 44)
  ;['#ff5f57', '#febc2e', '#28c840'].forEach((col, i) => {
    ctx.fillStyle = col
    ctx.beginPath()
    ctx.arc(24 + i * 20, 22, 6, 0, Math.PI * 2)
    ctx.fill()
  })
  ctx.fillStyle = s.fg + '18'
  roundRect(ctx, W / 2 - 160, 11, 320, 22, 11)
  ctx.fill()
  ctx.fillStyle = s.fg + 'aa'
  ctx.font = '500 13px "JetBrains Mono Variable", monospace'
  ctx.textAlign = 'center'
  ctx.fillText(s.url, W / 2, 27)
  ctx.textAlign = 'left'

  // Nav.
  ctx.fillStyle = s.fg
  ctx.font = '800 20px "Archivo Variable", sans-serif'
  ctx.fillText(p.title.split(' ')[0].toUpperCase(), 56, 96)
  ctx.font = '500 14px "Archivo Variable", sans-serif'
  ;['Work', 'About', 'Journal'].forEach((t, i) => ctx.fillText(t, 640 + i * 90, 96))
  ctx.fillStyle = s.accent
  roundRect(ctx, 900, 74, 76, 32, 16)
  ctx.fill()

  // Headline.
  ctx.fillStyle = s.fg
  ctx.font = `800 ${s.layout === 'type' ? 64 : 70}px "Archivo Variable", sans-serif`
  ctx.fillText(s.headline[0], 56, 250)
  ctx.font = 'italic 400 76px "Instrument Serif", serif'
  ctx.fillText(s.headline[1], 56, 330)
  ctx.font = '400 17px "Archivo Variable", sans-serif'
  ctx.fillStyle = s.fg + 'aa'
  ctx.fillText(p.kind, 58, 380)
  ctx.fillStyle = s.layout === 'type' ? s.fg : s.accent
  roundRect(ctx, 56, 410, 170, 50, 25)
  ctx.fill()
  ctx.fillStyle = s.layout === 'type' ? s.bg : s.bg
  ctx.font = '700 15px "Archivo Variable", sans-serif'
  ctx.fillText('Explore  →', 92, 441)

  const tex = new THREE.CanvasTexture(c)
  tex.colorSpace = THREE.SRGBColorSpace
  tex.anisotropy = 8
  return tex
}

function useScreens() {
  const [textures, setTextures] = useState<THREE.CanvasTexture[] | null>(null)
  useEffect(() => {
    let alive = true
    let made: THREE.CanvasTexture[] = []
    document.fonts.ready.then(() => {
      if (!alive) return
      made = site.projects.map((p) => drawScreen(p))
      setTextures(made)
    })
    return () => {
      alive = false
      made.forEach((t) => t.dispose())
    }
  }, [])
  return textures
}

function Laptop({ state, track }: { state: WorkState; track: RefObject<HTMLElement | null> }) {
  const group = useRef<THREE.Group>(null)
  const lid = useRef<THREE.Group>(null)
  const textures = useScreens()
  const screen = useMemo(() => new THREE.MeshBasicMaterial({ color: '#000', toneMapped: false }), [])
  const shown = useRef(-1)
  const flash = useRef(0)

  const keys = useMemo(() => {
    const list: [number, number][] = []
    for (let r = 0; r < 5; r++) for (let k = 0; k < 13; k++) list.push([-1.29 + k * 0.215, -0.82 + r * 0.215])
    return list
  }, [])

  // All 65 keys in one draw call.
  const keyboard = useRef<THREE.InstancedMesh>(null)
  useEffect(() => {
    const mesh = keyboard.current
    if (!mesh) return
    const m = new THREE.Matrix4()
    keys.forEach(([x, z], i) => mesh.setMatrixAt(i, m.makeTranslation(x, 0.095, z - 0.12)))
    mesh.instanceMatrix.needsUpdate = true
  }, [keys])

  useFrame((st, dt) => {
    if (!group.current || !lid.current) return
    const p = state.progress
    const open = smoothstep(0.0, 0.14, p)
    const m = localPointer(track.current)
    lid.current.rotation.x = damp(lid.current.rotation.x, -open * 1.92, 5, dt)
    const sway = Math.sin(state.active * 2.1) * 0.16
    group.current.rotation.y = damp(group.current.rotation.y, -0.75 + open * 0.55 + sway + m.x * 0.12, 3, dt)
    group.current.rotation.x = damp(group.current.rotation.x, 0.08 - m.y * 0.06, 3, dt)
    group.current.position.y = -0.55 + Math.sin(st.clock.elapsedTime * 0.9) * 0.04

    if (textures && shown.current !== state.active) {
      shown.current = state.active
      screen.map = textures[state.active]
      screen.needsUpdate = true
      flash.current = 1
    }
    flash.current = Math.max(0, flash.current - dt * 2.5)
    const power = smoothstep(0.55, 1, open)
    screen.color.setScalar(textures ? power * (1 + flash.current * 0.6) : 0)
  })

  const alu = useMemo(() => new THREE.MeshStandardMaterial({ color: '#25262b', metalness: 0.85, roughness: 0.32 }), [])
  const keyMat = useMemo(() => new THREE.MeshStandardMaterial({ color: '#0c0c0e', roughness: 0.55 }), [])

  return (
    <group ref={group} scale={1.05}>
      {/* base */}
      <RoundedBox args={[3.2, 0.09, 2.2]} radius={0.04} smoothness={4} position={[0, 0.045, 0]} material={alu} />
      <instancedMesh ref={keyboard} args={[undefined, keyMat, keys.length]}>
        <boxGeometry args={[0.18, 0.02, 0.18]} />
      </instancedMesh>
      <mesh position={[0, 0.092, 0.68]} rotation-x={-Math.PI / 2}>
        <planeGeometry args={[1.25, 0.68]} />
        <meshStandardMaterial color="#1b1c20" metalness={0.6} roughness={0.25} />
      </mesh>
      {/* lid, hinged at the back edge */}
      <group ref={lid} position={[0, 0.09, -1.1]}>
        <RoundedBox args={[3.2, 0.06, 2.2]} radius={0.03} smoothness={4} position={[0, 0.03, 1.1]} material={alu} />
        <mesh position={[0, -0.002, 1.1]} rotation-x={Math.PI / 2}>
          <planeGeometry args={[3.08, 2.08]} />
          <meshStandardMaterial color="#030303" roughness={0.15} />
        </mesh>
        <mesh position={[0, -0.004, 1.16]} rotation-x={Math.PI / 2} material={screen}>
          <planeGeometry args={[2.88, 1.8]} />
        </mesh>
      </group>
      {/* soft shadow */}
      <mesh position={[0, -0.01, 0]} rotation-x={-Math.PI / 2}>
        <planeGeometry args={[5, 4]} />
        <meshBasicMaterial transparent opacity={0.55} depthWrite={false} map={shadowTexture()} />
      </mesh>
    </group>
  )
}

let shadowTex: THREE.Texture | null = null
function shadowTexture() {
  if (shadowTex) return shadowTex
  const c = document.createElement('canvas')
  c.width = c.height = 128
  const ctx = c.getContext('2d')!
  const g = ctx.createRadialGradient(64, 64, 4, 64, 64, 64)
  g.addColorStop(0, 'rgba(0,0,0,0.9)')
  g.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, 128, 128)
  shadowTex = new THREE.CanvasTexture(c)
  return shadowTex
}

export function LaptopView({ state }: { state: WorkState }) {
  const track = useRef<HTMLDivElement>(null)
  return (
    <View ref={track} className="absolute inset-0">
      <PerspectiveCamera makeDefault position={[0, 2.2, 7.4]} fov={30} onUpdate={(c) => c.lookAt(0, 0.35, 0)} />
      <Studio />
      <Laptop state={state} track={track} />
    </View>
  )
}

/* ------------------------------------------------------------------ */
/* Gravity orbs: the toolkit as spheres pulled into a well. The pointer */
/* pushes them away; click to set off a small big bang.                 */
/* ------------------------------------------------------------------ */

const ORB_STYLES = [
  { base: '#ff5b1f', ink: '#120d0a', metal: 0, rough: 0.28 },
  { base: '#101015', ink: '#f1ece3', metal: 0, rough: 0.18 },
  { base: '#efe9df', ink: '#120d0a', metal: 0, rough: 0.35 },
  { base: '#d8d8dc', ink: '#120d0a', metal: 1, rough: 0.14 },
]

function labelTexture(text: string, base: string, ink: string) {
  const c = document.createElement('canvas')
  c.width = 512
  c.height = 256
  const ctx = c.getContext('2d')!
  ctx.fillStyle = base
  ctx.fillRect(0, 0, 512, 256)
  ctx.fillStyle = ink
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const size = text.length > 7 ? 30 : text.length > 4 ? 38 : 46
  ctx.font = `800 ${size}px "Archivo Variable", sans-serif`
  ctx.fillText(text, 128, 128) // u = 0.25 faces the camera on a three.js sphere
  const t = new THREE.CanvasTexture(c)
  t.colorSpace = THREE.SRGBColorSpace
  t.anisotropy = 8
  return t
}

type Body = { p: THREE.Vector3; v: THREE.Vector3; r: number }

function Orbs({ track }: { track: RefObject<HTMLElement | null> }) {
  const labels = site.toolkit.orbs.slice(0, quality.orbCount)
  const meshes = useRef<(THREE.Mesh | null)[]>([])
  const [materials, setMaterials] = useState<THREE.MeshPhysicalMaterial[] | null>(null)
  const geometry = useMemo(() => new THREE.SphereGeometry(1, 40, 24), [])

  const bodies = useMemo<Body[]>(
    () =>
      labels.map((_, i) => ({
        p: new THREE.Vector3(Math.cos(i * 2.4) * (2 + i * 0.35), 3 + Math.sin(i * 2.4) * (2 + i * 0.35), ((i % 3) - 1) * 0.6),
        v: new THREE.Vector3(),
        r: 0.72 + ((i * 37) % 10) * 0.045,
      })),
    [labels],
  )

  useEffect(() => {
    let alive = true
    let mats: THREE.MeshPhysicalMaterial[] = []
    document.fonts.ready.then(() => {
      if (!alive) return
      mats = labels.map((text, i) => {
        const s = ORB_STYLES[i % ORB_STYLES.length]
        return new THREE.MeshPhysicalMaterial({ map: labelTexture(text, s.base, s.ink), metalness: s.metal, roughness: s.rough, clearcoat: 1, clearcoatRoughness: 0.15 })
      })
      setMaterials(mats)
    })
    return () => {
      alive = false
      mats.forEach((m) => {
        m.map?.dispose()
        m.dispose()
      })
    }
  }, [labels])

  const active = useRef(false)
  useEffect(() => {
    const el = track.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => (active.current = e.isIntersecting), { threshold: 0.1 })
    io.observe(el)
    const bang = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      if (e.clientY < r.top || e.clientY > r.bottom) return
      bodies.forEach((b) => {
        const d = b.p.clone().setZ(0)
        const len = Math.max(d.length(), 0.5)
        b.v.addScaledVector(d.normalize(), 22 / len + 6)
      })
    }
    window.addEventListener('pointerdown', bang)
    return () => {
      io.disconnect()
      window.removeEventListener('pointerdown', bang)
    }
  }, [bodies, track])

  const tmp = useMemo(() => new THREE.Vector3(), [])
  useFrame((st, delta) => {
    if (!active.current) return
    const dt = Math.min(delta, 1 / 20)
    const m = localPointer(track.current)
    const cam = st.camera as THREE.PerspectiveCamera
    const halfH = Math.tan((cam.fov * Math.PI) / 360) * cam.position.z
    const halfW = halfH * cam.aspect
    const mouse = tmp.set(m.x * halfW, m.y * halfH, 0)
    const steps = 2
    const h = dt / steps
    for (let s = 0; s < steps; s++) {
      for (const b of bodies) {
        // gravity well towards the centre, plus damping
        b.v.addScaledVector(b.p, -2.2 * h)
        b.v.z += -b.p.z * 6 * h
        b.v.multiplyScalar(1 - 1.6 * h)
        if (m.inside) {
          const dx = b.p.x - mouse.x
          const dy = b.p.y - mouse.y
          const d2 = dx * dx + dy * dy
          const reach = 2.6 + b.r
          if (d2 < reach * reach) {
            const d = Math.sqrt(d2) || 0.001
            const f = (1 - d / reach) * 90 * h
            b.v.x += (dx / d) * f
            b.v.y += (dy / d) * f
          }
        }
      }
      for (let i = 0; i < bodies.length; i++)
        for (let j = i + 1; j < bodies.length; j++) {
          const a = bodies[i]
          const b = bodies[j]
          const dx = b.p.x - a.p.x
          const dy = b.p.y - a.p.y
          const dz = b.p.z - a.p.z
          const min = a.r + b.r
          const d2 = dx * dx + dy * dy + dz * dz
          if (d2 < min * min && d2 > 1e-6) {
            const d = Math.sqrt(d2)
            const push = (min - d) / 2
            const nx = dx / d
            const ny = dy / d
            const nz = dz / d
            a.p.x -= nx * push
            a.p.y -= ny * push
            a.p.z -= nz * push
            b.p.x += nx * push
            b.p.y += ny * push
            b.p.z += nz * push
            const rel = (b.v.x - a.v.x) * nx + (b.v.y - a.v.y) * ny + (b.v.z - a.v.z) * nz
            if (rel < 0) {
              const k = rel * 0.8
              a.v.x += nx * k
              a.v.y += ny * k
              a.v.z += nz * k
              b.v.x -= nx * k
              b.v.y -= ny * k
              b.v.z -= nz * k
            }
          }
        }
      for (const b of bodies) {
        b.p.addScaledVector(b.v, h)
        b.p.x = clamp(b.p.x, -halfW + b.r, halfW - b.r)
      }
    }
    bodies.forEach((b, i) => {
      const mesh = meshes.current[i]
      if (!mesh) return
      mesh.position.copy(b.p)
      mesh.scale.setScalar(b.r)
      mesh.rotation.z = damp(mesh.rotation.z, clamp(-b.v.x * 0.05, -0.5, 0.5), 4, dt)
      mesh.rotation.x = damp(mesh.rotation.x, clamp(b.v.y * 0.05, -0.5, 0.5), 4, dt)
    })
  })

  if (!materials) return null
  return (
    <group>
      {labels.map((label, i) => (
        <mesh key={label} ref={(m) => void (meshes.current[i] = m)} geometry={geometry} material={materials[i]} />
      ))}
    </group>
  )
}

export function OrbsView() {
  const track = useRef<HTMLDivElement>(null)
  return (
    <View ref={track} className="absolute inset-0">
      <PerspectiveCamera makeDefault position={[0, 0, 16]} fov={34} />
      <Studio />
      <Orbs track={track} />
    </View>
  )
}

/* ------------------------------------------------------------------ */
/* Sculpture: a glass knot circled by chrome rings (About section).     */
/* ------------------------------------------------------------------ */

function Sculpture({ track }: { track: RefObject<HTMLElement | null> }) {
  const group = useRef<THREE.Group>(null)
  const rings = useRef<THREE.Group>(null)
  useFrame((st, dt) => {
    if (!group.current || !rings.current) return
    const m = localPointer(track.current)
    const t = st.clock.elapsedTime
    group.current.rotation.y = damp(group.current.rotation.y, scroll.y * 0.0012 + m.x * 0.4, 3, dt)
    group.current.rotation.x = damp(group.current.rotation.x, -m.y * 0.3, 3, dt)
    rings.current.rotation.x = t * 0.35
    rings.current.rotation.z = t * 0.22
  })
  return (
    <Float speed={1.4} rotationIntensity={0.4} floatIntensity={0.8}>
      <group ref={group}>
        <mesh>
          <torusKnotGeometry args={[1, 0.34, 160, 28, 2, 3]} />
          <meshPhysicalMaterial color="#f3ece4" metalness={1} roughness={0.14} iridescence={0.9} iridescenceIOR={1.6} iridescenceThicknessRange={[180, 820]} clearcoat={1} clearcoatRoughness={0.08} />
        </mesh>
        <group ref={rings}>
          <mesh rotation-x={Math.PI / 2}>
            <torusGeometry args={[2.05, 0.035, 16, 160]} />
            <meshStandardMaterial color="#ff5b1f" metalness={1} roughness={0.2} emissive="#ff5b1f" emissiveIntensity={0.6} />
          </mesh>
          <mesh rotation-y={Math.PI / 2.6}>
            <torusGeometry args={[2.35, 0.025, 16, 160]} />
            <meshStandardMaterial color="#e8e8ec" metalness={1} roughness={0.1} />
          </mesh>
        </group>
      </group>
    </Float>
  )
}

export function SculptureView({ className = 'absolute inset-0' }: { className?: string }) {
  const track = useRef<HTMLDivElement>(null)
  return (
    <View ref={track} className={className}>
      <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={35} />
      <Studio warm={1.3} />
      <Sculpture track={track} />
    </View>
  )
}

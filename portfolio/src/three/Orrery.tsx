import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import {
  BoxGeometry,
  Color,
  type Group,
  IcosahedronGeometry,
  type InstancedMesh,
  type Mesh,
  MeshBasicMaterial,
  MeshStandardMaterial,
  Object3D,
  SphereGeometry,
  TorusGeometry,
} from 'three'
import { ORRERY_POSITION } from '../lib/rig'
import { store } from '../lib/store'

// An armillary sphere: one ring per capability listed in the Stack section.
// Hovering a row on the page lights up and speeds up its ring here.

interface Ring {
  radius: number
  tube: number
  tilt: [number, number, number]
  speed: number
  bead: number
}

export const ORRERY_RINGS: Ring[] = [
  { radius: 1.15, tube: 0.02, tilt: [0.55, 0.0, 0.3], speed: 0.62, bead: 0.085 },
  { radius: 1.62, tube: 0.018, tilt: [1.25, 0.4, 0.0], speed: -0.46, bead: 0.07 },
  { radius: 2.1, tube: 0.024, tilt: [0.2, 0.0, 1.1], speed: 0.34, bead: 0.105 },
  { radius: 2.58, tube: 0.018, tilt: [1.45, 0.2, 0.5], speed: -0.27, bead: 0.075 },
  { radius: 3.06, tube: 0.026, tilt: [0.8, 0.9, 0.1], speed: 0.2, bead: 0.115 },
  { radius: 3.54, tube: 0.02, tilt: [0.1, 0.3, -0.5], speed: -0.15, bead: 0.09 },
]

const TICKS = 96
const BONE = new Color('#cfc7b6')
const EMBER = new Color('#ff5a1f')

export function Orrery() {
  const root = useRef<Group>(null)
  const spinners = useRef<(Group | null)[]>([])
  const shell = useRef<Mesh>(null)
  const ticks = useRef<InstancedMesh>(null)
  const glow = useRef<number[]>(ORRERY_RINGS.map(() => 0))

  const ringGeometries = useMemo(() => ORRERY_RINGS.map((r) => new TorusGeometry(r.radius, r.tube, 12, 160)), [])
  const ringMaterials = useMemo(
    () =>
      ORRERY_RINGS.map(
        () => new MeshStandardMaterial({ color: BONE, metalness: 1, roughness: 0.2, emissive: EMBER, emissiveIntensity: 0, envMapIntensity: 1.3 }),
      ),
    [],
  )
  const beadGeometry = useMemo(() => new SphereGeometry(1, 24, 16), [])
  const beadMaterials = useMemo(
    () => ORRERY_RINGS.map(() => new MeshStandardMaterial({ color: '#1b1712', metalness: 1, roughness: 0.3, emissive: EMBER, emissiveIntensity: 1.6 })),
    [],
  )
  const coreMaterial = useMemo(() => new MeshBasicMaterial({ color: new Color(9, 3.1, 0.9), toneMapped: false }), [])
  const shellGeometry = useMemo(() => new IcosahedronGeometry(0.62, 1), [])
  const shellMaterial = useMemo(() => new MeshBasicMaterial({ color: new Color(0.9, 0.82, 0.7), wireframe: true, transparent: true, opacity: 0.55 }), [])
  const frameGeometry = useMemo(() => new TorusGeometry(4.15, 0.034, 12, 200), [])
  const frameMaterial = useMemo(() => new MeshStandardMaterial({ color: '#8f887a', metalness: 1, roughness: 0.32 }), [])
  const tickGeometry = useMemo(() => new BoxGeometry(0.014, 1, 0.014), [])

  // Graduation marks around the outer frame, like the scale on an astrolabe.
  useLayoutEffect(() => {
    const mesh = ticks.current
    if (!mesh) return
    const dummy = new Object3D()
    for (let i = 0; i < TICKS; i++) {
      const a = (i / TICKS) * Math.PI * 2
      const long = i % 8 === 0
      const length = long ? 0.3 : i % 4 === 0 ? 0.19 : 0.1
      const radius = 4.15 - length / 2 - 0.05
      dummy.position.set(Math.cos(a) * radius, Math.sin(a) * radius, 0)
      dummy.rotation.set(0, 0, a - Math.PI / 2)
      dummy.scale.set(long ? 1.6 : 1, length, 1)
      dummy.updateMatrix()
      mesh.setMatrixAt(i, dummy.matrix)
    }
    mesh.instanceMatrix.needsUpdate = true
  }, [])

  useEffect(
    () => () => {
      ringGeometries.forEach((g) => g.dispose())
      ringMaterials.forEach((m) => m.dispose())
      beadMaterials.forEach((m) => m.dispose())
      for (const d of [beadGeometry, coreMaterial, shellGeometry, shellMaterial, frameGeometry, frameMaterial, tickGeometry]) d.dispose()
    },
    [ringGeometries, ringMaterials, beadMaterials, beadGeometry, coreMaterial, shellGeometry, shellMaterial, frameGeometry, frameMaterial, tickGeometry],
  )

  useFrame((state, delta) => {
    const dt = Math.min(delta, 0.1)
    const motion = store.reducedMotion ? 0.15 : 1
    const t = state.clock.elapsedTime

    if (root.current) {
      root.current.rotation.y += dt * 0.07 * motion
      root.current.position.y = ORRERY_POSITION[1] + Math.sin(t * 0.5) * 0.12 * motion
    }
    if (shell.current) {
      shell.current.rotation.x += dt * 0.3 * motion
      shell.current.rotation.y += dt * 0.42 * motion
    }

    ORRERY_RINGS.forEach((ring, i) => {
      const active = store.activeSkill === i
      const dimmed = store.activeSkill !== -1 && !active
      glow.current[i] += ((active ? 1 : 0) - glow.current[i]) * (1 - Math.exp(-dt * 7))
      const g = glow.current[i]

      const spinner = spinners.current[i]
      if (spinner) {
        spinner.rotation.z += dt * ring.speed * (1 + g * 3.5) * motion
        const s = 1 + g * 0.05
        spinner.scale.set(s, s, 1 + g * 1.6)
      }
      ringMaterials[i].emissiveIntensity = g * 3.2
      ringMaterials[i].color.copy(BONE).multiplyScalar(dimmed ? 0.4 : 1)
      beadMaterials[i].emissiveIntensity = 1.6 + g * 6
    })
  })

  return (
    <group ref={root} position={ORRERY_POSITION} rotation={[0.18, 0, 0.12]}>
      {/* The little star at the centre. */}
      <mesh geometry={beadGeometry} material={coreMaterial} scale={0.3} />
      <mesh ref={shell} geometry={shellGeometry} material={shellMaterial} />
      <pointLight color="#ff7a33" intensity={14} distance={12} decay={1.6} />

      {ORRERY_RINGS.map((ring, i) => (
        <group key={i} rotation={ring.tilt}>
          <group
            ref={(el) => {
              spinners.current[i] = el
            }}
          >
            <mesh geometry={ringGeometries[i]} material={ringMaterials[i]} />
            <mesh geometry={beadGeometry} material={beadMaterials[i]} position={[ring.radius, 0, 0]} scale={ring.bead} />
            <mesh geometry={beadGeometry} material={ringMaterials[i]} position={[-ring.radius, 0, 0]} scale={ring.bead * 0.45} />
          </group>
        </group>
      ))}

      {/* Fixed outer frame with graduation marks. */}
      <group rotation={[Math.PI / 2 - 0.35, 0.25, 0]}>
        <mesh geometry={frameGeometry} material={frameMaterial} />
        <instancedMesh ref={ticks} args={[tickGeometry, frameMaterial, TICKS]} />
      </group>
      <mesh geometry={frameGeometry} material={frameMaterial} rotation={[0.2, 1.2, 0.4]} scale={1.045} />
    </group>
  )
}

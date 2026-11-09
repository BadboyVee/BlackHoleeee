import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { prefersReducedMotion } from '../../lib/env'
import { damp, DEG } from '../../lib/math'
import { onQualityChange, quality, sampleFrame } from '../../lib/quality'
import { frame } from '../../lib/scroll'
import { useLoad } from '../../lib/store'
import { fragmentShader, vertexShader } from './blackhole.glsl'
import { extras, target, type Shot } from './shots'

const BG = new THREE.Color('#050507')

if (import.meta.env.DEV) Object.assign(window, { __bh: { target, extras } })

function BlackHole() {
  const gl = useThree((s) => s.gl)
  const setDpr = useThree((s) => s.setDpr)
  const reduced = useMemo(prefersReducedMotion, [])

  const geometry = useMemo(() => {
    // One triangle that covers the screen: cheaper than a quad, no diagonal seam.
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3))
    return g
  }, [])

  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader,
        fragmentShader,
        depthTest: false,
        depthWrite: false,
        uniforms: {
          uResolution: { value: new THREE.Vector2(1, 1) },
          uTime: { value: 0 },
          uCamPos: { value: new THREE.Vector3() },
          uCamRight: { value: new THREE.Vector3() },
          uCamUp: { value: new THREE.Vector3() },
          uCamFwd: { value: new THREE.Vector3() },
          uTanHalfFov: { value: Math.tan(23 * DEG) },
          uShift: { value: new THREE.Vector2() },
          uRoll: { value: 0 },
          uExposure: { value: 1 },
          uDim: { value: 0 },
          uDisk: { value: 1 },
          uStars: { value: 1 },
          uDoppler: { value: 0.55 },
          uSpin: { value: reduced ? 0.4 : 2.2 },
          uSteps: { value: quality.steps },
          uStepScale: { value: quality.stepScale },
          uOctaves: { value: quality.octaves },
          uBg: { value: new THREE.Vector3(BG.r, BG.g, BG.b) },
        },
      }),
    [reduced],
  )

  useEffect(() => () => {
    geometry.dispose()
    material.dispose()
  }, [geometry, material])

  // Resolution follows the adaptive quality controller.
  useEffect(
    () => onQualityChange(() => setDpr(quality.backdropBase * quality.backdropScale)),
    [setDpr],
  )

  // Pointer parallax.
  useEffect(() => {
    const move = (e: PointerEvent) => {
      extras.pointerX = (e.clientX / window.innerWidth) * 2 - 1
      extras.pointerY = (e.clientY / window.innerHeight) * 2 - 1
    }
    window.addEventListener('pointermove', move, { passive: true })
    return () => window.removeEventListener('pointermove', move)
  }, [])

  const live = useRef<Shot>({ ...target })
  const pointer = useRef({ x: 0, y: 0 })
  const vectors = useMemo(
    () => ({ pos: new THREE.Vector3(), fwd: new THREE.Vector3(), right: new THREE.Vector3(), up: new THREE.Vector3(), worldUp: new THREE.Vector3(0, 1, 0), size: new THREE.Vector2() }),
    [],
  )
  const frames = useRef(0)
  const time = useRef(0)

  useFrame((state, delta) => {
    const dt = Math.min(delta, 0.1)
    const s = live.current
    const u = material.uniforms
    sampleFrame(frame.delta)

    // Ease every camera value towards the scroll target.
    for (const key of Object.keys(target) as (keyof Shot)[]) s[key] = damp(s[key], target[key], 3.2, dt)
    pointer.current.x = damp(pointer.current.x, extras.pointerX, 2.5, dt)
    pointer.current.y = damp(pointer.current.y, extras.pointerY, 2.5, dt)

    const intro = extras.intro
    const rush = Math.pow(1 - intro, 3)
    const dist = s.dist + rush * 60
    const elev = (s.elev + rush * 10 - pointer.current.y * 2.2) * DEG
    const az = (s.az - rush * 50 + pointer.current.x * 4.5) * DEG

    const { pos, fwd, right, up, worldUp, size } = vectors
    pos.set(Math.cos(elev) * Math.sin(az), Math.sin(elev), Math.cos(elev) * Math.cos(az)).multiplyScalar(dist)
    fwd.copy(pos).negate().normalize()
    right.crossVectors(fwd, worldUp).normalize()
    up.crossVectors(right, fwd)

    gl.getDrawingBufferSize(size)
    const aspect = size.x / Math.max(size.y, 1)

    // The disk spins up during the intro, then keeps a steady pace.
    time.current += dt * (0.25 + 0.75 * intro)

    u.uResolution.value.copy(size)
    u.uTime.value = time.current
    u.uCamPos.value.copy(pos)
    u.uCamFwd.value.copy(fwd)
    u.uCamRight.value.copy(right)
    u.uCamUp.value.copy(up)
    u.uTanHalfFov.value = Math.tan((s.fov * DEG) / 2)
    u.uShift.value.set(s.shiftX * aspect, s.shiftY)
    u.uRoll.value = (s.roll + rush * 25) * DEG
    u.uExposure.value = s.exposure * Math.min(1, intro * 1.6)
    u.uDisk.value = s.disk * (0.35 + 0.65 * intro)
    u.uDim.value = s.dim
    u.uSteps.value = quality.steps

    // While the page dims the sky, half the frames are plenty.
    frames.current++
    if (s.dim > 0.6 && frames.current % 2 === 1 && frames.current > 3) return

    state.gl.render(state.scene, state.camera)
    if (frames.current === 2) useLoad.getState().report('backdrop', 1)
  }, 1)

  return <mesh geometry={geometry} material={material} frustumCulled={false} />
}

/** The black hole that sits behind the whole page. */
export default function Backdrop() {
  return (
    <div className="gl-layer" style={{ zIndex: -2 }} aria-hidden="true">
      <Canvas
        frameloop="never"
        dpr={quality.backdropBase}
        flat
        linear
        style={{ pointerEvents: 'none' }}
        resize={{ scroll: false, debounce: { scroll: 0, resize: 120 } }}
        gl={{ antialias: false, alpha: false, depth: false, stencil: false, powerPreference: 'high-performance' }}
      >
        <BlackHole />
      </Canvas>
    </div>
  )
}

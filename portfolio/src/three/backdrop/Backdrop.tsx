import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { prefersReducedMotion } from '../../lib/env'
import { damp, DEG } from '../../lib/math'
import { backdropDpr, onQualityChange, quality, sampleFrame } from '../../lib/quality'
import { frame } from '../../lib/scroll'
import { useLoad } from '../../lib/store'
import { fragmentShader, skyFragmentShader, skyVertexShader, vertexShader } from './blackhole.glsl'
import { extras, target, type Shot } from './shots'

const BG = new THREE.Color('#050507')

if (import.meta.env.DEV) Object.assign(window, { __bh: { target, extras, quality } })

/**
 * Tileable fractal noise baked on the CPU once (256², two channels). The disk
 * shader reads it with two texture lookups instead of evaluating noise.
 */
function makeNoiseTexture(size = 256) {
  let seed = 1337
  const rand = () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  const layer = (periods: number[]) => {
    const grids = periods.map((p) => Float32Array.from({ length: p * p }, rand))
    return (x: number, y: number) => {
      let v = 0
      let amp = 0.5
      let total = 0
      periods.forEach((p, o) => {
        const fx = x * p
        const fy = y * p
        const ix = Math.floor(fx)
        const iy = Math.floor(fy)
        const tx = fx - ix
        const ty = fy - iy
        const sx = tx * tx * (3 - 2 * tx)
        const sy = ty * ty * (3 - 2 * ty)
        const g = grids[o]
        const x0 = ix % p
        const x1 = (ix + 1) % p
        const y0 = (iy % p) * p
        const y1 = ((iy + 1) % p) * p
        const a = g[y0 + x0]
        const b = g[y0 + x1]
        const c = g[y1 + x0]
        const d = g[y1 + x1]
        v += amp * (a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy)
        total += amp
        amp *= 0.5
      })
      return v / total
    }
  }
  const broad = layer([4, 8, 16, 32, 64])
  const fine = layer([8, 16, 32, 64, 128])
  const data = new Uint8Array(size * size * 4)
  for (let y = 0; y < size; y++)
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4
      data[i] = broad(x / size, y / size) * 255
      data[i + 1] = fine(x / size, y / size) * 255
      data[i + 3] = 255
    }
  const tex = new THREE.DataTexture(data, size, size)
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping
  tex.magFilter = tex.minFilter = THREE.LinearFilter
  tex.needsUpdate = true
  return tex
}

/** Renders the procedural starfield and galaxy band into a cube map, once. */
function bakeSky(gl: THREE.WebGLRenderer, size: number) {
  const target = new THREE.WebGLCubeRenderTarget(size, {
    generateMipmaps: true,
    minFilter: THREE.LinearMipmapLinearFilter,
    magFilter: THREE.LinearFilter,
  })
  const scene = new THREE.Scene()
  const geometry = new THREE.SphereGeometry(5, 64, 32)
  const material = new THREE.ShaderMaterial({
    vertexShader: skyVertexShader,
    fragmentShader: skyFragmentShader,
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: { uPixel: { value: Math.PI / 2 / size } },
  })
  scene.add(new THREE.Mesh(geometry, material))
  new THREE.CubeCamera(0.1, 10, target).update(gl, scene)
  geometry.dispose()
  material.dispose()
  return target
}

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
          uSkyLod: { value: 0 },
          uBg: { value: new THREE.Vector3(BG.r, BG.g, BG.b) },
          uSky: { value: null as THREE.CubeTexture | null },
          uNoise: { value: null as THREE.Texture | null },
        },
      }),
    [reduced],
  )

  // Bake the sky and the disk noise once, before the first frame.
  useEffect(() => {
    const sky = bakeSky(gl, quality.skySize)
    const noise = makeNoiseTexture()
    material.uniforms.uSky.value = sky.texture
    material.uniforms.uNoise.value = noise
    return () => {
      sky.dispose()
      noise.dispose()
    }
  }, [gl, material])

  useEffect(
    () => () => {
      geometry.dispose()
      material.dispose()
    },
    [geometry, material],
  )

  // Resolution follows the pixel budget, the window size and the adaptive controller.
  useEffect(() => {
    const update = () => setDpr(backdropDpr())
    update()
    window.addEventListener('resize', update)
    const off = onQualityChange(update)
    return () => {
      window.removeEventListener('resize', update)
      off()
    }
  }, [setDpr])

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
  const lastRender = useRef(-1)

  useFrame((state, delta) => {
    const dt = Math.min(delta, 0.1)
    const s = live.current
    const u = material.uniforms
    sampleFrame(frame.delta)

    // Ease every camera value towards the scroll target.
    for (const key of Object.keys(target) as (keyof Shot)[]) s[key] = damp(s[key], target[key], 3.2, dt)
    pointer.current.x = damp(pointer.current.x, extras.pointerX, 2.5, dt)
    pointer.current.y = damp(pointer.current.y, extras.pointerY, 2.5, dt)

    // The disk spins up during the intro, then keeps a steady pace.
    const intro = extras.intro
    time.current += dt * (0.25 + 0.75 * intro)

    // Frame-rate cap: at most 60 fps (30 while the page dims the sky), even on fast screens.
    frames.current++
    const fps = s.dim > 0.6 ? quality.backdropFps / 2 : quality.backdropFps
    if (frames.current > 3 && frame.time - lastRender.current < 1 / fps - 0.004) return
    lastRender.current = frame.time

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
    const tanHalf = Math.tan((s.fov * DEG) / 2)
    // Sky mip level: how many cube-map texels one screen pixel covers.
    const pixelAngle = (2 * tanHalf) / Math.max(size.y, 1)
    const texelAngle = Math.PI / 2 / quality.skySize

    u.uResolution.value.copy(size)
    u.uTime.value = time.current
    u.uCamPos.value.copy(pos)
    u.uCamFwd.value.copy(fwd)
    u.uCamRight.value.copy(right)
    u.uCamUp.value.copy(up)
    u.uTanHalfFov.value = tanHalf
    u.uShift.value.set(s.shiftX * aspect, s.shiftY)
    u.uRoll.value = (s.roll + rush * 25) * DEG
    u.uExposure.value = s.exposure * Math.min(1, intro * 1.6)
    u.uDisk.value = s.disk * (0.35 + 0.65 * intro)
    u.uDim.value = s.dim
    u.uSteps.value = quality.steps
    u.uSkyLod.value = Math.max(0, Math.log2(pixelAngle / texelAngle))

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

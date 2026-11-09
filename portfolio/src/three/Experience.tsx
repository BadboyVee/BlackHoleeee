import { useEffect, useMemo, useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment, Lightformer, PerformanceMonitor } from '@react-three/drei'
import { Bloom, ChromaticAberration, EffectComposer, ToneMapping, Vignette } from '@react-three/postprocessing'
import { ToneMappingMode } from 'postprocessing'
import { HalfFloatType, Vector2 } from 'three'
import { debug } from '../lib/debug'
import { markSceneReady, on, store } from '../lib/store'
import { BlackHole } from './BlackHole'
import { CameraRig } from './CameraRig'
import { Dust } from './Dust'
import { Glyphs } from './Glyphs'
import { Orrery } from './Orrery'
import type { Quality } from './sceneState'

/** Tells the preloader the scene is really on screen (shaders compiled). */
function ReadySignal() {
  const frames = useRef(0)
  useFrame(() => {
    if (frames.current < 3 && ++frames.current === 3) markSceneReady()
  })
  return null
}

/** A small hand-built studio so the metal picks up warm, on-palette reflections. */
function Studio() {
  return (
    <Environment resolution={256} frames={1}>
      <color attach="background" args={['#020202']} />
      <Lightformer form="ring" intensity={9} color="#ff7a2e" scale={7} position={[-6, 1, -8]} target={[0, 0, 0]} />
      <Lightformer form="rect" intensity={5} color="#ffe2c4" scale={[9, 1.2, 1]} position={[2, 7, -3]} target={[0, 0, 0]} />
      <Lightformer form="rect" intensity={2.2} color="#7fa4ff" scale={[2, 9, 1]} position={[9, 0, 4]} target={[0, 0, 0]} />
      <Lightformer form="circle" intensity={3} color="#ff4b12" scale={3} position={[-3, -7, 5]} target={[0, 0, 0]} />
    </Environment>
  )
}

export default function Experience() {
  const coarse = useMemo(() => window.matchMedia('(pointer: coarse)').matches || window.innerWidth < 820, [])
  const quality: Quality = coarse ? 'low' : 'high'
  const maxDpr = Math.min(window.devicePixelRatio || 1, coarse ? 1.25 : 1.5)
  const minDpr = Math.min(0.6, maxDpr)

  const [dpr, setDpr] = useState(debug.dpr ?? maxDpr)
  const [hidden, setHidden] = useState(store.canvasHidden)
  useEffect(() => on('canvasHidden', () => setHidden(store.canvasHidden)), [])

  const aberration = useMemo(() => new Vector2(0.0007, 0.0005), [])

  return (
    <Canvas
      dpr={dpr}
      // Nothing to draw while an opaque section covers the whole viewport.
      frameloop={hidden ? 'never' : 'always'}
      gl={{ antialias: false, alpha: false, stencil: false, powerPreference: 'high-performance' }}
      camera={{ fov: 34, near: 0.1, far: 400, position: [-5.8, 2.7, 23] }}
      // The canvas is a backdrop: pointer input is read from the window instead.
      events={undefined}
    >
      <color attach="background" args={['#020203']} />

      {/* Step resolution down on slow GPUs, back up when there is headroom. */}
      {debug.dpr === null && (
        <PerformanceMonitor
          bounds={(refresh) => (refresh > 90 ? [50, 90] : [42, 58])}
          flipflops={4}
          onChange={({ factor }) => setDpr(Math.round((minDpr + (maxDpr - minDpr) * factor) * 20) / 20)}
        />
      )}

      <CameraRig />
      <BlackHole quality={quality} />
      <Dust count={coarse ? 500 : 900} />
      <Glyphs />
      <Orrery />

      {/* The disk is the key light for everything else in the scene. */}
      <pointLight position={[0, 0.6, 0]} color="#ff8a3d" intensity={5.5} decay={0} />
      <ambientLight intensity={0.12} color="#9fb4ff" />
      <Studio />

      <EffectComposer multisampling={0} frameBufferType={HalfFloatType} enableNormalPass={false}>
        <Bloom mipmapBlur intensity={0.9} radius={0.82} luminanceThreshold={0.95} luminanceSmoothing={0.25} />
        <ChromaticAberration offset={aberration} radialModulation modulationOffset={0.3} />
        <Vignette offset={0.22} darkness={0.72} />
        <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
      </EffectComposer>

      <ReadySignal />
    </Canvas>
  )
}

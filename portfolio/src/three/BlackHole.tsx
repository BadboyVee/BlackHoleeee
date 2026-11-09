import { useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { BufferGeometry, Float32BufferAttribute, Matrix4, ShaderMaterial } from 'three'
import vertexShader from './shaders/blackhole.vert.glsl?raw'
import fragmentShader from './shaders/blackhole.frag.glsl?raw'
import { debug } from '../lib/debug'
import { store } from '../lib/store'
import { sceneState, type Quality } from './sceneState'

/**
 * The black hole and the whole sky behind it, drawn as one full-screen shader.
 * It sits at the world origin; the ordinary meshes are rendered on top of it.
 */
export function BlackHole({ quality }: { quality: Quality }) {
  const geometry = useMemo(() => {
    const g = new BufferGeometry()
    g.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3))
    return g
  }, [])

  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader,
        fragmentShader,
        depthTest: false,
        depthWrite: false,
        uniforms: {
          uTime: { value: 0 },
          uCamWorld: { value: new Matrix4() },
          uProjInv: { value: new Matrix4() },
          uSteps: { value: 150 },
          uDiskGain: { value: 1 },
          uStarGain: { value: 1 },
          uDiskSpeed: { value: 0.045 },
        },
      }),
    [],
  )

  useEffect(() => {
    material.uniforms.uSteps.value = debug.steps ?? (quality === 'high' ? 150 : 96)
  }, [material, quality])

  useEffect(
    () => () => {
      geometry.dispose()
      material.dispose()
    },
    [geometry, material],
  )

  useFrame(({ camera }, delta) => {
    const u = material.uniforms
    u.uTime.value += Math.min(delta, 0.1) * (store.reducedMotion ? 0.25 : 1)
    u.uCamWorld.value.copy(camera.matrixWorld)
    u.uProjInv.value.copy(camera.projectionMatrixInverse)
    u.uDiskGain.value = 1.55 * sceneState.disk
    u.uStarGain.value = sceneState.stars
  })

  return <mesh geometry={geometry} material={material} frustumCulled={false} renderOrder={-1000} />
}

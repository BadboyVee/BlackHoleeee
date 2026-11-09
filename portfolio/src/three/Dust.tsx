import { useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { AdditiveBlending, BufferGeometry, Float32BufferAttribute, type PerspectiveCamera, ShaderMaterial, Vector2 } from 'three'
import { store } from '../lib/store'

const vertexShader = /* glsl */ `
  attribute float aSize;
  attribute float aSeed;
  uniform float uTime;
  uniform float uScale;
  varying float vAlpha;
  varying float vSeed;

  void main() {
    vec3 p = position;
    p.y += sin(uTime * 0.21 + aSeed * 31.0) * 0.45;
    p.x += cos(uTime * 0.17 + aSeed * 17.0) * 0.35;
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    float dist = -mv.z;
    gl_PointSize = max(aSize * uScale / dist, 1.0);
    // Fade specks that drift right past the lens, and those far away.
    vAlpha = smoothstep(0.8, 5.0, dist) * (1.0 - smoothstep(55.0, 100.0, dist));
    vSeed = aSeed;
  }
`

const fragmentShader = /* glsl */ `
  varying float vAlpha;
  varying float vSeed;

  void main() {
    float d = length(gl_PointCoord - 0.5);
    float a = smoothstep(0.5, 0.0, d);
    vec3 tint = mix(vec3(1.0, 0.62, 0.34), vec3(0.78, 0.86, 1.0), step(0.6, vSeed));
    gl_FragColor = vec4(tint * a * a * vAlpha * (0.5 + vSeed), 1.0);
  }
`

/** Fine dust drifting through the scene — pure depth cue for the parallax. */
export function Dust({ count = 900 }: { count?: number }) {
  const geometry = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    const seeds = new Float32Array(count)
    // Deterministic pseudo-random so the layout is the same on every visit.
    let s = 1337
    const rand = () => {
      s = (s * 16807) % 2147483647
      return s / 2147483647
    }
    for (let i = 0; i < count; i++) {
      positions[i * 3] = -45 + rand() * 130
      positions[i * 3 + 1] = -28 + rand() * 66
      positions[i * 3 + 2] = -70 + rand() * 125
      sizes[i] = 0.035 + Math.pow(rand(), 3) * 0.16
      seeds[i] = rand()
    }
    const g = new BufferGeometry()
    g.setAttribute('position', new Float32BufferAttribute(positions, 3))
    g.setAttribute('aSize', new Float32BufferAttribute(sizes, 1))
    g.setAttribute('aSeed', new Float32BufferAttribute(seeds, 1))
    return g
  }, [count])

  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader,
        fragmentShader,
        transparent: true,
        depthWrite: false,
        blending: AdditiveBlending,
        uniforms: { uTime: { value: 0 }, uScale: { value: 1000 } },
      }),
    [],
  )

  useEffect(
    () => () => {
      geometry.dispose()
      material.dispose()
    },
    [geometry, material],
  )

  const buffer = useMemo(() => new Vector2(), [])

  useFrame(({ camera, gl }, delta) => {
    material.uniforms.uTime.value += Math.min(delta, 0.1) * (store.reducedMotion ? 0 : 1)
    gl.getDrawingBufferSize(buffer)
    const fov = ((camera as PerspectiveCamera).fov * Math.PI) / 180
    material.uniforms.uScale.value = buffer.y / (2 * Math.tan(fov / 2))
  })

  return <points geometry={geometry} material={material} frustumCulled={false} />
}

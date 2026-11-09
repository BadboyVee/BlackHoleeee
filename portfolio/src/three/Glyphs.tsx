import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { type Group, MeshStandardMaterial } from 'three'
import { Font, type FontData } from 'three/examples/jsm/loaders/FontLoader.js'
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry.js'
import glyphData from './glyphs.json'
import { store } from '../lib/store'

// Code symbols as solid 3D models, extruded from JetBrains Mono outlines (see
// scripts/make-glyphs.mjs). They hang in the space the camera flies through
// during the hero and about sections, which is what sells the parallax.

interface Item {
  text: string
  position: [number, number, number]
  rotation: [number, number, number]
  scale: number
  /** Spin speed (rad/s) around x and y. */
  spin: [number, number]
}

const ITEMS: Item[] = [
  { text: '</>', position: [-12.5, 6.2, 9], rotation: [0.25, 0.5, -0.12], scale: 1.25, spin: [0.05, 0.16] },
  { text: '{}', position: [-9.5, -2.4, 13.5], rotation: [-0.3, 0.7, 0.2], scale: 0.8, spin: [0.09, -0.14] },
  { text: ';', position: [-3.4, 5.6, 15], rotation: [0.4, -0.3, 0.1], scale: 0.55, spin: [0.2, 0.1] },
  { text: '#', position: [4.5, -4.4, 12], rotation: [0.2, 0.2, 0.4], scale: 0.7, spin: [-0.07, 0.18] },
  { text: '()', position: [10, 9.5, 14], rotation: [-0.2, -0.6, 0.15], scale: 0.9, spin: [0.06, 0.12] },
  { text: '=>', position: [16, 3.5, 20], rotation: [0.3, -0.9, -0.2], scale: 1.0, spin: [0.04, -0.13] },
  { text: '*', position: [7.5, 13.5, 19], rotation: [0.5, 0.2, 0.3], scale: 0.6, spin: [0.18, 0.22] },
  { text: '[]', position: [22, 15, 8], rotation: [-0.4, -1.1, 0.1], scale: 1.1, spin: [0.05, 0.1] },
  { text: '+', position: [14, 19, 13], rotation: [0.1, 0.4, 0.6], scale: 0.5, spin: [-0.2, 0.15] },
  { text: '</>', position: [30, 11, 2], rotation: [0.2, -1.3, 0.2], scale: 0.9, spin: [0.06, -0.12] },
  { text: '{}', position: [26, 22, -6], rotation: [0.6, -1.0, -0.3], scale: 1.3, spin: [-0.05, 0.09] },
  { text: '_', position: [-6, 10.5, 18.5], rotation: [0.1, 0.3, -0.5], scale: 0.7, spin: [0.1, 0.2] },
]

export function Glyphs() {
  const font = useMemo(() => new Font(glyphData as unknown as FontData), [])

  const geometries = useMemo(() => {
    const cache = new Map<string, TextGeometry>()
    for (const { text } of ITEMS) {
      if (cache.has(text)) continue
      const g = new TextGeometry(text, {
        font,
        size: 1,
        depth: 0.34,
        curveSegments: 8,
        bevelEnabled: true,
        bevelThickness: 0.045,
        bevelSize: 0.03,
        bevelSegments: 3,
      })
      g.center()
      cache.set(text, g)
    }
    return cache
  }, [font])

  // Polished obsidian: almost black until it catches the light of the disk.
  const material = useMemo(
    () => new MeshStandardMaterial({ color: '#b9b0a2', metalness: 1, roughness: 0.22, envMapIntensity: 1.5 }),
    [],
  )

  useEffect(
    () => () => {
      geometries.forEach((g) => g.dispose())
      material.dispose()
    },
    [geometries, material],
  )

  const group = useRef<Group>(null)
  const boost = useRef(0)

  useFrame((state, delta) => {
    if (!group.current || store.reducedMotion) return
    const dt = Math.min(delta, 0.1)
    // Scrolling stirs them up; they settle again when the page rests.
    boost.current += (Math.min(Math.abs(store.velocity) * 0.06, 4) - boost.current) * (1 - Math.exp(-dt * 3))
    const t = state.clock.elapsedTime
    group.current.children.forEach((child, i) => {
      const item = ITEMS[i]
      const speed = 1 + boost.current
      child.rotation.x += item.spin[0] * dt * speed
      child.rotation.y += item.spin[1] * dt * speed
      child.position.y = item.position[1] + Math.sin(t * 0.4 + i * 1.7) * 0.35
    })
  })

  return (
    <group ref={group}>
      {ITEMS.map((item, i) => (
        <mesh
          key={i}
          geometry={geometries.get(item.text)}
          material={material}
          position={item.position}
          rotation={item.rotation}
          scale={item.scale}
        />
      ))}
    </group>
  )
}

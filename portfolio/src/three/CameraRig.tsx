import { useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { PerspectiveCamera } from 'three'
import { debug } from '../lib/debug'
import { createPose, measureRig, samplePose, type Pose } from '../lib/rig'
import { on, store } from '../lib/store'
import { sceneState } from './sceneState'

const FIELDS: (keyof Pose)[] = ['fx', 'fy', 'fz', 'r', 'elev', 'az', 'roll', 'fov', 'sx', 'sy', 'disk', 'stars']

/**
 * Flies the camera along the scroll path defined in lib/rig.ts and layers a
 * little pointer parallax and idle drift on top, so the scene never sits still.
 */
export function CameraRig() {
  const camera = useThree((s) => s.camera) as PerspectiveCamera
  const size = useThree((s) => s.size)

  const target = useRef(createPose())
  const current = useRef(createPose())
  const pointer = useRef({ x: 0, y: 0 })
  const snap = useRef(true)

  useEffect(() => {
    measureRig()
    const remeasure = () => measureRig()
    window.addEventListener('resize', remeasure)
    // Fonts, images and split text all nudge the layout after first paint.
    const observer = new ResizeObserver(remeasure)
    observer.observe(document.body)
    // Coming back from behind an opaque section: jump, don't swoop.
    const off = on('canvasHidden', () => {
      if (!store.canvasHidden) snap.current = true
    })
    return () => {
      window.removeEventListener('resize', remeasure)
      observer.disconnect()
      off()
    }
  }, [])

  useFrame((state, delta) => {
    const dt = Math.min(delta, 0.1)
    const cur = current.current
    const tgt = samplePose(store.scroll, target.current)

    const k = snap.current || debug.snap ? 1 : 1 - Math.exp(-dt * 5)
    snap.current = false
    for (const f of FIELDS) cur[f] += (tgt[f] - cur[f]) * k

    const still = store.reducedMotion
    const pk = 1 - Math.exp(-dt * 2.2)
    pointer.current.x += ((still ? 0 : store.pointer.x) - pointer.current.x) * pk
    pointer.current.y += ((still ? 0 : store.pointer.y) - pointer.current.y) * pk

    const t = still ? 0 : state.clock.elapsedTime
    const az = cur.az + pointer.current.x * 0.075 + Math.sin(t * 0.13) * 0.022
    const elev = Math.min(1.53, Math.max(-1.53, cur.elev - pointer.current.y * 0.05 + Math.sin(t * 0.09) * 0.012))

    const ce = Math.cos(elev)
    camera.position.set(cur.fx + cur.r * ce * Math.sin(az), cur.fy + cur.r * Math.sin(elev), cur.fz + cur.r * ce * Math.cos(az))
    camera.up.set(0, 1, 0)
    camera.lookAt(cur.fx, cur.fy, cur.fz)
    camera.rotateZ(cur.roll)
    camera.fov = cur.fov
    // Shift the picture inside the frame (rather than turning the camera) so
    // the hole can sit off-centre without being stretched by perspective.
    camera.setViewOffset(size.width, size.height, -cur.sx * size.width * 0.5, cur.sy * size.height * 0.5, size.width, size.height)
    camera.updateMatrixWorld()

    sceneState.disk = cur.disk
    sceneState.stars = cur.stars
  }, -2)

  return null
}

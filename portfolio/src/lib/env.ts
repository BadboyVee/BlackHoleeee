const query = (q: string) => typeof window !== 'undefined' && window.matchMedia(q).matches

export const prefersReducedMotion = () => query('(prefers-reduced-motion: reduce)')
export const isCoarsePointer = () => query('(pointer: coarse)')
export const isSmallScreen = () => query('(max-width: 767px)')

/**
 * A rough GPU tier from the renderer string. Software rasterisers (headless
 * browsers, some VMs) and phones get the light settings.
 */
export function gpuTier(): 'low' | 'mid' | 'high' {
  if (typeof document === 'undefined') return 'mid'
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl2') ?? canvas.getContext('webgl')
    if (!gl) return 'low'
    const info = gl.getExtension('WEBGL_debug_renderer_info')
    const renderer = String(info ? gl.getParameter(info.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER))
    gl.getExtension('WEBGL_lose_context')?.loseContext()
    if (/swiftshader|llvmpipe|software|basic render/i.test(renderer)) return 'low'
    if (isSmallScreen() || isCoarsePointer()) return 'mid'
    return 'high'
  } catch {
    return 'mid'
  }
}

// Development-only knobs, read from the URL: /?dpr=0.5&steps=90&snap&nointro
// Handy on slow machines and for automated screenshots. In a production build
// `import.meta.env.DEV` is false, so all of this is stripped out.

const params = import.meta.env.DEV ? new URLSearchParams(window.location.search) : null
const num = (key: string) => (params?.has(key) ? Number(params.get(key)) : null)

export const debug = {
  /** Force the canvas pixel ratio (disables adaptive resolution). */
  dpr: num('dpr'),
  /** Force the ray-march step count. */
  steps: num('steps'),
  /** Camera jumps straight to its scroll pose instead of easing toward it. */
  snap: params?.has('snap') ?? false,
  /** Skip the preloader. */
  noIntro: params?.has('nointro') ?? false,
}

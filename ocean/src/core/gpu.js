// Can this browser run the game?
//
// It needs real WebGPU. When WebGPU can't start, three.js quietly drops to its
// WebGL2 backend, which can't run the compute passes the ocean, sky and
// terrain are built with, and the load then dies with a cryptic shader error.
// So ask for an adapter and a device first, and if either is refused say so
// plainly, with what to try.

const TRY = 'To try anyway in Chrome: open chrome://flags, search for "WebGPU", set "Unsafe WebGPU Support" to Enabled, tap Relaunch, then open the game again.\n\nOr play it on a computer in Chrome or Edge.';

export class NoWebGPU extends Error {}

export const noWebGPU = (why) => new NoWebGPU(`${why}\n\n${TRY}`);

/** resolves when WebGPU can start here, else throws a NoWebGPU saying why */
export async function checkWebGPU() {
  if (!navigator.gpu) throw noWebGPU("This browser doesn't offer WebGPU, which the game needs to draw the ocean. Use an up-to-date Chrome or Edge (on a phone: Chrome on Android 12 or newer).");
  let adapter = null;
  try {
    // same request three.js makes: 'compatibility' also accepts the lighter WebGPU some phones have
    adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance', featureLevel: 'compatibility' });
  } catch (e) { /* reported as no adapter */ }
  if (!adapter) throw noWebGPU("This browser has WebGPU, but it's switched off for this device's graphics chip, so the game can't start.");
  try {
    (await adapter.requestDevice()).destroy();
  } catch (e) {
    throw noWebGPU(`WebGPU couldn't start on this device (${e.message || e}).`);
  }
}

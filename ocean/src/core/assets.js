// Where the game's files live.
//
// Normally they sit next to index.html (served over http). The single-file
// build (tools/build-single.mjs) embeds every file as a data URL in
// globalThis.__SALTWIND_ASSETS__, keyed by its path under ocean/, so the
// page also runs when opened straight from disk.

import * as THREE from 'three/webgpu';

const EMBEDDED = globalThis.__SALTWIND_ASSETS__ || null;
const ROOT = new URL('../../', import.meta.url);

/** URL of a file under ocean/, e.g. assetURL('assets/terrain/island.bin.gz') */
export function assetURL(path) {
  if (EMBEDDED) {
    const url = EMBEDDED[path];
    if (!url) throw new Error(`single-file build is missing ${path}`);
    return url;
  }
  return new URL(path, ROOT).href;
}

/** folder three's Draco decoder is loaded from (the loader appends file names) */
export function dracoDecoderPath() {
  return EMBEDDED ? 'embedded:draco/' : import.meta.resolve('three/addons/libs/draco/gltf/');
}

if (EMBEDDED) {
  // loaders ask for folder + name (the Draco decoder): serve the embedded copy
  THREE.DefaultLoadingManager.setURLModifier((url) => (url.startsWith('embedded:') ? EMBEDDED[url.slice(9)] ?? url : url));
}

// Binary format of the baked island (assets/terrain/island.bin.gz), shared by
// the bake tool and the game.
//
//   'ISL2'  u32 N  f32 hMin  f32 hStep
//   u16[N*N]   heights, q = round((h - hMin) / hStep), stored as the
//              difference to the previous texel of the row (compresses well)
//   u8[N*N*4]  aux texels, ready to upload as an RGBA8 texture:
//              r  drainage: log2(1 + catchment / texel area) * 12
//              g  erosion: metres laid down (+) or removed (-), * 6 + 128
//              b  sky visibility * 255
//              a  forest cover * 255

const MAGIC = 0x324c5349; // 'ISL2'
export const H_MIN = -80, H_STEP = 1 / 256;

export function encodeIsland({ height, flow, change, sky, forest }, N, cellArea) {
  const head = 16;
  const buf = new ArrayBuffer(head + N * N * 2 + N * N * 4);
  const dv = new DataView(buf);
  dv.setUint32(0, MAGIC, true);
  dv.setUint32(4, N, true);
  dv.setFloat32(8, H_MIN, true);
  dv.setFloat32(12, H_STEP, true);
  const q = new Uint16Array(buf, head, N * N);
  for (let j = 0; j < N; j++) {
    let prev = 0;
    for (let i = 0; i < N; i++) {
      const k = j * N + i;
      const v = Math.max(0, Math.min(65535, Math.round((height[k] - H_MIN) / H_STEP)));
      q[k] = (v - prev) & 0xffff;
      prev = v;
    }
  }
  const aux = new Uint8Array(buf, head + N * N * 2, N * N * 4);
  const cl = (v) => Math.max(0, Math.min(255, Math.round(v)));
  for (let k = 0; k < N * N; k++) {
    aux[k * 4] = cl(Math.log2(1 + flow[k] / cellArea) * 12);
    aux[k * 4 + 1] = cl(change[k] * 6 + 128);
    aux[k * 4 + 2] = cl(sky[k] * 255);
    aux[k * 4 + 3] = cl(forest[k] * 255);
  }
  return new Uint8Array(buf);
}

export function decodeIsland(arrayBuffer) {
  const dv = new DataView(arrayBuffer);
  if (dv.getUint32(0, true) !== MAGIC) throw new Error('island data: bad magic');
  const N = dv.getUint32(4, true);
  const hMin = dv.getFloat32(8, true), hStep = dv.getFloat32(12, true);
  const head = 16;
  const q = new Uint16Array(arrayBuffer.slice(head, head + N * N * 2));
  const height = new Float32Array(N * N);
  for (let j = 0; j < N; j++) {
    let v = 0;
    for (let i = 0; i < N; i++) {
      const k = j * N + i;
      v = (v + q[k]) & 0xffff;
      height[k] = hMin + v * hStep;
    }
  }
  const aux = new Uint8Array(arrayBuffer.slice(head + N * N * 2, head + N * N * 6));
  return { N, height, aux };
}

/** fetch + gunzip (servers may or may not have undone the gzip already) */
export async function fetchIsland(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`island data: HTTP ${res.status} for ${url}`);
  let buf = await res.arrayBuffer();
  const b = new Uint8Array(buf, 0, 2);
  if (b[0] === 0x1f && b[1] === 0x8b) {
    const stream = new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'));
    buf = await new Response(stream).arrayBuffer();
  }
  return decodeIsland(buf);
}

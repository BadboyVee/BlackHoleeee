import * as THREE from 'three/webgpu';
import { positionWorld } from 'three/tsl';
import { CSMShadowNode } from 'three/addons/csm/CSMShadowNode.js';
import { Sky } from './sky/sky.js';
import { Ocean } from './ocean/ocean.js';
import { WaterMaterial } from './ocean/waterMaterial.js';
import { Shore } from './ocean/shore.js';
import { bakeFoamTexture } from './ocean/foamTexture.js';
import { bakeTerrainTextures } from './world/terrainTextures.js';
import { Island } from './world/island.js';
import { Terrain } from './world/terrain.js';
import { Pipeline } from './render/pipeline.js';
import { env } from './env.js';

const $ = (id) => document.getElementById(id);
const status = (t, p) => { $('loader-status').textContent = t; if (p !== undefined) $('loader-fill').style.width = `${Math.round(p * 100)}%`; };
const query = new URLSearchParams(location.search);

const debug = window.__ocean = { ready: false, frame: 0 };
let frameWaiters = [];
debug.waitFrames = (n) => new Promise((res) => frameWaiters.push({ left: n, res }));

// three r186 always passes an identity `swizzle: 'rgba'` when creating texture
// views; browsers that shipped the older dictionary form reject the string.
// Identity swizzle is a no-op, so dropping it keeps those browsers working.
if (typeof GPUTexture !== 'undefined') {
  const createView = GPUTexture.prototype.createView;
  GPUTexture.prototype.createView = function (desc) {
    if (desc && desc.swizzle === 'rgba') {
      const d = {};
      for (const k in desc) if (k !== 'swizzle' && desc[k] !== undefined) d[k] = desc[k];
      return createView.call(this, d);
    }
    return createView.call(this, desc);
  };
}

if (query.has('trace')) THREE.Node.captureStackTrace = true;
const nextFrame = () => new Promise((r) => requestAnimationFrame(() => r()));

async function start() {
  if (!navigator.gpu) throw new Error('WebGPU is not available in this browser. Try a recent Chrome, Edge or Safari.');
  status('Initialising WebGPU…', 0.04);
  const renderer = new THREE.WebGPURenderer({ antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, query.has('test') ? 1 : 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.55;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  $('app').appendChild(renderer.domElement);
  await renderer.init();

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.08, 30000);
  camera.position.set(40, 2.4, 20);
  camera.lookAt(80, 1.5, 120);

  // ---------------------------------------------------------------- sky
  status('Building sky…', 0.1);
  const sky = new Sky(renderer, { test: query.has('test'), panoWidth: +(query.get('pano') || 4096) });
  await sky.init();
  scene.backgroundNode = sky.backgroundNode();
  scene.environment = sky.envTarget.texture;

  // ---------------------------------------------------------------- sun
  const sun = new THREE.DirectionalLight(0xffffff, 1);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 1200;
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = 0.04;
  const csm = new CSMShadowNode(sun, { cascades: 3, maxFar: 420, mode: 'practical', lightMargin: 260 });
  csm.fade = true;
  sun.shadow.shadowNode = csm;
  scene.add(sun, sun.target);
  const hemi = new THREE.HemisphereLight(0x8fb4d9, 0x6b5a45, 0.6);
  scene.add(hemi);

  const setSun = (el, az) => {
    sky.setSun(el, az);
    const d = sky.sunDirection.value;
    env.sunDir.value.copy(d);
    env.sunDiskDir.value.copy(sky.sunDiskDirection.value);
    const E = sky.lightIlluminance.value * sky.lightFade;
    sun.color.copy(sky.lightColor.value);
    sun.intensity = E;
    sun.position.copy(d).multiplyScalar(300);
    sun.target.position.set(0, 0, 0);
    env.sunColor.value.copy(sky.lightColor.value).multiplyScalar(E);
    env.skyIrradiance.value.copy(sky.skyIrradiance);
    env.nightFactor.value = sky.nightFactor.value;
    // ambient comes from the sky environment map (IBL); the hemisphere light
    // only adds a little extra sand bounce from below
    hemi.color.setRGB(0, 0, 0);
    hemi.groundColor.setRGB(0.45, 0.38, 0.28).multiplyScalar(E * Math.max(d.y, 0) * 0.012);
    hemi.intensity = 1;
    sky.envAge = 1e9; // refresh the environment on the next frame
  };
  setSun(+(query.get('sunEl') || 16), +(query.get('sunAz') || 205));

  // ---------------------------------------------------------------- world
  status('Shaping the island…', 0.22);
  await nextFrame();
  const island = new Island(7);
  const terrain = new Terrain(island);
  scene.add(terrain.mesh);

  status('Building wave spectrum…', 0.35);
  const oceanParams = {
    lengthScales: [420, 57, 7.7],
    choppiness: 0.95, foamThreshold: 0.42, foamGain: 1.4, foamDecay: 3.5,
    depth: 80, seed: 3,
    local: { scale: 1, windSpeed: 7, windDirection: 20, fetch: 60, spreadBlend: 0.85, swell: 0.25, peakEnhancement: 3.3, shortWavesFade: 0.01 },
    swellSpectrum: { scale: 0.7, windSpeed: 2.5, windDirection: 10, fetch: 500, spreadBlend: 1, swell: 1, peakEnhancement: 3.3, shortWavesFade: 0.01 },
  };
  const ocean = new Ocean(renderer, oceanParams);
  status('Tracing wave rays into the bay…', 0.42);
  await nextFrame();
  const shore = new Shore(island, terrain);
  status('Baking materials…', 0.48);
  await nextFrame();
  const foamTexture = bakeFoamTexture(renderer, query.has('test') ? 512 : 1024);
  const terrainTextures = bakeTerrainTextures(renderer, query.has('test') ? 512 : 1024);
  terrain.setupShading({ textures: terrainTextures, shore, foamTexture, time: env.time });
  const dbgLayer = query.get('layer');
  if (dbgLayer !== null) {
    const { texture: tex, screenUV, vec4: v4, int: i32 } = await import('three/tsl');
    const which = query.get('arr') === 'n' ? terrainTextures.normal : terrainTextures.albedo;
    scene.backgroundNode = v4(tex(which, screenUV.mul(2)).depth(i32(+dbgLayer)).level(+(query.get('lod') || 0)).rgb, 1);
    renderer.toneMapping = THREE.NoToneMapping;
  }
  const water = new WaterMaterial({ ocean, terrain, sky, shore, foamTexture });
  const waterMesh = new THREE.Mesh(ocean.geometry, water);
  waterMesh.frustumCulled = false;
  waterMesh.renderOrder = 10;
  waterMesh.receiveShadow = true;
  waterMesh.name = 'ocean';
  scene.add(waterMesh);

  // ---------------------------------------------------------------- pipeline
  const pipeline = new Pipeline({ renderer, scene, camera, sun });
  pipeline.sunShadowTerms.push(() => sky.cloudShadow(positionWorld));
  pipeline.build();

  // ---------------------------------------------------------------- warm up
  status('Compiling shaders…', 0.6);
  ocean.update(0.016, 0, camera);
  terrain.update(camera);
  sky.update(0.016, camera, 0);
  await renderer.compileAsync(scene, camera);
  status('Warming up…', 0.9);
  for (let i = 0; i < 10; i++) { sky.update(0.016, camera, 0); await nextFrame(); }
  sky.updateEnvironment(true);
  $('loader').classList.add('done');

  const timer = new THREE.Timer();
  let time = +(query.get('t') || 0);
  let frozen = query.has('freeze');
  debug.setTime = (t, freeze = true) => { time = t; frozen = freeze; };
  let fpsAcc = 0, fpsFrames = 0;
  renderer.setAnimationLoop(() => {
    timer.update();
    const dt = frozen ? 0 : Math.min(timer.getDelta(), 0.1);
    time += dt;
    env.time.value = time;
    env.dt.value = dt;
    ocean.update(dt, time, camera);
    terrain.update(camera);
    sky.update(dt, camera, time);
    sky.updateEnvironment();
    pipeline.render();
    fpsAcc += dt; fpsFrames++;
    if (fpsAcc > 0.5) {
      $('fps-value').textContent = Math.round(fpsFrames / fpsAcc);
      $('fps-ms').textContent = `${(fpsAcc / fpsFrames * 1000).toFixed(1)} ms`;
      fpsAcc = 0; fpsFrames = 0;
    }
    debug.frame++;
    debug.ready = debug.frame > 2;
    frameWaiters = frameWaiters.filter((w) => (--w.left <= 0 ? (w.res(), false) : true));
  });

  // ---------------------------------------------------------------- debug hooks
  Object.assign(debug, { renderer, scene, camera, sky, ocean, terrain, island, water, pipeline, sun, csm, env, shore });
  debug.stats = () => ({ frame: debug.frame, oceanPatches: ocean.selector.count, terrainPatches: terrain.selector.count, hs: +ocean.fft.stats.hs.toFixed(2) });
  // yaw: 0 = north (-z), 90 = east (+x)
  debug.look = (yaw, pitch, x, y, z) => {
    if (x !== undefined) camera.position.set(x, y, z);
    const yr = THREE.MathUtils.degToRad(yaw), pr = THREE.MathUtils.degToRad(pitch);
    const d = new THREE.Vector3(Math.sin(yr) * Math.cos(pr), Math.sin(pr), -Math.cos(yr) * Math.cos(pr));
    camera.lookAt(camera.position.clone().add(d));
  };
  debug.setSun = setSun;
}

start().catch((e) => {
  console.error(e);
  $('loader-error').hidden = false;
  $('loader-error').textContent = String(e && e.message || e);
});

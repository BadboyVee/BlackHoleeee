import * as THREE from 'three/webgpu';
import { positionWorld, texture, float, exp, length, max, select } from 'three/tsl';
import { CSMShadowNode } from 'three/addons/csm/CSMShadowNode.js';
import { Sky } from './sky/sky.js';
import { Ocean } from './ocean/ocean.js';
import { WaterMaterial } from './ocean/waterMaterial.js';
import { Shore } from './ocean/shore.js';
import { bakeFoamTexture } from './ocean/foamTexture.js';
import { bakeTerrainTextures, loadGroundImages } from './world/terrainTextures.js';
import { Island, VILLAGE, REEF } from './world/island.js';
import { Terrain } from './world/terrain.js';
import { CollisionWorld } from './world/collision.js';
import { Village } from './world/village.js';
import { Vegetation } from './world/vegetation.js';
import { Boulders } from './world/rocks.js';
import { Grass } from './world/grass.js';
import { Fish } from './life/fish.js';
import { Whale } from './life/whale.js';
import { Birds } from './life/birds.js';
import { Crabs, Motes } from './life/critters.js';
import { Reef } from './life/reef.js';
import { Audio } from './audio/audio.js';
import { Pipeline } from './render/pipeline.js';
import { Composite } from './render/composite.js';
import { LensDroplets } from './render/droplets.js';
import { Post } from './render/post.js';
import { WaterProbe } from './ocean/probe.js';
import { Wake } from './ocean/wake.js';
import { Spray } from './fx/spray.js';
import { Surf } from './ocean/surf.js';
import { Boat } from './boat/boat.js';
import { Caustics } from './ocean/caustics.js';
import { underwaterSun, underwaterAmbient } from './ocean/underwaterLight.js';
import { Input } from './player/input.js';
import { TouchControls } from './player/touch.js';
import { Player } from './player/player.js';
import { Flashlight } from './player/flashlight.js';
import { buildSettings } from './ui/settings.js';
import { AutoExposure } from './render/exposure.js';
import { FramePacer, Governor } from './render/framerate.js';
import { env } from './env.js';
import { checkWebGPU, noWebGPU, NoWebGPU } from './core/gpu.js';

const $ = (id) => document.getElementById(id);
const status = (t, p) => {
  $('loader-status').textContent = t;
  if (p !== undefined) $('loader-fill').style.width = `${Math.round(p * 100)}%`;
  if (new URLSearchParams(location.search).has('test')) console.log(`[stage] ${t} ${performance.now().toFixed(0)}ms`);
};
const query = new URLSearchParams(location.search);
const TEST = query.has('test');
// phones and small tablets start lighter (the settings panel can raise it again; ?phone forces it)
const PHONE = query.has('phone') || (!TEST && matchMedia('(pointer: coarse)').matches && Math.min(screen.width, screen.height) < 820);
// ?off=grass,fish,... hides systems and skips their updates (debug bisection)
const OFF = new Set((query.get('off') || '').split(',').filter(Boolean));
const on = (k) => !OFF.has(k);

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

// time of day -> sun position (a simple arc: rises in the east, noon to the south)
const MAX_SUN_EL = 62;
function sunFromHour(h) {
  const day = (h - 6) / 12;                     // 0 at sunrise, 1 at sunset
  const el = MAX_SUN_EL * Math.sin(Math.PI * day);
  const az = (90 + day * 180 + 360 * 4) % 360;
  return { el: Math.max(-14, el), az };
}
function hourFromSun(el, az) {
  const day = ((az - 90 + 360) % 360) / 180;
  return 6 + Math.min(day, 1.15) * 12;
}

async function start() {
  status('Initialising WebGPU…', 0.04);
  await checkWebGPU();
  const renderer = new THREE.WebGPURenderer({ antialias: false, powerPreference: 'high-performance' });
  const app = { renderer, resolutionScale: 1, resolutionMax: 1, daySpeed: 0, exposureBias: 0.55 };
  const pixelRatio = () => (TEST ? 1 : Math.min(window.devicePixelRatio || 1, 1.25) * app.resolutionScale);
  renderer.setPixelRatio(pixelRatio());
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.55;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  $('app').appendChild(renderer.domElement);
  await renderer.init();
  // three.js drops to WebGL2 if WebGPU fails after all; the game can't run there
  if (!renderer.backend.isWebGPUBackend) throw noWebGPU("WebGPU couldn't start on this device, so the game can't run.");
  renderer.onDeviceLost = (info) => {
    console.error(`WebGPU device lost at frame ${debug.frame}: ${info.message || info.reason}`);
    debug.deviceLost = info.message || String(info.reason);
  };

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.08, 30000);
  camera.position.set(40, 2.4, 20);
  camera.lookAt(80, 1.5, 120);

  // ---------------------------------------------------------------- sky
  status('Building sky…', 0.1);
  const sky = new Sky(renderer, { test: TEST, panoWidth: +(query.get('pano') || (TEST ? 1024 : PHONE ? 2048 : 4096)) });
  await sky.init();
  scene.backgroundNode = sky.backgroundNode();
  scene.environment = sky.envTarget.texture;

  // ---------------------------------------------------------------- sun
  const sun = new THREE.DirectionalLight(0xffffff, 1);
  sun.castShadow = true;
  sun.shadow.mapSize.setScalar(PHONE ? 1024 : 2048);
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 1200;
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = 0.04;
  // (a phone's small screen gets by with two cascades: a third fewer shadow casters drawn)
  const csm = new CSMShadowNode(sun, { cascades: PHONE ? 2 : 3, maxFar: 420, mode: 'practical', lightMargin: 260 });
  csm.fade = true;
  sun.shadow.shadowNode = csm;
  scene.add(sun, sun.target);
  const hemi = new THREE.HemisphereLight(0x8fb4d9, 0x6b5a45, 0.6);
  scene.add(hemi);

  const setSun = (el, az) => {
    app.sunEl = el; app.sunAz = az;
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
  app.setSun = setSun;
  setSun(+(query.get('sunEl') || 16), +(query.get('sunAz') || 205));
  app.hour = hourFromSun(app.sunEl, app.sunAz);

  // ---------------------------------------------------------------- world
  status('Shaping the island…', 0.22);
  await nextFrame();
  const island = await Island.load();
  const terrain = new Terrain(island);
  scene.add(terrain.mesh);
  const collision = new CollisionWorld(island);

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
  const foamTexture = bakeFoamTexture(renderer, TEST ? 512 : 1024);
  const terrainTextures = bakeTerrainTextures(renderer, TEST ? 512 : 1024);
  await loadGroundImages(renderer, terrainTextures, TEST ? 512 : 1024);
  terrain.setupShading({ textures: terrainTextures, shore, foamTexture, time: env.time });
  const dbgLayer = query.get('layer');
  if (dbgLayer !== null) {
    const { texture: tex, screenUV, vec4: v4, int: i32 } = await import('three/tsl');
    const which = query.get('arr') === 'n' ? terrainTextures.normal : terrainTextures.albedo;
    scene.backgroundNode = v4(tex(which, screenUV.mul(2)).depth(i32(+dbgLayer)).level(+(query.get('lod') || 0)).rgb, 1);
    renderer.toneMapping = THREE.NoToneMapping;
  }
  const wake = new Wake(renderer, { terrain, size: TEST ? 256 : 512 });
  ocean.wake = wake;
  const spray = new Spray(renderer, { ocean, wake });
  scene.add(spray.mesh);
  const surf = new Surf(renderer, { ocean, shore, terrain, island, spray, time: env.time, slices: TEST ? 32 : 4 });
  ocean.surf = surf;
  const water = new WaterMaterial({ ocean, terrain, sky, shore, foamTexture });
  water.debugShore = query.has('waterDebug') ? (+query.get('waterDebug') || 1) : 0;
  const waterMesh = new THREE.Mesh(ocean.geometry, water);
  waterMesh.frustumCulled = false;
  waterMesh.renderOrder = 10;
  waterMesh.receiveShadow = true;
  waterMesh.name = 'ocean';
  scene.add(waterMesh);

  const probe = new WaterProbe(renderer, ocean, shore, env.time);
  probe.noReadback = query.has('noreadback');
  const caustics = new Caustics(renderer, ocean);

  // ---------------------------------------------------------------- player
  const input = new Input(renderer.domElement, { ignore: (e) => !!e.target.closest?.('#panel') });
  const touch = new TouchControls(input, renderer.domElement);
  const player = new Player({ camera, input, collision, probe, queryIndex: probe.allocQueries(1) });
  const flashlight = new Flashlight(scene);
  // the torch casts no shadow map; a constant shadow node makes three.js run
  // the shadow hook so the pipeline can attenuate its light through water
  flashlight.light.castShadow = true;
  flashlight.light.shadow.shadowNode = float(1);
  const droplets = new LensDroplets(renderer);
  status('Building the village…', 0.52);
  await nextFrame();
  const village = new Village({ scene, island, collision, terrain });
  status('Growing trees…', 0.55);
  await nextFrame();
  const vegetation = await Vegetation.create({ scene, island, collision, terrain });
  const vegBase = +query.get('veg') || 1;     // ?veg= scales every quality tier's vegetation detail
  vegetation.setDetail(vegBase);
  const boulders = await Boulders.create({ scene, island, collision, textures: terrainTextures });
  if (TEST) console.log('[veg] counts', JSON.stringify(vegetation.counts), 'boulders', boulders.counts);
  vegetation.update(camera);
  boulders.update(camera);
  const grass = new Grass(renderer, { terrain, island, grid: TEST ? 56 : PHONE ? 80 : 112 });
  scene.add(grass.mesh);
  const whale = new Whale({ scene, spray, ocean, island });
  const fish = new Fish(renderer, { scene, terrain, reef: REEF, escortStart: whale.pos });
  const reefLife = new Reef({ scene, island, reef: REEF, collision });
  const birds = new Birds({ scene });
  const crabs = new Crabs({ scene, island });
  const motes = new Motes({ scene });
  // the boat, moored alongside the end of the pier, bow to seaward
  const boat = new Boat({
    scene, probe, collision, wake, spray,
    mooring: { x: VILLAGE.pierX + 3.2, z: VILLAGE.pierZ1 - 9, heading: Math.PI },
  });
  app.boat = boat;
  {
    const tsl = await import('three/tsl');
    const { halfBeamNode, sheerNode, BOAT } = await import('./boat/boatModel.js');
    boat.matrixWorldInverse = new THREE.Matrix4();
    water.addHullMask({ matrixWorldInverse: boat.matrixWorldInverse, length: BOAT.L, halfBeam: (s) => halfBeamNode(tsl, s), sheer: (s) => sheerNode(tsl, s).add(0.05) });
  }

  // ---------------------------------------------------------------- pipeline
  const pipeline = new Pipeline({ renderer, scene, camera, sun });
  pipeline.sunShadowTerms.push(() => sky.cloudShadow(positionWorld));
  pipeline.sunShadowTerms.push((builder) => (builder.material.isWaterMaterial || builder.material.userData.noUnderwater ? null : underwaterSun(ocean, caustics)));
  pipeline.aoTerms.push((builder) => (builder.material.userData.noUnderwater ? null : underwaterAmbient(ocean)));
  pipeline.lightShadowTerms.push({
    light: flashlight.light,
    fn: (builder) => {
      if (builder.material.isWaterMaterial) return null;
      // torch light travels through water: the whole way when the torch is
      // under water, only the submerged part when it shines in from above
      const c = env.waterAbsorption.add(env.waterScattering);
      const d = length(positionWorld.sub(env.flashlightPos));
      const submergedPath = select(env.cameraUnderwater.greaterThan(0.5), d, max(positionWorld.y.negate(), 0).mul(1.3));
      return exp(c.negate().mul(submergedPath));
    },
  });
  const composite = new Composite({ camera, probe, sky, renderer });
  pipeline.composites.push(composite.node());
  pipeline.ctxExtra = { dropletTexture: texture(droplets.target.texture) };
  const post = app.post = new Post({ camera, sky });
  pipeline.post.push(post.hdrNode());
  pipeline.post.push(droplets.node());
  pipeline.finals = [post.finalNode()];
  pipeline.build();
  const autoExposure = app.autoExposure = new AutoExposure(renderer, pipeline.taaPass.getTextureNode().value);
  // reflections must ignore what lies behind the water surface
  water.preDepth = pipeline.preDepth;

  Object.assign(app, { scene, camera, sky, ocean, water, shore, terrain, island, collision, probe, caustics, pipeline, composite, player, flashlight, droplets, input, sun, csm, wake, spray, surf, village, vegetation, boulders, grass, fish, whale, reefLife, birds, crabs, motes });
  const hide = { grass: [grass.mesh], fish: fish.groups.map((g) => g.mesh), whale: [whale.mesh], veg: [vegetation.group, boulders.group], village: [village.group], boat: [boat.group], spray: [spray.mesh], reef: [reefLife.group], birds: [birds.mesh, birds.beaks], crabs: [crabs.mesh], motes: [motes.mesh] };
  for (const [k, list] of Object.entries(hide)) if (!on(k)) for (const o of list) o.visible = false;

  // ---------------------------------------------------------------- places
  const places = {
    beach: () => player.spawn(72, -3, 140, -4),
    pier: () => player.spawn(VILLAGE.pierX, VILLAGE.pierZ1 - 6, 200, -2),
    // over the deeper, western side of the reef (the east is only 1.5 m deep)
    reef: () => { player.setView(REEF.x - 60, 0.3, REEF.z - 15, 110, -14); player.setMode('swim'); },
    boat: () => (app.boat ? app.boat.boardFromMenu(player) : places.pier()),
  };
  app.teleport = (k) => { places[k]?.(); };
  if (query.get('spawn') === 'fly') player.setView(40, 2.4, 20, 20, -2);
  else places.beach();

  // ---------------------------------------------------------------- audio
  const audio = app.audio = new Audio();
  player.on('step', (e) => {
    let surface = 'grass';
    if (e.wade > 0.12) surface = 'water';
    else if (e.surface && e.surface.tag === 'wood') surface = 'wood';
    else if (island.heightAt(e.x, e.z) < 4.2 && island.sdfAt(e.x, e.z) > -70) surface = 'sand';
    audio.footstep(surface, e.speed);
  });
  player.on('mode', (m, prev) => {
    if (m === 'swim' && (prev === 'walk' || prev === 'fly') && player.vel.y < -2.5) audio.splash(camera.position.clone(), Math.min(2, -player.vel.y / 4));
  });

  // ---------------------------------------------------------------- frame rate
  // Quality tiers the governor (render/framerate.js) steps between to hold the
  // chosen frame rate; 'high' is the full look. The lower tiers skip ambient
  // occlusion, contact shadows, water reflections and camera effects, thin out
  // grass and vegetation, and redraw the far shadow cascades less often (most
  // of a frame's draw calls are shadow casters).
  const full = { ao: pipeline.aoIntensity.value, contact: pipeline.contactStrength.value, mblur: post.motionBlur.value, godRays: post.godRays.value, flare: post.flare.value };
  const TIERS = {
    high: { ao: true, contact: true, ssr: true, mblur: true, rays: true, grass: true, veg: 1, smallShadows: true, cascades: [1, 1, 1] },
    medium: { ao: false, contact: true, ssr: true, mblur: false, rays: true, grass: true, veg: 0.75, smallShadows: false, cascades: [1, 1, 2] },
    low: { ao: false, contact: false, ssr: false, mblur: false, rays: false, grass: false, veg: 0.5, smallShadows: false, cascades: [1, 2, 3] },
  };
  let tier = TIERS.high;
  let panel = null;
  const applyQuality = (name, scale) => {
    const t = tier = TIERS[name];
    pipeline.settings.ao = t.ao;
    pipeline.aoIntensity.value = t.ao ? full.ao : 0;
    pipeline.settings.contactShadows = t.contact;
    pipeline.contactStrength.value = t.contact ? full.contact : 0;
    water.ssrEnabled.value = t.ssr ? 1 : 0;
    post.motionBlur.value = t.mblur ? full.mblur : 0;
    post.godRays.value = t.rays ? full.godRays : 0;
    post.flare.value = t.rays ? full.flare : 0;
    if (on('grass')) grass.mesh.visible = t.grass;
    vegetation.setDetail(vegBase * t.veg);
    vegetation.setSmallShadows(t.smallShadows);
    const s = Math.round(app.resolutionMax * scale * 100) / 100;
    if (s !== app.resolutionScale) { app.resolutionScale = s; app.onResize?.(); }
    if (panel) {
      for (const [id, v] of [['ao', pipeline.aoIntensity.value], ['contact', pipeline.contactStrength.value], ['ssr', t.ssr], ['mblur', post.motionBlur.value],
        ['godrays', post.godRays.value], ['flare', post.flare.value], ['vegDetail', vegetation.lodScale]]) panel.get(id)?.set(v);
    }
  };
  const pacer = new FramePacer();
  const governor = new Governor(renderer.backend.device, applyQuality);
  governor.enabled = !TEST && !query.has('nofit');
  // the choice sticks between visits (where the browser keeps storage)
  const prefs = (() => { try { return JSON.parse(localStorage.getItem('saltwind.frame')) || {}; } catch (e) { return {}; } })();
  const savePrefs = () => { try { localStorage.setItem('saltwind.frame', JSON.stringify({ fps: pacer.fps, quality: governor.mode })); } catch (e) { /* not kept */ } };
  pacer.fps = TEST ? 0 : prefs.fps ?? (PHONE ? 30 : 0);
  governor.mode = ['auto', 'low', 'medium', 'high'].includes(prefs.quality) ? prefs.quality : 'auto';
  governor.setTarget(pacer.fps || 60);
  app.frame = {
    get fps() { return pacer.fps; },
    get quality() { return governor.mode; },
    setFps(v) { pacer.fps = v; governor.setTarget(v || 60); savePrefs(); },
    setQuality(v) { governor.setMode(v); savePrefs(); },
    rescale() { applyQuality(governor.tier, governor.scale); },
  };

  // ---------------------------------------------------------------- ui
  panel = buildSettings(app);
  panel.onToggle = (open) => { if (open) input.unlock(); };
  const hint = $('hint'), badge = $('mode-badge'), crosshair = $('crosshair'), promptEl = $('prompt');
  const setHint = (html) => { hint.innerHTML = html; hint.hidden = !html; };
  const lockHint = 'Click to look around · <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> move · <kbd>Tab</kbd> settings';
  const touchHint = 'Left thumb moves (drag past the ring to run) · drag elsewhere to look · <kbd>☰</kbd> settings';
  const showTouchHint = () => {
    if (TEST) return;
    setHint(touchHint);
    setTimeout(() => { if (hint.innerHTML === touchHint) setHint(''); }, 9000);
  };
  if (input.touch) showTouchHint();
  else setHint(TEST ? '' : lockHint);
  touch.onStart = showTouchHint;
  input.onLockChange = (locked) => {
    crosshair.hidden = !locked;
    setHint(locked ? '' : lockHint);
    if (locked && panel.open) panel.toggle(false);
  };
  let badgeTimer = 0;
  const showBadge = (text) => { badge.textContent = text; badge.hidden = false; badge.style.opacity = 1; badgeTimer = 2.2; };
  const modeNames = { walk: 'On foot', swim: 'Swimming', fly: 'Free fly', boat: 'Boat' };
  player.on('mode', (m) => {
    const helm = input.touch ? 'At the helm · stick: throttle and steer · E leave' : 'At the helm · W/S throttle · A/D steer · V camera · E leave';
    if (!TEST) showBadge(m === 'boat' ? helm : (modeNames[m] || m));
    panel.get('mode')?.set(m === 'fly' ? 'fly' : 'walk');
  });

  // warm up with everything on, so every shader compiles behind the loading screen
  applyQuality('high', 1);

  const onResize = () => {
    renderer.setPixelRatio(pixelRatio());
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    // a phone held upright gets a taller view so the view across stays usable
    camera.fov = camera.aspect < 1 ? THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(31)) / Math.sqrt(camera.aspect))) : 62;
    camera.updateProjectionMatrix();
    const s = renderer.getDrawingBufferSize(new THREE.Vector2());
    droplets.resize(s.x, s.y);
  };
  app.onResize = onResize;
  addEventListener('resize', onResize);
  onResize();

  // ---------------------------------------------------------------- warm up
  status('Compiling shaders…', 0.6);
  player.update(0);
  camera.updateMatrixWorld();
  ocean.update(0.016, 0, camera);
  terrain.update(camera);
  sky.update(0.016, camera, 0);
  await renderer.compileAsync(scene, camera);
  status('Warming up…', 0.9);
  for (let i = 0; i < 10; i++) { sky.update(0.016, camera, 0); await nextFrame(); }
  sky.updateEnvironment(true);
  // render the real frame graph a few times with every LOD drawable, so the
  // pipelines of all passes (prepass, MRT scene pass, shadows) compile behind
  // the loading screen instead of stalling the first seconds of play
  vegetation.prime(true);
  boulders.prime(true);
  for (let i = 0; i < 3; i++) {
    probe.update(camera); grass.update(camera, player); spray.update(0.016); surf.update(0.016); wake.update(0.016, boat.pos);
    composite.update(renderer); post.update(renderer, 0.016, 0); droplets.render();
    pipeline.render();
    await nextFrame();
  }
  vegetation.prime(false);
  boulders.prime(false);
  vegetation.update(camera);
  boulders.update(camera);
  // then start from the chosen quality (phones on Auto start a few rungs down)
  governor.start(governor.mode === 'auto' && PHONE ? 4 : 0);
  $('loader').classList.add('done');

  const timer = new THREE.Timer();
  let time = +(query.get('t') || 0);
  let frozen = query.has('freeze');
  debug.setTime = (t, freeze = true) => { time = t; frozen = freeze; };
  let fpsAcc = 0, fpsFrames = 0;
  let wasUnder = false, underTime = 0;
  let lastSunKey = '';
  renderer.setAnimationLoop(() => {
    if (!pacer.ready(performance.now())) return;    // the frame rate cap
    governor.begin();
    timer.update();
    const rawDt = timer.getDelta();
    const realDt = Math.min(rawDt, 0.1);
    const dt = frozen ? 0 : realDt;
    time += dt;
    env.time.value = time;
    env.dt.value = dt;

    // --- time of day
    if (app.daySpeed > 0) {
      app.hour = (app.hour + realDt * app.daySpeed / 60) % 24;
      const s = sunFromHour(app.hour);
      const key = `${s.el.toFixed(2)}|${s.az.toFixed(2)}`;
      if (key !== lastSunKey) {
        lastSunKey = key;
        setSun(s.el, s.az);
        panel.get('sunEl')?.set(s.el); panel.get('sunAz')?.set(s.az);
      }
    }
    // darker scenes get a little more exposure (eyes adapt at dusk and night)
    const adapt = THREE.MathUtils.lerp(1, 2.6, env.nightFactor.value) * THREE.MathUtils.lerp(1, 1.35, THREE.MathUtils.smoothstep(12 - app.sunEl, 0, 12));
    // ...and to the place: what an open scene would read under this sky
    const lumOf = (c) => c.r * 0.2126 + c.g * 0.7152 + c.b * 0.0722;
    const refLum = 0.075 * (lumOf(env.sunColor.value) * Math.max(env.sunDir.value.y, 0) + lumOf(env.skyIrradiance.value));
    renderer.toneMappingExposure = app.exposureBias * adapt * autoExposure.update(realDt, refLum);
    if (TEST && debug.frame % 8 === 4) console.log(`[exposure] lum ${autoExposure.lum?.toFixed(4)} ref ${refLum.toFixed(4)} factor ${autoExposure.factor.toFixed(2)}`);

    // --- player + interaction
    if (input.pressed('Tab')) panel.toggle();
    if (input.pressed('KeyF')) { flashlight.toggle(); panel.get('torch')?.set(flashlight.on); }
    if (input.pressed('KeyE')) {
      if (player.mode === 'boat') boat.leave(player);
      else if (player.mode !== 'fly' && boat.canBoard(player.eye)) boat.board(player);
    }
    boat.update(dt, time, player.mode === 'boat' ? input : null, env);
    boat.matrixWorldInverse.copy(boat.group.matrixWorld).invert();
    village.update(realDt, performance.now() / 1000, env);
    player.update(realDt);
    flashlight.update(camera, realDt);
    // context prompt
    const near = player.mode !== 'boat' && player.mode !== 'fly' && boat.canBoard(player.eye);
    const promptText = near ? 'Press <kbd>E</kbd> to take the helm' : '';
    if (promptEl.dataset.t !== promptText) { promptEl.innerHTML = promptText; promptEl.hidden = !promptText; promptEl.dataset.t = promptText; }

    // --- water state at the eye
    camera.updateMatrixWorld();
    const eyeWater = probe.eyeHeight(camera);
    const under = camera.position.y < eyeWater;
    env.cameraUnderwater.value = under ? 1 : 0;
    env.cameraDepth.value = eyeWater - camera.position.y;
    composite.eyeWaterHeight.value = eyeWater;
    composite.flashIntensity.value = flashlight.light.intensity;
    underTime = under ? underTime + realDt : underTime;
    if (wasUnder && !under) { droplets.splash(THREE.MathUtils.clamp(underTime / 1.2, 0.25, 1)); underTime = 0; }
    wasUnder = under;
    droplets.update(realDt, under);

    ocean.update(dt, time, camera, eyeWater);
    if (on('wake')) wake.update(dt, boat.pos);
    if (on('surf')) surf.update(dt);
    if (on('spray')) spray.update(dt);
    terrain.update(camera);
    if (on('veg')) { vegetation.update(camera); boulders.update(camera); }
    if (on('grass')) grass.update(camera, player);
    if (on('fish')) fish.update(dt, time, player.mode === 'swim' || under ? camera.position : boat.pos, on('whale') ? whale.body : null);
    if (on('whale')) whale.update(dt, time, camera.position);
    if (on('birds')) birds.update(realDt, performance.now() / 1000);
    if (on('crabs')) crabs.update(realDt, player);
    reefLife.enabled = on('reef');
    reefLife.update(camera, under);
    motes.update(camera);
    for (const ev of whale.events.splice(0)) if (ev.type === 'splash') audio.splash(ev.pos, 2.5 * ev.strength);
    audio.update({
      camera, underwater: under, shoreDist: island.sdfAt(camera.position.x, camera.position.z),
      heightAboveGround: camera.position.y - Math.max(island.heightAt(camera.position.x, camera.position.z), 0),
      wind: env.windSpeed.value, night: env.nightFactor.value, treeDensity: 0.3, surf: shore.swellHeight.value,
      boat: boat.pos, boatSpeed: Math.abs(boat.speed), whale: whale.pos,
    });
    probe.update(camera);
    caustics.update(camera);
    sky.update(dt, camera, time);
    sky.updateEnvironment();
    composite.update(renderer);
    post.update(renderer, realDt, time);
    droplets.render();
    // the lower tiers redraw the far shadow cascades every second or third frame
    csm.lights.forEach((l, i) => {
      const every = tier.cascades[i] || 1;
      l.shadow.autoUpdate = every === 1;
      if (every > 1) l.shadow.needsUpdate = (debug.frame + i) % every === 0;
    });
    pipeline.render();
    if (governor.enabled) governor.done();

    // --- hud
    if (badgeTimer > 0) {
      badgeTimer -= realDt;
      if (badgeTimer <= 0.6) badge.style.opacity = Math.max(0, badgeTimer / 0.6);
      if (badgeTimer <= 0) badge.hidden = true;
    }
    // the real rate (the simulation's step is clamped, the counter is not)
    fpsAcc += rawDt; fpsFrames++;
    if (fpsAcc > 0.5) {
      $('fps-value').textContent = Math.round(fpsFrames / fpsAcc);
      $('fps-ms').textContent = `${(fpsAcc / fpsFrames * 1000).toFixed(1)} ms · ${Math.round(app.resolutionScale * 100)}% ${governor.tier}`;
      fpsAcc = 0; fpsFrames = 0;
    }
    input.endFrame();
    debug.frame++;
    if (TEST && debug.frame <= 6) console.log(`[frame] ${debug.frame} at ${performance.now().toFixed(0)}ms`);
    debug.ready = debug.frame > 2;
    frameWaiters = frameWaiters.filter((w) => (--w.left <= 0 ? (w.res(), false) : true));
  });

  // ---------------------------------------------------------------- debug hooks
  Object.assign(debug, app, { app });
  debug.stats = () => ({ frame: debug.frame, oceanPatches: ocean.selector.count, terrainPatches: terrain.selector.count, hs: +ocean.fft.stats.hs.toFixed(2), mode: player.mode });
  // yaw: 0 = north (-z), 90 = east (+x)
  debug.look = (yaw, pitch, x, y, z) => {
    if (x === undefined) { x = player.eye.x; y = player.eye.y; z = player.eye.z; }
    player.setView(x, y, z, yaw, pitch);
    player.update(0);
  };
  debug.setSun = setSun;
  debug.prewarmSurf = (seconds = 16, step = 0.25) => surf.prewarm(seconds, step, time);
}

start().catch((e) => {
  console.error(e);
  if (e instanceof NoWebGPU) { status('WebGPU needed', 0); $('loader').classList.add('no-gpu'); }
  $('loader-error').hidden = false;
  $('loader-error').textContent = String(e && e.message || e);
});

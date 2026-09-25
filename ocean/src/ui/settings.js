// Wires the settings panel to the simulation and renderer.

import { Panel } from './panel.js';

const debounce = (fn, ms) => {
  let t = 0;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
};

const SEA_PRESETS = {
  glassy: { wind: 2.5, dir: 20, swell: 0.35, chop: 0.6, caps: 0.7, surf: 0.45 },
  calm: { wind: 5, dir: 20, swell: 0.55, chop: 0.8, caps: 0.55, surf: 0.65 },
  breezy: { wind: 7, dir: 20, swell: 0.7, chop: 0.95, caps: 0.42, surf: 0.85 },
  choppy: { wind: 11, dir: 25, swell: 0.9, chop: 1.1, caps: 0.3, surf: 1.15 },
  storm: { wind: 17, dir: 30, swell: 1.4, chop: 1.25, caps: 0.18, surf: 1.6 },
};

export function buildSettings(app) {
  const { ocean, water, shore, sky, composite, caustics, pipeline, renderer, player, flashlight } = app;
  const panel = new Panel(document.getElementById('panel'), document.getElementById('panel-toggle'), document.getElementById('panel-body'));
  panel.header('Saltwind Cove', 'WebGPU ocean · settings');
  const P = ocean.params;
  const rebuild = debounce(() => {
    ocean.fft.updateSpectrum();
    water.updateRoughnessTable();
    app.onSpectrumChanged?.();
  }, 180);

  // ------------------------------------------------------------ sea state
  const sea = panel.section('Sea state', { open: true, icon: '≋' });
  panel.buttons(sea, Object.keys(SEA_PRESETS).map((k) => [k[0].toUpperCase() + k.slice(1), () => applyPreset(k)]));
  panel.slider(sea, { id: 'wind', label: 'Wind speed', min: 0.5, max: 20, step: 0.1, value: P.local.windSpeed, format: (v) => `${v.toFixed(1)} m/s`,
    onInput: (v) => { P.local.windSpeed = v; rebuild(); } });
  panel.slider(sea, { id: 'windDir', label: 'Wind direction', min: 0, max: 360, step: 1, value: P.local.windDirection, format: (v) => `${v.toFixed(0)}°`,
    onInput: (v) => { P.local.windDirection = v; rebuild(); } });
  panel.slider(sea, { id: 'fetch', label: 'Fetch', min: 5, max: 400, step: 1, value: P.local.fetch, format: (v) => `${v.toFixed(0)} km`,
    hint: 'How far the wind has blown over open water: short fetch = young, steep chop', onInput: (v) => { P.local.fetch = v; rebuild(); } });
  panel.slider(sea, { id: 'swell', label: 'Ocean swell', min: 0, max: 2, step: 0.01, value: P.swellSpectrum.scale, format: (v) => v.toFixed(2),
    onInput: (v) => { P.swellSpectrum.scale = v; rebuild(); } });
  panel.slider(sea, { id: 'swellDir', label: 'Swell direction', min: 0, max: 360, step: 1, value: P.swellSpectrum.windDirection, format: (v) => `${v.toFixed(0)}°`,
    onInput: (v) => { P.swellSpectrum.windDirection = v; rebuild(); } });
  panel.slider(sea, { id: 'chop', label: 'Choppiness', min: 0, max: 1.6, step: 0.01, value: ocean.fft.choppiness.value,
    onInput: (v) => { ocean.fft.choppiness.value = v; } });
  panel.slider(sea, { id: 'caps', label: 'Whitecaps', min: 0, max: 1, step: 0.01, value: 1 - ocean.fft.foamThreshold.value,
    hint: 'How easily crests break into foam', format: (v) => `${Math.round(v * 100)}%`, onInput: (v) => { ocean.fft.foamThreshold.value = 1 - v; } });
  panel.slider(sea, { id: 'foamLife', label: 'Foam persistence', min: 0.5, max: 8, step: 0.1, value: ocean.fft.foamDecay.value,
    format: (v) => `${v.toFixed(1)} s`, onInput: (v) => { ocean.fft.foamDecay.value = v; } });
  const hsNote = panel.note(sea, '');
  const showHs = () => { hsNote.textContent = `Significant wave height ≈ ${ocean.fft.stats.hs.toFixed(2)} m · peak wavelength ≈ ${ocean.fft.stats.peakWavelength.toFixed(0)} m`; };
  app.onSpectrumChanged = showHs;
  showHs();

  // ------------------------------------------------------------ surf
  const surf = panel.section('Surf & shoreline', { icon: '◠' });
  panel.slider(surf, { id: 'surf', label: 'Breaker height', min: 0, max: 2, step: 0.01, value: shore.swellHeight.value, format: (v) => `${v.toFixed(2)} m`,
    onInput: (v) => { shore.swellHeight.value = v; } });
  panel.slider(surf, { id: 'period', label: 'Swell period', min: 6, max: 15, step: 0.1, value: shore.period.value, format: (v) => `${v.toFixed(1)} s`,
    hint: 'Longer period swell feels the bottom earlier and refracts more', onInput: debounce((v) => { shore.setPeriod(v); }, 500) });
  panel.slider(surf, { id: 'sets', label: 'Waves per set', min: 3, max: 14, step: 0.1, value: shore.setLength.value, format: (v) => v.toFixed(1),
    onInput: (v) => { shore.setLength.value = v; } });
  panel.slider(surf, { id: 'peaks', label: 'Peak width', min: 20, max: 160, step: 1, value: shore.peakWidth.value, format: (v) => `${v.toFixed(0)} m`,
    hint: 'Along-shore size of the breaking sections', onInput: (v) => { shore.peakWidth.value = v; } });

  // ------------------------------------------------------------ sky
  const skySec = panel.section('Sun & sky', { open: true, icon: '☀' });
  panel.slider(skySec, { id: 'sunEl', label: 'Sun elevation', min: -14, max: 85, step: 0.1, value: app.sunEl, format: (v) => `${v.toFixed(1)}°`,
    onInput: (v) => { app.setSun(v, app.sunAz); } });
  panel.slider(skySec, { id: 'sunAz', label: 'Sun azimuth', min: 0, max: 360, step: 0.5, value: app.sunAz, format: (v) => `${v.toFixed(0)}°`,
    onInput: (v) => { app.setSun(app.sunEl, v); } });
  panel.slider(skySec, { id: 'daySpeed', label: 'Time flow', min: 0, max: 60, step: 0.5, value: 0, format: (v) => (v === 0 ? 'paused' : `×${v.toFixed(1)}`),
    hint: 'Animate the sun across the sky (1 game minute per real second at ×1)', onInput: (v) => { app.daySpeed = v; } });
  panel.slider(skySec, { id: 'coverage', label: 'Cloud cover', min: 0, max: 1, step: 0.01, value: sky.coverage.value, format: (v) => `${Math.round(v * 100)}%`,
    onInput: (v) => { sky.coverage.value = v; sky.warm = 0; } });
  panel.slider(skySec, { id: 'cloudDensity', label: 'Cloud density', min: 4, max: 60, step: 0.5, value: sky.cloudDensity.value, format: (v) => v.toFixed(1),
    onInput: (v) => { sky.cloudDensity.value = v; sky.warm = 0; } });
  panel.slider(skySec, { id: 'cirrus', label: 'Cirrus', min: 0, max: 1, step: 0.01, value: sky.cirrusAmount.value, format: (v) => `${Math.round(v * 100)}%`,
    onInput: (v) => { sky.cirrusAmount.value = v; sky.warm = 0; } });
  panel.slider(skySec, { id: 'exposure', label: 'Exposure', min: 0.15, max: 1.6, step: 0.01, value: renderer.toneMappingExposure, format: (v) => v.toFixed(2),
    onInput: (v) => { app.exposureBias = v; } });

  // ------------------------------------------------------------ water
  const wat = panel.section('Water', { icon: '◌' });
  panel.slider(wat, { id: 'vis', label: 'Underwater visibility', min: 0.3, max: 2.5, step: 0.01, value: composite.underwaterVisibility.value, format: (v) => `×${v.toFixed(2)}`,
    onInput: (v) => { composite.underwaterVisibility.value = v; } });
  panel.slider(wat, { id: 'caustics', label: 'Caustics', min: 0, max: 2, step: 0.01, value: caustics.intensity.value, format: (v) => v.toFixed(2),
    onInput: (v) => { caustics.intensity.value = v; } });
  panel.slider(wat, { id: 'foamAmt', label: 'Foam brightness', min: 0, max: 2, step: 0.01, value: water.foamScale.value, format: (v) => v.toFixed(2),
    onInput: (v) => { water.foamScale.value = v; } });
  panel.slider(wat, { id: 'sss', label: 'Crest glow (SSS)', min: 0, max: 2, step: 0.01, value: water.sssStrength.value, format: (v) => v.toFixed(2),
    onInput: (v) => { water.sssStrength.value = v; } });
  panel.slider(wat, { id: 'glare', label: 'Sun glitter', min: 0, max: 1.5, step: 0.01, value: water.glare.value, format: (v) => v.toFixed(2),
    onInput: (v) => { water.glare.value = v; } });
  panel.toggleRow(wat, { id: 'ssr', label: 'Screen-space reflections', value: water.ssrEnabled.value > 0.5, onChange: (v) => { water.ssrEnabled.value = v ? 1 : 0; } });
  panel.toggleRow(wat, { id: 'shafts', label: 'Underwater light shafts', value: composite.shafts.value > 0.5, onChange: (v) => { composite.shafts.value = v ? 1 : 0; } });

  // ------------------------------------------------------------ graphics
  const gfx = panel.section('Graphics', { icon: '◧' });
  if (app.frame) {
    panel.choice(gfx, { id: 'fps', label: 'Frame rate', value: app.frame.fps, options: [[20, '20'], [30, '30'], [40, '40'], [50, '50'], [0, 'No limit']],
      onChange: (v) => app.frame.setFps(v) });
    panel.choice(gfx, { id: 'quality', label: 'Quality', value: app.frame.quality, options: [['auto', 'Auto'], ['low', 'Low'], ['medium', 'Medium'], ['high', 'High']],
      onChange: (v) => app.frame.setQuality(v) });
    panel.note(gfx, 'The game lowers the render resolution (and with Auto quality, the effects) as needed to hold the frame rate.');
  }
  panel.slider(gfx, { id: 'res', label: 'Resolution', min: 0.4, max: 1.5, step: 0.05, value: app.resolutionMax, format: (v) => `${Math.round(v * 100)}%`,
    hint: 'The most the game renders at; it goes below this when it needs to for the frame rate',
    onInput: debounce((v) => { app.resolutionMax = v; app.frame ? app.frame.rescale() : app.onResize?.(); }, 150) });
  if (app.vegetation) {
    panel.slider(gfx, { id: 'vegDetail', label: 'Vegetation detail', min: 0.4, max: 1.6, step: 0.05, value: app.vegetation.lodScale, format: (v) => `×${v.toFixed(2)}`,
      onInput: (v) => { app.vegetation.setDetail(v); } });
  }
  if (app.autoExposure) panel.toggleRow(gfx, { id: 'adapt', label: 'Eye adaptation', value: app.autoExposure.enabled, onChange: (v) => { app.autoExposure.enabled = v; } });
  panel.slider(gfx, { id: 'ao', label: 'Ambient occlusion', min: 0, max: 1, step: 0.01, value: pipeline.aoIntensity.value, format: (v) => v.toFixed(2),
    onInput: (v) => { pipeline.aoIntensity.value = v; } });
  panel.slider(gfx, { id: 'contact', label: 'Contact shadows', min: 0, max: 1, step: 0.01, value: pipeline.contactStrength.value, format: (v) => v.toFixed(2),
    onInput: (v) => { pipeline.contactStrength.value = v; } });
  panel.slider(gfx, { id: 'bloom', label: 'Bloom', min: 0, max: 0.5, step: 0.005, value: pipeline.bloomPass.strength.value, format: (v) => v.toFixed(3),
    onInput: (v) => { pipeline.bloomPass.strength.value = v; } });
  if (app.post) {
    panel.slider(gfx, { id: 'sharpen', label: 'Sharpen', min: 0, max: 1, step: 0.01, value: app.post.sharpen.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.sharpen.value = v; } });
    panel.slider(gfx, { id: 'mblur', label: 'Motion blur', min: 0, max: 1, step: 0.01, value: app.post.motionBlur.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.motionBlur.value = v; } });
    panel.slider(gfx, { id: 'flare', label: 'Lens flare', min: 0, max: 2, step: 0.01, value: app.post.flare.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.flare.value = v; } });
    panel.slider(gfx, { id: 'godrays', label: 'God rays', min: 0, max: 1.5, step: 0.01, value: app.post.godRays.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.godRays.value = v; } });
    panel.slider(gfx, { id: 'vignette', label: 'Vignette', min: 0, max: 1, step: 0.01, value: app.post.vignette.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.vignette.value = v; } });
    panel.slider(gfx, { id: 'grain', label: 'Film grain', min: 0, max: 1, step: 0.01, value: app.post.grain.value, format: (v) => v.toFixed(2),
      onInput: (v) => { app.post.grain.value = v; } });
  }

  // ------------------------------------------------------------ player
  const pl = panel.section('Explore', { icon: '⌖' });
  panel.buttons(pl, [
    ['Beach', () => app.teleport('beach')], ['Pier', () => app.teleport('pier')],
    ['Reef', () => app.teleport('reef')], ['Boat', () => app.teleport('boat')],
  ]);
  panel.choice(pl, { id: 'mode', label: 'Mode', value: player.mode === 'fly' ? 'fly' : 'walk', options: [['walk', 'On foot'], ['fly', 'Free fly']],
    onChange: (v) => player.setMode(v) });
  panel.slider(pl, { id: 'sens', label: 'Mouse sensitivity', min: 0.4, max: 3, step: 0.05, value: 1, format: (v) => `×${v.toFixed(2)}`,
    onInput: (v) => { player.sensitivity = 0.0021 * v; } });
  panel.toggleRow(pl, { id: 'torch', label: 'Flashlight', value: flashlight.on, onChange: (v) => flashlight.toggle(v) });
  if (app.audio) {
    panel.slider(pl, { id: 'volume', label: 'Volume', min: 0, max: 1, step: 0.01, value: app.audio.volume, format: (v) => `${Math.round(v * 100)}%`,
      onInput: (v) => app.audio.setVolume(v) });
  }

  const keys = panel.section('Controls', { icon: '⌨' });
  panel.keys(keys, [
    ['Click', 'capture mouse / look'],
    ['W A S D', 'move'],
    ['Shift', 'run / swim fast / fly fast'],
    ['Space', 'jump · swim up · fly up'],
    ['C', 'swim down · fly down'],
    ['E', 'board / leave the boat'],
    ['V', 'boat: 1st / 3rd person'],
    ['F', 'flashlight'],
    ['G', 'free fly on / off'],
    ['Tab', 'this panel'],
  ]);
  panel.note(keys, 'In the boat: W/S throttle, A/D steer. Free fly drops you with gravity when you switch back.');

  function applyPreset(k) {
    const p = SEA_PRESETS[k];
    panel.get('wind').set(p.wind, true);
    panel.get('windDir').set(p.dir, true);
    panel.get('swell').set(p.swell, true);
    panel.get('chop').set(p.chop, true);
    panel.get('caps').set(p.caps, true);
    panel.get('surf').set(p.surf, true);
  }

  return panel;
}

// Frame graph.
//
//   prepass  (opaque, cheap: lighting skipped)  -> depth, view normal, velocity
//   GTAO     half-res, temporally filtered      -> indirect-only AO via context
//   SSS      screen-space contact shadows       -> sun shadow term via context
//   scene    HDR colour + aux (water face mask, TAA reactivity)
//   composite underwater volume / aerial haze / god rays / meniscus
//   TAA -> motion blur -> bloom + lens flare -> exposure, ACES, grade, vignette

import * as THREE from 'three/webgpu';
import {
  Fn, pass, mrt, output, normalView, velocity, vec2, vec3, vec4, float, context, screenUV, uniform,
  packNormalToRGB, unpackRGBToNormal, sample, frontFacing, select, positionWorld, mix, clamp,
} from 'three/tsl';
import { ao } from 'three/addons/tsl/display/GTAONode.js';
import { sss } from 'three/addons/tsl/display/SSSNode.js';
import { traa } from 'three/addons/tsl/display/TRAANode.js';
import { bloom } from 'three/addons/tsl/display/BloomNode.js';

export const LAYER_NO_PREPASS = 3;

export class Pipeline {
  constructor({ renderer, scene, camera, sun }) {
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;
    this.sun = sun;
    this.sunShadowTerms = [];   // (builder) => float node, multiplied into the sun's shadow
    this.lightShadowTerms = []; // { light, fn: (builder) => node } for any other light
    this.aoTerms = [];          // (builder) => float node, multiplied into indirect light
    this.composites = [];       // (color, ctx) => color, run in HDR before TAA
    this.post = [];             // (color, ctx) => color, after TAA before tonemapping
    this.settings = { ao: true, contactShadows: true, taa: true, bloom: true };
    this.aoIntensity = uniform(1);
    this.contactStrength = uniform(0.75);
    camera.layers.enable(LAYER_NO_PREPASS);
  }

  build() {
    const { renderer, scene, camera } = this;
    const rp = this.renderPipeline = new THREE.RenderPipeline(renderer);

    // ------------------------------------------------------------ prepass
    const prePass = this.prePass = pass(scene, camera);
    prePass.name = 'prepass';
    prePass.transparent = false;
    const preLayers = new THREE.Layers();
    preLayers.enableAll();
    preLayers.disable(LAYER_NO_PREPASS);
    prePass.setLayers(preLayers);
    prePass.setMRT(mrt({ output: packNormalToRGB(normalView), velocity }));
    prePass.contextNode = context({ prepass: true });
    prePass.getTexture('output').type = THREE.UnsignedByteType;
    const preNormal = sample((uv) => unpackRGBToNormal(prePass.getTextureNode().sample(uv)));
    const preDepth = this.preDepth = prePass.getTextureNode('depth');
    const preVelocity = this.preVelocity = prePass.getTextureNode('velocity');

    // ------------------------------------------------------------ AO / contact shadows
    const aoPass = this.aoPass = ao(preDepth, preNormal, camera);
    aoPass.resolutionScale = 0.5;
    aoPass.useTemporalFiltering = true;
    aoPass.radius.value = 0.55;
    aoPass.thickness.value = 0.6;
    aoPass.distanceFallOff.value = 1.0;
    aoPass.samples.value = 12;
    const aoTex = aoPass.getTextureNode();

    const sssPass = this.sssPass = sss(preDepth, camera, this.sun);
    sssPass.maxDistance.value = 0.35;
    sssPass.thickness.value = 0.03;
    sssPass.shadowIntensity.value = 1;
    sssPass.quality.value = 0.5;
    sssPass.resolutionScale = 0.5;
    sssPass.useTemporalFiltering = true;
    const sssTex = sssPass.getTextureNode();

    // ------------------------------------------------------------ scene pass
    const scenePass = this.scenePass = pass(scene, camera);
    scenePass.name = 'scene';
    const auxNode = Fn((inputs, builder) => {
      const m = builder.material;
      if (m && m.isWaterMaterial) return vec4(select(frontFacing, float(1), float(0.5)), 0.55, 0, 0);
      if (m && m.userData && m.userData.reactive) return vec4(0, m.userData.reactive, 0, 0);
      return vec4(0);
    })();
    scenePass.setMRT(mrt({ output, aux: auxNode }));
    const self = this;
    scenePass.contextNode = context({
      getAO: (inputNode, builder) => {
        const m = builder.material;
        if (m.transparent === true || (m.userData && m.userData.noAO)) return inputNode;
        let a = mix(float(1), aoTex.sample(screenUV).r, self.aoIntensity);
        for (const t of self.aoTerms) { const n = t(builder); if (n) a = a.mul(n); }
        return inputNode !== null ? inputNode.mul(a) : a;
      },
      getShadow: (lightNode, builder) => {
        let s = lightNode.shadowColorNode;
        if (lightNode.light === self.sun) {
          const m = builder.material;
          if (!(m.userData && m.userData.noContactShadow)) {
            s = s.mul(mix(float(1), sssTex.sample(screenUV).r, self.contactStrength));
          }
          for (const t of self.sunShadowTerms) { const n = t(builder); if (n) s = s.mul(n); }
        }
        for (const t of self.lightShadowTerms) {
          if (t.light !== lightNode.light) continue;
          const n = t.fn(builder);
          if (n) s = s ? s.mul(n) : n;
        }
        return s;
      },
    });
    const sceneColor = this.sceneColor = scenePass.getTextureNode('output');
    const aux = this.aux = scenePass.getTextureNode('aux');
    const sceneDepth = this.sceneDepth = scenePass.getTextureNode('depth');

    // ------------------------------------------------------------ composite (HDR)
    this.resolution = uniform(new THREE.Vector2(1, 1));
    const ctx = { aux, sceneDepth, preDepth, velocity: preVelocity, camera, scenePass, prePass, sceneColorNode: sceneColor, resolution: this.resolution };
    let color = sceneColor;
    for (const c of this.composites) color = c(color, ctx);

    // ------------------------------------------------------------ TAA
    const taaPass = this.taaPass = traa(color, preDepth, preVelocity, camera);
    taaPass.useSubpixelCorrection = false;
    color = taaPass;
    ctx.postTexture = taaPass.getTextureNode();
    Object.assign(ctx, this.ctxExtra || {});

    for (const p of this.post) color = p(color, ctx);

    // ------------------------------------------------------------ bloom
    const bloomPass = this.bloomPass = bloom(color, 0.12, 0.35, 1.2);
    color = color.add(bloomPass);
    for (const p of (this.finals || [])) color = p(color, ctx);

    rp.outputNode = color;
    return rp;
  }

  render() {
    const size = this.renderer.getDrawingBufferSize(new THREE.Vector2());
    this.resolution.value.copy(size);
    this.renderPipeline.render();
  }
}

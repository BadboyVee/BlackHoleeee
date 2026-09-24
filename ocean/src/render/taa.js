// TRAA with a reactive mask.
//
// three's TRAANode keeps ~95% history everywhere. The ocean surface, spray
// and particles move without matching velocity (their motion is procedural),
// so their history is reprojected as if static and glints and foam smear.
// Materials write a "reactivity" into the scene pass's aux target (water
// 0.55, spray 1); here it raises the current-frame weight and tightens the
// variance clip for those pixels. Everything else is three's resolve.

import { FloatType, Vector2 } from 'three/webgpu';
import { float, Fn, max, texture, uv, vec2, ivec2, mix, context, velocity, OnBeforeRenderPipeline, OnAfterRenderPipeline, convertToTexture } from 'three/tsl';
import TRAANode from 'three/addons/tsl/display/TRAANode.js';
import { clipAABB, flickerReduction, sampleCurrentDepth, samplePreviousDepth } from 'three/addons/tsl/utils/TAAUtils.js';

const _size = new Vector2();

class ReactiveTRAANode extends TRAANode {
  constructor(beautyNode, depthNode, velocityNode, camera, reactiveNode) {
    super(beautyNode, depthNode, velocityNode, camera);
    this.reactiveNode = reactiveNode;
    this.reactiveStrength = 0.75;
  }

  setup(builder) {
    if (builder.renderPipeline && !builder.context.renderPipelineState.viewOffsetOwner) {
      builder.context.renderPipelineState.viewOffsetOwner = this;
      this._needsPostProcessingSync = true;
      OnBeforeRenderPipeline(() => {
        const size = builder.renderer.getDrawingBufferSize(_size);
        this.setViewOffset(size.width, size.height);
      });
      OnAfterRenderPipeline(() => { this.clearViewOffset(); });
    }
    if (builder.renderer.reversedDepthBuffer === true) this._historyRenderTarget.depthTexture.type = FloatType;
    this._velocityNode = builder.context.velocity !== undefined ? builder.context.velocity : velocity;

    const varianceClipping = Fn(([positionTexel, currentColor, historyColor, gamma]) => {
      const offsets = [[-1, -1], [-1, 1], [1, -1], [1, 1], [1, 0], [0, -1], [0, 1], [-1, 0]];
      const moment1 = currentColor.toVar();
      const moment2 = currentColor.pow2().toVar();
      for (const [x, y] of offsets) {
        const neighbor = this.beautyNode.offset(ivec2(x, y)).load(positionTexel).max(0);
        moment1.addAssign(neighbor);
        moment2.addAssign(neighbor.pow2());
      }
      const N = float(offsets.length + 1);
      const mean = moment1.div(N);
      const variance = moment2.div(N).sub(mean.pow2()).max(0).sqrt().mul(gamma);
      const minColor = mean.sub(variance);
      const maxColor = mean.add(variance);
      return clipAABB(mean.clamp(minColor, maxColor), historyColor, minColor, maxColor);
    });

    const historyNode = texture(this._historyRenderTarget.texture);
    const resolve = Fn(() => {
      const uvNode = uv();
      const textureSize = this.beautyNode.size();
      const positionTexel = uvNode.mul(textureSize);
      const currentDepth = sampleCurrentDepth(this.depthNode, positionTexel, this._cameraNearFar);
      const closestDepth = currentDepth.get('closestDepth');
      const closestPositionTexel = currentDepth.get('closestPositionTexel');
      const farthestDepth = currentDepth.get('farthestDepth');
      const offsetUV = this.velocityNode.load(closestPositionTexel).xy.mul(vec2(0.5, -0.5));
      const historyUV = uvNode.sub(offsetUV);
      const previousDepth = samplePreviousDepth(this._previousDepthNode, historyUV, this._previousCameraProjectionMatrixInverse, this._previousCameraWorldMatrix, this._cameraWorldMatrixInverse, this._cameraNearFar, this.camera);
      const isValidUV = historyUV.greaterThanEqual(0).all().and(historyUV.lessThanEqual(1).all());
      const isEdge = farthestDepth.sub(closestDepth).greaterThan(this.edgeDepthDiff);
      const isDisocclusion = closestDepth.sub(previousDepth).greaterThan(this.depthThreshold);
      const hasValidHistory = isValidUV.and(isEdge.or(isDisocclusion.not()));
      const currentColor = this.beautyNode.sample(uvNode);
      const historyColor = historyNode.sample(historyUV);
      const motionFactor = uvNode.sub(historyUV).mul(textureSize).length().div(this.maxVelocityLength).saturate();
      // reactive pixels (procedurally animated surfaces) trust the current frame more
      const reactive = this.reactiveNode ? this.reactiveNode.sample(uvNode).g.mul(this.reactiveStrength) : float(0);
      const currentWeight = float(0.05).toVar();
      currentWeight.assign(hasValidHistory.select(currentWeight.add(motionFactor).add(reactive.mul(0.35)).saturate(), 1));
      const varianceGamma = mix(0.5, 1, motionFactor.oneMinus().pow2()).mul(mix(float(1), float(0.6), reactive));
      const clippedHistoryColor = varianceClipping(positionTexel, currentColor, historyColor, varianceGamma);
      return flickerReduction(currentColor, clippedHistoryColor, currentWeight);
    });
    this._resolveMaterial.contextNode = context(builder.getSharedContext());
    this._resolveMaterial.colorNode = resolve();
    return this._textureNode;
  }
}

export const reactiveTraa = (beautyNode, depthNode, velocityNode, camera, reactiveNode) =>
  new ReactiveTRAANode(convertToTexture(beautyNode), depthNode, velocityNode, camera, reactiveNode);

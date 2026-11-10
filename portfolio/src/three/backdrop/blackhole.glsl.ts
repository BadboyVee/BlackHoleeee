/**
 * Ray-marched Schwarzschild black hole.
 *
 * Units: the Schwarzschild radius Rs is 1. A photon path around a non-spinning
 * black hole has the same shape as a Newtonian particle under the acceleration
 *     a = -1.5 · h² · r̂ / r⁴      (h = |r × v|, conserved)
 * which follows from the orbit equation u'' + u = 1.5·Rs·u². Integrating that
 * backwards from the camera gives the lensed sky, the shadow (radius ≈ 2.6),
 * the photon ring (r = 1.5) and every lensed image of the accretion disk.
 *
 * Performance notes. Everything expensive that does not change per frame is
 * baked once at startup: the starry sky goes into a cube map (one lookup per
 * pixel instead of dozens of noise calls) and the gas turbulence of the disk
 * into a small tileable noise texture. Rays that never come close are bent
 * analytically with the weak-field deflection, and the integrator evaluates
 * the force once per step (kick-drift-kick with the force carried over).
 */

/* ------------------------------------------------------------------ */
/* Sky bake: rendered once into a cube map.                            */
/* ------------------------------------------------------------------ */

export const skyVertexShader = /* glsl */ `
  varying vec3 vDir;
  void main() {
    vDir = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

export const skyFragmentShader = /* glsl */ `
  precision highp float;
  varying vec3 vDir;
  uniform float uPixel;   // angular size of one cube-map texel

  float hash13(vec3 p3) {
    p3 = fract(p3 * 0.1031);
    p3 += dot(p3, p3.zyx + 31.32);
    return fract((p3.x + p3.y) * p3.z);
  }

  vec3 hash33(vec3 p3) {
    p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yxz + 33.33);
    return fract((p3.xxy + p3.yxx) * p3.zyx);
  }

  float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(mix(hash13(i), hash13(i + vec3(1, 0, 0)), u.x),
          mix(hash13(i + vec3(0, 1, 0)), hash13(i + vec3(1, 1, 0)), u.x), u.y),
      mix(mix(hash13(i + vec3(0, 0, 1)), hash13(i + vec3(1, 0, 1)), u.x),
          mix(hash13(i + vec3(0, 1, 1)), hash13(i + vec3(1, 1, 1)), u.x), u.y),
      u.z);
  }

  float fbm(vec3 p) {
    float sum = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 4; i++) {
      sum += amp * noise(p);
      p = p * 2.07 + vec3(17.13, 3.71, 9.27);
      amp *= 0.5;
    }
    return sum;
  }

  vec3 starLayer(vec3 dir, float scale, float density, float seed) {
    vec3 p = dir * scale;
    vec3 cell = floor(p);
    float h = hash13(cell + seed);
    if (h > density) return vec3(0.0);
    vec3 rnd = hash33(cell + seed * 1.37);
    vec3 d = cell + 0.25 + 0.5 * rnd - p;
    d -= dir * dot(d, dir);
    float radius = uPixel * scale * (0.7 + 0.6 * rnd.z);
    float core = 1.0 - smoothstep(0.0, radius, length(d));
    float bright = pow(h / density, 8.0) * 2.2 + 0.07;
    vec3 tint = mix(vec3(0.62, 0.74, 1.0), vec3(1.0, 0.82, 0.62), rnd.y);
    return tint * core * core * bright;
  }

  void main() {
    vec3 dir = normalize(vDir);
    vec3 col = vec3(0.0);
    col += starLayer(dir, 30.0, 0.09, 1.0);
    col += starLayer(dir, 75.0, 0.07, 7.0) * 0.75;
    col += starLayer(dir, 160.0, 0.06, 13.0) * 0.45;

    // A faint galactic band with dust, tilted across the sky.
    vec3 bandNormal = normalize(vec3(0.35, 1.0, -0.42));
    float lat = dot(dir, bandNormal);
    float band = exp(-lat * lat * 9.0);
    float clouds = fbm(dir * 3.2 + vec3(0.0, 0.0, 4.0));
    float dust = fbm(dir * 7.5 + vec3(5.0));
    vec3 glow = mix(vec3(0.12, 0.06, 0.22), vec3(0.35, 0.16, 0.08), clouds);
    col += glow * band * smoothstep(0.3, 0.9, clouds) * (1.0 - 0.8 * smoothstep(0.45, 0.7, dust)) * 0.22;
    col += vec3(0.05, 0.03, 0.09) * smoothstep(0.4, 0.95, fbm(dir * 1.6 + 11.0)) * 0.22;

    // Stored at half scale (so bright stars survive an 8-bit target) and in
    // square-root space, which keeps enough levels in the dark nebula to avoid banding.
    gl_FragColor = vec4(sqrt(min(col * 0.5, vec3(1.0))), 1.0);
  }
`

/* ------------------------------------------------------------------ */
/* Main pass.                                                          */
/* ------------------------------------------------------------------ */

export const vertexShader = /* glsl */ `
  void main() {
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`

export const fragmentShader = /* glsl */ `
  precision highp float;

  uniform vec2 uResolution;
  uniform float uTime;
  uniform vec3 uCamPos;
  uniform vec3 uCamRight;
  uniform vec3 uCamUp;
  uniform vec3 uCamFwd;
  uniform float uTanHalfFov;
  uniform vec2 uShift;
  uniform float uRoll;
  uniform float uExposure;
  uniform float uDim;
  uniform float uDisk;
  uniform float uStars;
  uniform float uDoppler;
  uniform float uSpin;
  uniform int uSteps;
  uniform float uStepScale;
  uniform float uSkyLod;
  uniform vec3 uBg;
  uniform samplerCube uSky;
  uniform sampler2D uNoise;

  #define R_IN 2.6
  #define R_OUT 12.5
  #define ESCAPE 14.5
  #define TAU 6.2831853

  float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
  }

  vec3 sky(vec3 dir) {
    vec3 s = textureLod(uSky, dir, uSkyLod).rgb;
    return s * s * (2.0 * uStars);
  }

  // ---------------------------------------------------------------- disk

  vec3 heat(float t) {
    vec3 c = mix(vec3(0.45, 0.05, 0.01), vec3(1.0, 0.33, 0.07), smoothstep(0.0, 0.4, t));
    c = mix(c, vec3(1.0, 0.68, 0.36), smoothstep(0.4, 0.75, t));
    c = mix(c, vec3(1.0, 0.93, 0.84), smoothstep(0.75, 1.1, t));
    c = mix(c, vec3(0.8, 0.88, 1.0), smoothstep(1.15, 1.7, t));
    return c;
  }

  // Gas texture in co-rotating coordinates. The noise texture tiles, so three
  // copies wrap seamlessly around the orbit; the low angular frequency
  // stretches the turbulence into streaks.
  float gas(float r, float phi, float t, float seed) {
    float ang = phi + t / (r * sqrt(r));          // Keplerian: omega ~ r^-1.5
    vec2 uv = vec2(ang * (3.0 / TAU), r * 0.12 + seed);
    float broad = textureLod(uNoise, uv, 0.0).r;
    float fine = textureLod(uNoise, uv * vec2(2.0, 3.3) + vec2(0.0, 0.37), 0.0).g;
    return broad * 0.62 + fine * 0.6;
  }

  // p: hit point on the disk plane, r: its radius, dir: backwards ray direction.
  vec4 disk(vec3 p, float r, vec3 dir) {
    float phi = atan(p.z, p.x);

    // Differential rotation shears any texture without limit, so blend two copies
    // whose clocks restart half a period apart; each one resets while invisible.
    const float PERIOD = 28.0;
    float t = uTime * uSpin;
    float t1 = mod(t, PERIOD);
    float t2 = mod(t + 0.5 * PERIOD, PERIOD);
    float w = 1.0 - abs(t1 / PERIOD * 2.0 - 1.0);
    float n = mix(gas(r, phi, t2, 0.53), gas(r, phi, t1, 0.0), w);
    float streak = smoothstep(0.3, 0.95, n);

    float x = (r - R_IN) / (R_OUT - R_IN);
    float profile = smoothstep(0.0, 0.04, x) * (1.0 - smoothstep(0.2, 1.0, x));

    // Relativistic Doppler beaming and gravitational redshift (softened for taste).
    vec3 orbit = vec3(p.z, 0.0, -p.x) / r;
    float beta = min(0.72 * inversesqrt(max(r - 1.0, 0.4)), 0.75);
    float gamma = inversesqrt(1.0 - beta * beta);
    float D = 1.0 / (gamma * (1.0 - beta * dot(orbit, -dir)));
    D = mix(1.0, D, uDoppler);
    float g = D * sqrt(max(1.0 - 1.0 / r, 0.05));

    float temperature = pow(R_IN / r, 0.8) * g;
    float intensity = pow(g, 2.6) * pow(R_IN / r, 1.35) * uDisk;

    float grazing = min(1.0 / max(abs(dir.y), 0.08), 7.0);
    float tau = profile * (0.22 + 1.5 * streak) * 0.65 * grazing;
    float alpha = 1.0 - exp(-tau);
    vec3 emission = heat(temperature) * intensity * (0.3 + 1.5 * streak) * alpha * 2.6;
    return vec4(emission, alpha);
  }

  // ---------------------------------------------------------------- lensing

  // Remaining weak-field deflection of a straight ray from pos to infinity.
  vec3 bendWeak(vec3 pos, vec3 dir) {
    float r = length(pos);
    float b = length(cross(pos, dir));
    float s = dot(pos, dir) / r;
    float bend = (1.5 / max(b, 1e-3)) * (0.6666667 - (s - s * s * s / 3.0));
    vec3 peri = pos - dir * dot(pos, dir);
    return normalize(dir - normalize(peri) * bend);
  }

  vec3 trace(vec3 ro, vec3 rd) {
    vec3 pos = ro;
    vec3 vel = rd;
    float r2 = dot(pos, pos);
    float r = sqrt(r2);
    vec3 hv = cross(pos, vel);
    float h2 = dot(hv, hv);

    // Rays that pass outside the disk only get a gentle bend.
    const float FAR_B = R_OUT + 1.2;
    if (r > ESCAPE && h2 > FAR_B * FAR_B) return sky(bendWeak(pos, vel));

    vec3 col = vec3(0.0);
    float trans = 1.0;
    float minR = r;
    float haze = 0.0;
    bool captured = false;
    vec3 acc = -1.5 * h2 * pos / (r2 * r2 * r);

    for (int i = 0; i < 400; i++) {
      if (i >= uSteps) break;
      if (r > ESCAPE && dot(pos, vel) > 0.0) break;

      float dt = clamp(uStepScale * r - 0.03, 0.025, 2.5) * inversesqrt(dot(vel, vel));

      // Kick-drift-kick; the force at the new point is reused by the next step.
      vel += acc * (0.5 * dt);
      vec3 prev = pos;
      pos += vel * dt;
      r2 = dot(pos, pos);
      r = sqrt(r2);
      minR = min(minR, r);
      acc = -1.5 * h2 * pos / (r2 * r2 * r);
      vel += acc * (0.5 * dt);

      if (prev.y * pos.y <= 0.0) {
        vec3 hit = mix(prev, pos, prev.y / (prev.y - pos.y + 1e-7));
        float hr = length(hit.xz);
        if (hr > R_IN && hr < R_OUT) {
          vec4 d = disk(hit, hr, normalize(vel));
          col += trans * d.rgb;
          trans *= 1.0 - d.a;
          if (trans < 0.02) break;
        }
      }

      // Thin glowing haze around the disk plane: a cheap in-shader bloom.
      float rho2 = dot(pos.xz, pos.xz);
      haze += trans * dt * exp(-abs(pos.y) * 2.2)
        * (1.0 - smoothstep(R_IN * R_IN, (R_OUT + 3.0) * (R_OUT + 3.0), rho2))
        * smoothstep(1.44, R_IN * R_IN, rho2);

      if (r2 < 1.0) {
        captured = true;
        break;
      }
    }

    // Out of steps while still deep in the well: almost always a captured photon.
    if (!captured && r < ESCAPE && (r < 3.0 || dot(pos, vel) < 0.0)) captured = true;

    if (!captured) {
      vec3 dir = normalize(vel);
      if (r > ESCAPE) dir = bendWeak(pos, dir);
      col += trans * sky(dir);
      // Photon ring: light skimming the photon sphere at r = 1.5.
      float ring = exp(-pow((minR - 1.56) * 7.0, 2.0));
      col += vec3(1.0, 0.8, 0.58) * ring * 0.55 * uDisk * trans;
    }
    col += vec3(1.0, 0.42, 0.14) * haze * (captured ? 0.006 : 0.05) * uDisk;
    return col;
  }

  // ---------------------------------------------------------------- main

  vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
  }

  void main() {
    vec2 frag = gl_FragCoord.xy;
    vec2 p = (2.0 * frag - uResolution) / uResolution.y;

    float c = cos(uRoll);
    float s = sin(uRoll);
    vec2 q = mat2(c, s, -s, c) * p - uShift;

    vec3 rd = normalize(uCamFwd + (q.x * uCamRight + q.y * uCamUp) * uTanHalfFov);
    vec3 col = trace(uCamPos, rd);

    col = aces(col * uExposure);
    col = pow(col, vec3(1.0 / 2.2));

    // Soft vignette, then settle into the page colour so the canvas edge is invisible.
    float vig = 1.0 - smoothstep(0.35, 2.1, length(p * vec2(0.62, 0.95)));
    col *= mix(0.55, 1.0, vig);
    col = uBg + col * (1.0 - uBg);
    col = mix(col, uBg, uDim);

    col += (hash12(frag + fract(uTime) * 97.0) - 0.5) / 255.0;
    gl_FragColor = vec4(col, 1.0);
  }
`

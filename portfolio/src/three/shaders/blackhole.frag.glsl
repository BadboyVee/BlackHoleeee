// A Schwarzschild black hole, ray-traced per pixel.
//
// Units: the event horizon has radius 1. Light is bent by integrating the
// null-geodesic equation in its Cartesian form,
//
//     x'' = -1.5 * h^2 * x / |x|^5        (h = |x × x'| is conserved)
//
// which reproduces the photon sphere at r = 1.5 and the ~2.6 r shadow exactly.
// Every time a bent ray crosses the equatorial plane it samples the accretion
// disk, so the far side of the disk shows up arched over and under the shadow
// and the thin photon ring appears on its own — nothing here is painted on.

precision highp float;

uniform float uTime;
uniform mat4 uCamWorld;
uniform mat4 uProjInv;
uniform int uSteps;
uniform float uDiskGain;
uniform float uStarGain;
uniform float uDiskSpeed;

varying vec2 vNdc;

#define R_IN 3.0
#define R_OUT 12.5
#define R_ESCAPE 36.0
#define MAX_STEPS 200

// ---------------------------------------------------------------- noise ----

float hash31(vec3 p) {
  p = fract(p * vec3(0.1031, 0.1030, 0.0973));
  p += dot(p, p.yzx + 33.33);
  return fract((p.x + p.y) * p.z);
}

vec3 hash33(vec3 p) {
  p = fract(p * vec3(0.1031, 0.1030, 0.0973));
  p += dot(p, p.yxz + 33.33);
  return fract((p.xxy + p.yxx) * p.zyx);
}

float vnoise(vec3 x) {
  vec3 i = floor(x);
  vec3 f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(mix(hash31(i), hash31(i + vec3(1, 0, 0)), f.x),
        mix(hash31(i + vec3(0, 1, 0)), hash31(i + vec3(1, 1, 0)), f.x), f.y),
    mix(mix(hash31(i + vec3(0, 0, 1)), hash31(i + vec3(1, 0, 1)), f.x),
        mix(hash31(i + vec3(0, 1, 1)), hash31(i + vec3(1, 1, 1)), f.x), f.y),
    f.z);
}

float fbm(vec3 p) {
  float a = 0.5;
  float s = 0.0;
  for (int i = 0; i < 4; i++) {
    s += a * vnoise(p);
    p = p * 2.03 + 17.1;
    a *= 0.5;
  }
  return s;
}

// ---------------------------------------------------------------- stars ----

vec3 starLayer(vec3 d, float scale, float density, float size) {
  vec3 q = d * scale;
  vec3 id = floor(q);
  vec3 f = fract(q);
  vec3 rnd = hash33(id);
  if (rnd.x > density) return vec3(0.0);
  vec3 c = 0.5 + (hash33(id + 11.7) - 0.5) * 0.6;
  float dist = length(f - c);
  float mag = pow(rnd.y, 5.0);
  float twinkle = 0.8 + 0.2 * sin(uTime * (1.0 + rnd.z * 3.0) + rnd.y * 40.0);
  float core = smoothstep(size, 0.0, dist);
  vec3 tint = mix(vec3(1.0, 0.72, 0.5), vec3(0.62, 0.78, 1.0), rnd.z);
  tint = mix(vec3(1.0), tint, 0.65);
  return tint * core * core * (0.25 + 5.0 * mag) * twinkle;
}

vec3 background(vec3 d) {
  vec3 col = vec3(0.0);
  col += starLayer(d, 46.0, 0.55, 0.085);
  col += starLayer(d, 92.0, 0.6, 0.11) * 0.55;
  col += starLayer(d.zxy, 18.0, 0.22, 0.05) * 2.6;

  // A faint dust lane so the lensing has something soft to smear.
  float band = exp(-pow(dot(d, normalize(vec3(0.35, 0.86, -0.36))) * 2.6, 2.0));
  float neb = fbm(d * 2.4 + 4.0);
  neb = pow(smoothstep(0.32, 0.86, neb), 2.0);
  float fine = fbm(d * 7.0 - 2.0);
  col += (vec3(0.16, 0.075, 0.04) * neb + vec3(0.02, 0.035, 0.07) * fine) * (0.25 + band) * 0.42;

  return col * uStarGain;
}

// ----------------------------------------------------------------- disk ----

float diskNoise(float a, float r) {
  vec2 c = vec2(cos(a), sin(a));
  float broad = fbm(vec3(c * 1.25, r * 0.85));
  float streak = fbm(vec3(c * 2.6 + 9.0, r * 3.4));
  float fine = vnoise(vec3(c * 7.0, r * 9.0));
  return broad * 0.45 + streak * 0.4 + fine * 0.15;
}

vec4 sampleDisk(vec3 hp, vec3 rayDir) {
  float r = length(hp.xz);
  float x = (r - R_IN) / (R_OUT - R_IN);
  if (x <= 0.0 || x >= 1.0) return vec4(0.0);

  // Keplerian shear: inner gas laps the outer gas. Two phase-shifted samples
  // are cross-faded so the pattern can wind forever without tearing.
  float ang = atan(hp.z, hp.x);
  float omega = pow(R_IN / r, 1.5);
  float cyc = uTime * uDiskSpeed;
  float p1 = fract(cyc);
  float p2 = fract(cyc + 0.5);
  float w = abs(1.0 - 2.0 * p1);
  float n1 = diskNoise(ang - omega * (p1 - 0.5) * 10.0, r);
  float n2 = diskNoise(ang - omega * (p2 - 0.5) * 10.0 + 2.4, r);
  float n = mix(n1, n2, w);

  float streak = smoothstep(0.26, 0.72, n);
  float temp = pow(R_IN / r, 1.25);

  float fadeIn = smoothstep(0.0, 0.045, x);
  float fadeOut = 1.0 - smoothstep(0.3, 1.0, x);
  float alpha = fadeIn * fadeOut * (0.4 + 0.6 * streak);

  vec3 cool = vec3(0.86, 0.13, 0.02);
  vec3 warm = vec3(1.0, 0.42, 0.09);
  vec3 hot = vec3(1.0, 0.84, 0.64);
  vec3 col = mix(cool, warm, smoothstep(0.06, 0.42, temp));
  col = mix(col, hot, smoothstep(0.4, 1.0, temp));

  // Relativistic beaming: the side rotating toward the camera is brighter and
  // bluer, the receding side dimmer and redder.
  vec3 tang = vec3(-hp.z, 0.0, hp.x) / r;
  float beta = sqrt(0.5 / r);
  float dop = sqrt(1.0 - beta * beta) / (1.0 - beta * dot(tang, -normalize(rayDir)));
  col = mix(col, col * vec3(0.8, 0.98, 1.45), clamp((dop - 1.0) * 1.3, 0.0, 1.0));
  col = mix(col, col * vec3(1.15, 0.66, 0.4), clamp((1.0 - dop) * 1.6, 0.0, 1.0));

  float redshift = sqrt(max(1.0 - 1.0 / r, 0.0));
  float bright = temp * temp * (0.16 + 2.6 * streak * streak) * dop * dop * redshift;

  return vec4(col * bright * uDiskGain, alpha);
}

// ----------------------------------------------------------------- main ----

void main() {
  vec4 nearPoint = uProjInv * vec4(vNdc, -1.0, 1.0);
  vec3 rd = normalize(mat3(uCamWorld) * normalize(nearPoint.xyz / nearPoint.w));
  vec3 p = uCamWorld[3].xyz;
  vec3 v = rd;

  vec3 hv = cross(p, v);
  float h2 = dot(hv, hv);

  vec3 col = vec3(0.0);
  float trans = 1.0;
  bool captured = false;

  for (int i = 0; i < MAX_STEPS; i++) {
    if (i >= uSteps) break;

    float r2 = dot(p, p);
    float r = sqrt(r2);

    if (r < 1.0) {
      captured = true;
      break;
    }
    if (r > R_ESCAPE && dot(p, v) > 0.0) break;

    float dt = 0.075 * r + 0.012;
    v += -1.5 * h2 * p / (r2 * r2 * r) * dt;
    vec3 np = p + v * dt;

    // Soft glow hugging the disk plane.
    float haze = exp(-abs(p.y) * 1.9) * smoothstep(R_OUT + 3.0, R_IN, r) * smoothstep(1.6, R_IN, r);
    col += trans * vec3(1.0, 0.42, 0.14) * haze * dt * 0.022 * uDiskGain;

    if (p.y * np.y < 0.0) {
      float t = p.y / (p.y - np.y);
      vec4 d = sampleDisk(mix(p, np, t), v);
      col += trans * d.rgb * d.a;
      trans *= 1.0 - d.a;
      if (trans < 0.01) break;
    }

    p = np;
  }

  if (!captured) col += trans * background(normalize(v));

  gl_FragColor = vec4(col, 1.0);

  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}

/*
 * Offline path tracer for the voxel pagoda scene.
 *
 *   gcc -O3 -march=native -ffast-math -pthread -o pt pathtracer.c -lm
 *   ./pt scene=scene.bin out=frame.f32 w=3840 h=2160 spp=256
 *
 * Reads the grid written by export.js and writes linear HDR float32 RGB (tonemap.py
 * turns that into a PNG). Unidirectional path tracing with next-event estimation on a
 * disc sun, a gradient sky dome, diffuse inter-reflection, thin-leaf transmission,
 * Fresnel water and a touch of aerial perspective. Rays leap through empty space using
 * the distances stored in the air voxels.
 *
 * index.html carries a GLSL port of the same integrator; keep the two in step.
 */
#define _GNU_SOURCE
#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct { float x, y, z; } v3;
static inline v3 V3(float x, float y, float z) { v3 r = {x, y, z}; return r; }
static inline v3 add(v3 a, v3 b) { return V3(a.x + b.x, a.y + b.y, a.z + b.z); }
static inline v3 sub(v3 a, v3 b) { return V3(a.x - b.x, a.y - b.y, a.z - b.z); }
static inline v3 mul(v3 a, float s) { return V3(a.x * s, a.y * s, a.z * s); }
static inline v3 mulv(v3 a, v3 b) { return V3(a.x * b.x, a.y * b.y, a.z * b.z); }
static inline float dot(v3 a, v3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
static inline v3 cross(v3 a, v3 b) { return V3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x); }
static inline v3 norm(v3 a) { return mul(a, 1.0f / sqrtf(dot(a, a))); }
static inline v3 mix3(v3 a, v3 b, float t) { return add(mul(a, 1 - t), mul(b, t)); }
static inline float clampf(float v, float a, float b) { return v < a ? a : v > b ? b : v; }
static inline float smoothstepf(float a, float b, float x) { float t = clampf((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }

enum { K_DIFF = 0, K_WATER = 1, K_METAL = 2, K_EMIT = 3, K_LEAF = 4 };
typedef struct { v3 rgb; int kind; float vary; } Mat;

static int NX, NY, NZ, NPAL;
static uint8_t *VOX;
static Mat PAL[256];

/* scene and look parameters (all overridable from the command line) */
static v3 EYE, TARGET, SUN;
static float FOV = 26;
static float SUN_RADIUS = 0.035f;                 /* angular radius of the sun disc, radians */
static v3 SUN_E = {3.30f, 3.05f, 2.60f};          /* radiance of a white surface facing the sun */
static float SKY_I = 1.0f;
static float FOG_START = 300, FOG_DENSITY = 0.00042f;
static float BEVEL = 0.10f, BEVEL_W = 0.085f;
static float LEAF_T = 0.28f;
static float ALBEDO = 0.92f;
static int MAXB = 5;

static inline uint32_t pcg(uint32_t *s) {
    uint32_t x = *s; *s = x * 747796405u + 2891336453u;
    uint32_t w = ((x >> ((x >> 28) + 4)) ^ x) * 277803737u;
    return (w >> 22) ^ w;
}
static inline float rnd(uint32_t *s) { return (pcg(s) >> 8) * (1.0f / 16777216.0f); }
static inline uint32_t hash3i(int x, int y, int z) {
    uint32_t h = (uint32_t)x * 0x27d4eb2du ^ (uint32_t)y * 0x165667b1u ^ (uint32_t)z * 0x9e3779b1u;
    h ^= h >> 15; h *= 0x85ebca6bu; h ^= h >> 13; h *= 0xc2b2ae35u; h ^= h >> 16;
    return h;
}

typedef struct { float t; int ax, sgn; int v[3]; int mat; } Hit;

/* Walk the grid. Air voxels hold k = chessboard distance to the nearest solid minus one,
 * so the ray may jump straight to the far side of the (2k+1)^3 box around its voxel. */
static int trace(v3 o, v3 d, float tmax, int skipFirst, Hit *h) {
    float od[3] = {o.x, o.y, o.z}, dd[3] = {d.x, d.y, d.z}, inv[3];
    int st[3];
    const int N[3] = {NX, NY, NZ};
    float t0 = 0, t1 = tmax;
    int ax = -1;
    for (int a = 0; a < 3; a++) {
        if (fabsf(dd[a]) < 1e-7f) dd[a] = dd[a] < 0 ? -1e-7f : 1e-7f;
        inv[a] = 1.0f / dd[a];
        st[a] = dd[a] > 0 ? 1 : -1;
        float ta = (0 - od[a]) * inv[a], tb = ((float)N[a] - od[a]) * inv[a];
        if (ta > tb) { float s = ta; ta = tb; tb = s; }
        if (ta > t0) { t0 = ta; ax = a; }
        if (tb < t1) t1 = tb;
    }
    if (t0 >= t1) return 0;
    float t = t0;
    int v[3];
    for (int a = 0; a < 3; a++) {
        int q = (int)floorf(od[a] + dd[a] * t);
        v[a] = q < 0 ? 0 : q >= N[a] ? N[a] - 1 : q;
    }
    if (ax >= 0) v[ax] = st[ax] > 0 ? 0 : N[ax] - 1;
    for (int it = 0; it < 2048; it++) {
        uint8_t val = VOX[v[0] + NX * (v[2] + NZ * v[1])];
        int k;
        if (val >= 32) {
            if (!(skipFirst && it == 0)) {
                h->t = t; h->ax = ax; h->sgn = ax >= 0 ? -st[ax] : 0;
                h->v[0] = v[0]; h->v[1] = v[1]; h->v[2] = v[2]; h->mat = val - 31;
                return 1;
            }
            k = 0;
        } else k = val;
        float tx = ((float)(st[0] > 0 ? v[0] + k + 1 : v[0] - k) - od[0]) * inv[0];
        float ty = ((float)(st[1] > 0 ? v[1] + k + 1 : v[1] - k) - od[1]) * inv[1];
        float tz = ((float)(st[2] > 0 ? v[2] + k + 1 : v[2] - k) - od[2]) * inv[2];
        if (tx < ty) { if (tx < tz) { ax = 0; t = tx; } else { ax = 2; t = tz; } }
        else { if (ty < tz) { ax = 1; t = ty; } else { ax = 2; t = tz; } }
        if (t >= t1) return 0;
        if (k == 0) v[ax] += st[ax];
        else {
            for (int b = 0; b < 3; b++) {
                if (b == ax) continue;
                int q = (int)floorf(od[b] + dd[b] * t);
                int lo = v[b] - k, hi = v[b] + k;
                q = q < lo ? lo : q > hi ? hi : q;
                if ((unsigned)q >= (unsigned)N[b]) return 0;
                v[b] = q;
            }
            v[ax] += (k + 1) * st[ax];
        }
        if ((unsigned)v[ax] >= (unsigned)N[ax]) return 0;
    }
    return 0;
}

static inline v3 sky_view(v3 d) {
    /* What the camera sees: clear blue overhead, paling into haze toward and below the horizon. */
    float s = smoothstepf(-0.30f, 0.06f, d.y);
    v3 c = mix3(V3(0.60f, 0.79f, 1.00f), V3(0.115f, 0.33f, 0.86f), s);
    return mul(c, SKY_I);
}
static inline v3 sky_light(v3 d) {
    /* What lights the scene: a softer dome so open shade stays cool but not inky blue. */
    float s = smoothstepf(-0.12f, 0.75f, d.y);
    v3 c = mix3(V3(0.74f, 0.86f, 1.00f), V3(0.30f, 0.52f, 1.00f), s);
    float sd = dot(d, SUN);
    if (sd > 0) { float g = sd * sd; g *= g; g *= g; g *= g; c = add(c, mul(V3(1.0f, 0.86f, 0.62f), 0.35f * g)); }
    if (d.y < 0) c = mix3(c, V3(0.52f, 0.60f, 0.52f), clampf(-d.y * 3.0f, 0, 1));    /* light bounced up off the land beyond */
    return mul(c, SKY_I);
}

static inline void basis(v3 n, v3 *t, v3 *b) {
    float s = n.z >= 0 ? 1.0f : -1.0f, a = -1.0f / (s + n.z), c = n.x * n.y * a;
    *t = V3(1 + s * n.x * n.x * a, s * c, -s * n.x);
    *b = V3(c, s + n.y * n.y * a, -n.y);
}
static inline v3 cosine_dir(v3 n, uint32_t *rs) {
    float u1 = rnd(rs), u2 = rnd(rs), r = sqrtf(u1), ph = 6.2831853f * u2;
    v3 t, b; basis(n, &t, &b);
    return norm(add(add(mul(t, r * cosf(ph)), mul(b, r * sinf(ph))), mul(n, sqrtf(1 - u1))));
}
static inline v3 sun_dir(uint32_t *rs) {
    float u1 = rnd(rs), u2 = rnd(rs), r = SUN_RADIUS * sqrtf(u1), ph = 6.2831853f * u2;
    v3 t, b; basis(SUN, &t, &b);
    return norm(add(SUN, add(mul(t, r * cosf(ph)), mul(b, r * sinf(ph)))));
}

typedef struct { v3 albedo, normal; float depth; } Aov;

static v3 radiance(v3 o, v3 d, uint32_t *rs, Aov *aov) {
    v3 L = {0, 0, 0}, T = {1, 1, 1};
    float fog = 0;
    int skip = 0, specular = 1;
    for (int bounce = 0; bounce < MAXB; bounce++) {
        Hit h;
        if (!trace(o, d, 1e9f, skip, &h)) {
            L = add(L, mulv(T, specular ? sky_view(d) : sky_light(d)));
            if (bounce == 0) { aov->albedo = sky_view(d); aov->normal = V3(0, 0, 0); aov->depth = 1e5f; }
            break;
        }
        skip = 0;
        v3 p = add(o, mul(d, h.t));
        v3 n = V3(0, 0, 0);
        if (h.ax == 0) n.x = (float)h.sgn; else if (h.ax == 1) n.y = (float)h.sgn; else if (h.ax == 2) n.z = (float)h.sgn;
        else break;                                    /* started inside a solid: give up */
        const Mat *m = &PAL[h.mat];

        /* per-voxel tint and a faint groove at the edge of every face, so each cube reads */
        uint32_t hv = hash3i(h.v[0], h.v[1], h.v[2]);
        float f = 1.0f + m->vary * (((hv & 0xffff) / 32767.5f) - 1.0f);
        float pc[3] = {p.x - h.v[0], p.y - h.v[1], p.z - h.v[2]};
        float a = pc[(h.ax + 1) % 3], b = pc[(h.ax + 2) % 3];
        float e = fminf(fminf(a, 1 - a), fminf(b, 1 - b));
        f *= 1.0f - BEVEL * (1.0f - smoothstepf(0.0f, BEVEL_W, e));
        v3 alb = mul(m->rgb, f * ALBEDO);

        if (bounce == 0) {
            aov->albedo = alb; aov->normal = n; aov->depth = h.t;
            fog = 1.0f - expf(-fmaxf(0.0f, h.t - FOG_START) * FOG_DENSITY);
        }
        if (m->kind == K_EMIT) { L = add(L, mulv(T, mul(m->rgb, 3.5f))); break; }
        if (m->kind == K_WATER) {
            float c = fmaxf(0.0f, -dot(d, n)), fr = 0.04f + 0.96f * powf(1 - c, 5);
            if (rnd(rs) < fr + 0.10f) {                /* mirror the sky and the garden */
                v3 r = sub(d, mul(n, 2 * dot(d, n)));
                r = norm(add(r, mul(V3(rnd(rs) - 0.5f, 0, rnd(rs) - 0.5f), 0.03f)));
                o = add(p, mul(n, 1e-3f)); d = r; specular = 1;
                T = mulv(T, V3(0.92f, 0.96f, 0.98f));
                continue;
            }
        } else if (m->kind == K_METAL) {
            if (rnd(rs) < 0.55f) {
                v3 r = sub(d, mul(n, 2 * dot(d, n)));
                r = norm(add(r, mul(V3(rnd(rs) - 0.5f, rnd(rs) - 0.5f, rnd(rs) - 0.5f), 0.55f)));
                if (dot(r, n) > 0.01f) { o = add(p, mul(n, 1e-3f)); d = r; specular = 0; T = mulv(T, mul(m->rgb, 1.05f)); continue; }
            }
        }
        specular = 0;
        float tr = m->kind == K_LEAF ? LEAF_T : 0.0f;

        /* direct sunlight */
        v3 l = sun_dir(rs);
        float nl = dot(n, l);
        Hit sh;
        if (nl > 0) {
            if (!trace(add(p, mul(n, 1e-3f)), l, 1e9f, 0, &sh)) L = add(L, mulv(T, mulv(alb, mul(SUN_E, nl * (1 - tr)))));
        } else if (tr > 0) {                           /* sun shining through a leaf from behind */
            if (!trace(sub(p, mul(n, 1e-3f)), l, 1e9f, 1, &sh)) L = add(L, mulv(T, mulv(alb, mul(SUN_E, -nl * tr))));
        }

        /* continue the path */
        if (tr > 0 && rnd(rs) < tr) { d = cosine_dir(mul(n, -1), rs); o = sub(p, mul(n, 1e-3f)); skip = 1; }
        else { d = cosine_dir(n, rs); o = add(p, mul(n, 1e-3f)); }
        T = mulv(T, alb);
        if (bounce >= 2) {
            float q = fmaxf(T.x, fmaxf(T.y, T.z));
            if (q < 1.0f) { if (rnd(rs) > q) break; T = mul(T, 1.0f / q); }
        }
    }
    /* clamp fireflies, then lay the haze over the result */
    float mx = fmaxf(L.x, fmaxf(L.y, L.z));
    if (mx > 24.0f) L = mul(L, 24.0f / mx);
    if (fog > 0) L = mix3(L, mul(V3(0.62f, 0.80f, 1.00f), SKY_I), fog);
    return L;
}

/* ------------------------------------------------------------------ driver */
static int W = 960, H = 540, SPP = 16, PASS = 4, THREADS = 0, WANT_AOV = 0, SEED = 0;
static float *ACC, *AOVB;
static v3 CR, CU, CF;
static float TANH;
static atomic_int next_row;
static int pass_index, pass_spp;

static void *worker(void *arg) {
    (void)arg;
    for (;;) {
        int y = atomic_fetch_add(&next_row, 1);
        if (y >= H) break;
        for (int x = 0; x < W; x++) {
            uint32_t rs = hash3i(x, y, pass_index * 7919 + 13 + SEED * 104729) | 1u;
            v3 sum = {0, 0, 0};
            Aov as = {{0, 0, 0}, {0, 0, 0}, 0};
            for (int s = 0; s < pass_spp; s++) {
                /* gaussian pixel filter by importance sampling */
                float u1 = fmaxf(rnd(&rs), 1e-6f), u2 = rnd(&rs);
                float rr = 0.45f * sqrtf(-2.0f * logf(u1));
                if (rr > 1.5f) rr = 1.5f;
                float jx = rr * cosf(6.2831853f * u2), jy = rr * sinf(6.2831853f * u2);
                float sx = ((x + 0.5f + jx) / W * 2 - 1) * TANH * W / H;
                float sy = (1 - (y + 0.5f + jy) / H * 2) * TANH;
                v3 d = norm(add(CF, add(mul(CR, sx), mul(CU, sy))));
                Aov a;
                v3 c = radiance(EYE, d, &rs, &a);
                sum = add(sum, c);
                as.albedo = add(as.albedo, a.albedo); as.normal = add(as.normal, a.normal); as.depth += a.depth;
            }
            float *p = ACC + 3 * (y * W + x);
            p[0] += sum.x; p[1] += sum.y; p[2] += sum.z;
            if (AOVB) {
                float *q = AOVB + 7 * (y * W + x);
                q[0] += as.albedo.x; q[1] += as.albedo.y; q[2] += as.albedo.z;
                q[3] += as.normal.x; q[4] += as.normal.y; q[5] += as.normal.z; q[6] += as.depth;
            }
        }
    }
    return NULL;
}

static float srgb2lin(float c) { return c <= 0.04045f ? c / 12.92f : powf((c + 0.055f) / 1.055f, 2.4f); }
static int parse3(const char *s, v3 *v) { return sscanf(s, "%f,%f,%f", &v->x, &v->y, &v->z) == 3; }
static double now(void) { struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts); return ts.tv_sec + ts.tv_nsec * 1e-9; }

static void write_scaled(const char *path, const float *buf, size_t n, float scale) {
    char tmp[1024]; snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "wb");
    if (!f) { perror(tmp); exit(1); }
    float *row = malloc(sizeof(float) * 65536);
    for (size_t i = 0; i < n;) {
        size_t c = n - i < 65536 ? n - i : 65536;
        for (size_t j = 0; j < c; j++) row[j] = buf[i + j] * scale;
        fwrite(row, sizeof(float), c, f);
        i += c;
    }
    free(row); fclose(f); rename(tmp, path);
}

int main(int argc, char **argv) {
    const char *scene = "scene.bin", *out = "frame.f32";
    v3 eye_o, tgt_o, sun_o; int has_eye = 0, has_tgt = 0, has_sun = 0; float fov_o = 0;
    for (int i = 1; i < argc; i++) {
        char *eq = strchr(argv[i], '=');
        if (!eq) { fprintf(stderr, "expected key=value, got %s\n", argv[i]); return 1; }
        *eq = 0; const char *k = argv[i], *v = eq + 1;
        if (!strcmp(k, "scene")) scene = v; else if (!strcmp(k, "out")) out = v;
        else if (!strcmp(k, "w")) W = atoi(v); else if (!strcmp(k, "h")) H = atoi(v);
        else if (!strcmp(k, "spp")) SPP = atoi(v); else if (!strcmp(k, "pass")) PASS = atoi(v);
        else if (!strcmp(k, "threads")) THREADS = atoi(v); else if (!strcmp(k, "bounces")) MAXB = atoi(v);
        else if (!strcmp(k, "aov")) WANT_AOV = atoi(v); else if (!strcmp(k, "seed")) SEED = atoi(v);
        else if (!strcmp(k, "eye")) has_eye = parse3(v, &eye_o); else if (!strcmp(k, "target")) has_tgt = parse3(v, &tgt_o);
        else if (!strcmp(k, "sun")) has_sun = parse3(v, &sun_o); else if (!strcmp(k, "fov")) fov_o = atof(v);
        else if (!strcmp(k, "sunr")) SUN_RADIUS = atof(v); else if (!strcmp(k, "sune")) parse3(v, &SUN_E);
        else if (!strcmp(k, "sky")) SKY_I = atof(v); else if (!strcmp(k, "fogstart")) FOG_START = atof(v);
        else if (!strcmp(k, "fog")) FOG_DENSITY = atof(v); else if (!strcmp(k, "bevel")) BEVEL = atof(v);
        else if (!strcmp(k, "bevelw")) BEVEL_W = atof(v); else if (!strcmp(k, "leaf")) LEAF_T = atof(v);
        else { fprintf(stderr, "unknown option %s\n", k); return 1; }
    }
    FILE *f = fopen(scene, "rb");
    if (!f) { perror(scene); return 1; }
    char magic[4]; int32_t hd[4]; float cam[10];
    if (fread(magic, 1, 4, f) != 4 || memcmp(magic, "VXP1", 4) || fread(hd, 4, 4, f) != 4 || fread(cam, 4, 10, f) != 10) { fprintf(stderr, "bad scene file\n"); return 1; }
    NX = hd[0]; NY = hd[1]; NZ = hd[2]; NPAL = hd[3];
    EYE = V3(cam[0], cam[1], cam[2]); TARGET = V3(cam[3], cam[4], cam[5]); FOV = cam[6]; SUN = V3(cam[7], cam[8], cam[9]);
    for (int i = 0; i < NPAL; i++) {
        uint8_t c[4]; float vary;
        if (fread(c, 1, 4, f) != 4 || fread(&vary, 4, 1, f) != 1) return 1;
        PAL[i + 1].rgb = V3(srgb2lin(c[0] / 255.0f), srgb2lin(c[1] / 255.0f), srgb2lin(c[2] / 255.0f));
        PAL[i + 1].kind = c[3]; PAL[i + 1].vary = vary;
    }
    size_t nv = (size_t)NX * NY * NZ;
    VOX = malloc(nv);
    if (fread(VOX, 1, nv, f) != nv) { fprintf(stderr, "short voxel data\n"); return 1; }
    fclose(f);
    if (has_eye) EYE = eye_o;
    if (has_tgt) TARGET = tgt_o;
    if (has_sun) SUN = sun_o;
    if (fov_o > 0) FOV = fov_o;
    SUN = norm(SUN);
    CF = norm(sub(TARGET, EYE)); CR = norm(cross(CF, V3(0, 1, 0))); CU = cross(CR, CF);
    TANH = tanf(FOV * 0.5f * 3.14159265f / 180.0f);

    if (THREADS <= 0) THREADS = 4;
    ACC = calloc((size_t)W * H * 3, sizeof(float));
    if (WANT_AOV) AOVB = calloc((size_t)W * H * 7, sizeof(float));
    pthread_t th[64];
    double t0 = now();
    int done = 0;
    for (pass_index = 0; done < SPP; pass_index++) {
        pass_spp = SPP - done < PASS ? SPP - done : PASS;
        atomic_store(&next_row, 0);
        for (int i = 0; i < THREADS; i++) pthread_create(&th[i], NULL, worker, NULL);
        for (int i = 0; i < THREADS; i++) pthread_join(th[i], NULL);
        done += pass_spp;
        write_scaled(out, ACC, (size_t)W * H * 3, 1.0f / done);
        if (AOVB) { char p[1024]; snprintf(p, sizeof p, "%s.aov", out); write_scaled(p, AOVB, (size_t)W * H * 7, 1.0f / done); }
        fprintf(stderr, "\r%d/%d spp  %.1fs", done, SPP, now() - t0);
    }
    fprintf(stderr, "\n");
    return 0;
}

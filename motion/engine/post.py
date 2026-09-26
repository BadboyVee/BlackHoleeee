"""Per-frame image effects on float32 RGB arrays: bloom, chroma, glitch, grain, vignette."""
import cv2
import numpy as np


class Post:
    def __init__(self, w, h, seed=11):
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (xx - w / 2) / (w / 2)
        ny = (yy - h / 2) / (h / 2)
        self.r2 = (nx * nx * 0.9 + ny * ny * 1.1).astype(np.float32)
        rng = np.random.default_rng(seed)
        self.grain = []
        for _ in range(8):
            g = rng.standard_normal((h, w)).astype(np.float32)
            g = cv2.GaussianBlur(g, (0, 0), 0.85)
            g /= g.std() + 1e-6
            self.grain.append(g)

    # ------------------------------------------------------------ effects

    def _bright(self, img, threshold):
        small = cv2.resize(img, (self.w // 4, self.h // 4), interpolation=cv2.INTER_AREA)
        lum = small.max(axis=2, keepdims=True)
        return small * np.clip((lum - threshold) / (1.0 - threshold + 1e-6), 0.0, 1.0)

    def bloom(self, img, amount, threshold=0.62, radius=1.0, tint=None):
        """Two-scale glow. A warm tint turns it into film halation."""
        b = self._bright(img, threshold)
        s = max(radius, 0.1)
        b1 = cv2.GaussianBlur(b, (0, 0), 3.0 * s)
        b2 = cv2.GaussianBlur(b, (0, 0), 12.0 * s)
        glow = cv2.resize(b1 * 0.55 + b2 * 0.65, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        if tint is not None:
            glow = glow * np.asarray(tint, np.float32)
        return img + glow * amount

    def streaks(self, img, amount, threshold=0.7, length=1.0, tint=(0.55, 0.75, 1.0)):
        """Anamorphic lens streaks: bright points smeared into long horizontal flares."""
        lum = np.ascontiguousarray(self._bright(img, threshold).mean(axis=2))
        sx = 40.0 * length * self.w / 1920
        st = cv2.GaussianBlur(lum, (0, 0), sigmaX=sx, sigmaY=0.6)
        st = cv2.resize(st, (self.w, self.h), interpolation=cv2.INTER_LINEAR)[..., None]
        return img + st * np.asarray(tint, np.float32) * (amount * 6.0)

    def zoom_blur(self, img, amount, cx=0.5, cy=0.5, samples=10):
        """Radial blur toward a centre, like CC Radial Fast Blur on a zoom."""
        w, h = self.w, self.h
        acc = np.zeros_like(img)
        px, py = cx * w, cy * h
        for i in range(samples):
            s = 1.0 + amount * i / (samples - 1)
            M = np.float32([[s, 0, (1 - s) * px], [0, s, (1 - s) * py]])
            acc += cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return acc / samples

    def chroma(self, img, px):
        """Lateral chromatic aberration: red scaled out, blue scaled in, px at the frame edge."""
        w, h = self.w, self.h
        out = img.copy()
        for ch, sgn in ((0, 1.0), (2, -1.0)):
            s = 1.0 + sgn * px / (w / 2)
            M = np.float32([[s, 0, (1 - s) * w / 2], [0, s, (1 - s) * h / 2]])
            out[..., ch] = cv2.warpAffine(np.ascontiguousarray(img[..., ch]), M, (w, h),
                                          flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return out

    def glitch(self, img, amount, seed):
        rng = np.random.default_rng(seed)
        out = img.copy()
        h, w = self.h, self.w
        for _ in range(int(3 + amount * 16)):
            y0 = int(rng.integers(0, h))
            hh = int(rng.integers(2, max(3, int(8 + 110 * amount))))
            dx = int(rng.normal(0, 70 * amount * w / 1920))
            band = out[y0:y0 + hh]
            band[:] = np.roll(band, dx, axis=1)
            if rng.random() < 0.5:
                band[..., 0] = np.roll(band[..., 0], int(12 * amount * w / 1920), axis=1)
        return out

    def run(self, img, frame, fx):
        if not fx:
            fx = {}
        if fx.get("chroma", 0) > 0.05:
            img = self.chroma(img, fx["chroma"] * self.w / 1920)
        if fx.get("blur", 0) > 0.3:
            img = cv2.GaussianBlur(img, (0, 0), fx["blur"] * self.w / 1920)
        if fx.get("glitch", 0) > 0.01:
            img = self.glitch(img, fx["glitch"], fx.get("glitch_seed", frame))
        if fx.get("zoom_blur", 0) > 0.002:
            img = self.zoom_blur(img, fx["zoom_blur"], *fx.get("zoom_center", (0.5, 0.5)))
        if fx.get("bloom", 0) > 0:
            img = self.bloom(img, fx["bloom"], fx.get("bloom_th", 0.62), fx.get("bloom_r", 1.0) * self.w / 1920,
                             fx.get("bloom_tint"))
        if fx.get("streaks", 0) > 0:
            img = self.streaks(img, fx["streaks"], fx.get("streak_th", 0.7), fx.get("streak_len", 1.0),
                               fx.get("streak_tint", (0.55, 0.75, 1.0)))
        if fx.get("flash", 0) > 0:
            a = min(1.0, fx["flash"])
            col = np.asarray(fx.get("flash_color", (1.0, 1.0, 1.0)), np.float32)
            img = img * (1 - a) + col * a
        if fx.get("exposure", 1.0) != 1.0:
            img = img * fx["exposure"]
        v = fx.get("vignette", 0.22)
        if v > 0:
            img = img * (1.0 - v * np.clip(self.r2 * 0.55, 0, 1.2))[..., None]
        g = fx.get("grain", 0.028)
        if g > 0:
            n = self.grain[frame % len(self.grain)]
            n = np.roll(n, ((frame * 373) % self.h, (frame * 617) % self.w), axis=(0, 1))
            lum = img.mean(axis=2)
            img = img + (g * n * (0.45 + 2.2 * lum * (1.0 - np.clip(lum, 0, 1))))[..., None]
        return img

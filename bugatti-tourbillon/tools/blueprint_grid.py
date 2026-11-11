"""Draw metric car-coordinate grids over the blueprint views (for reading off coordinates).
Car coords: +X forward, +Y left, +Z up, origin on ground at mid-wheelbase. Uses blueprint_profiles.json."""
import json, sys
import numpy as np, cv2
from PIL import Image
SRC = "/root/.claude/uploads/d8c69794-a7de-5046-84fd-f7d20a1fbe4a/2bb588bc-image.jpg"
R = json.load(open("refs/derived/blueprint_profiles.json"))
A = Image.open(SRC).convert("RGB")
U = 8  # output upscale relative to original image

def view(name, kind):
    info = R[name]['img']; box = info['box']; S = info['S']; k = U / S
    c = A.crop(box).resize(((box[2]-box[0])*U, (box[3]-box[1])*U), Image.LANCZOS)
    img = cv2.cvtColor(np.asarray(c), cv2.COLOR_RGB2BGR)
    ppm = info['ppm'] * k
    h, w = img.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    if kind == 'side':
        ox, gy = info['ox']*k, info['gy']*k
        fx = lambda X: int(round(ox + X*ppm)); fz = lambda Z: int(round(gy - Z*ppm))
        for X in np.arange(-2.4, 2.61, 0.1):
            major = abs(X*2 - round(X*2)) < 1e-6
            cv2.line(img, (fx(X), 0), (fx(X), h-1), (90, 90, 90) if major else (205, 205, 205), 1)
            if major: cv2.putText(img, "%.1f" % X, (fx(X)+3, 16), font, 0.5, (0, 120, 0), 1, cv2.LINE_AA)
        for Z in np.arange(0, 1.31, 0.1):
            major = abs(Z*2 - round(Z*2)) < 1e-6
            cv2.line(img, (0, fz(Z)), (w-1, fz(Z)), (90, 90, 90) if major else (205, 205, 205), 1)
            cv2.putText(img, "%.1f" % Z, (3, fz(Z)-3), font, 0.45, (0, 120, 0), 1, cv2.LINE_AA)
    elif kind == 'top':
        cy = info['cy']*k; xn = info['x_nose_px']*k; xfront = R['side']['x_front']
        fx = lambda X: int(round(xn + (X - xfront)*ppm)); fy = lambda Y: int(round(cy - Y*ppm))
        for X in np.arange(-2.4, 2.61, 0.1):
            major = abs(X*2 - round(X*2)) < 1e-6
            cv2.line(img, (fx(X), 0), (fx(X), h-1), (90, 90, 90) if major else (205, 205, 205), 1)
            if major: cv2.putText(img, "%.1f" % X, (fx(X)+3, 16), font, 0.5, (0, 120, 0), 1, cv2.LINE_AA)
        for Y in np.arange(-1.2, 1.21, 0.1):
            major = abs(Y*2 - round(Y*2)) < 1e-6
            cv2.line(img, (0, fy(Y)), (w-1, fy(Y)), (90, 90, 90) if major else (205, 205, 205), 1)
            cv2.putText(img, "%.1f" % Y, (3, fy(Y)-3), font, 0.45, (0, 120, 0), 1, cv2.LINE_AA)
    else:  # front / rear:  image x = lateral
        cx, gy = info['cx']*k, info['gy']*k
        fy = lambda Y: int(round(cx + Y*ppm)); fz = lambda Z: int(round(gy - Z*ppm))
        for Y in np.arange(-1.2, 1.21, 0.1):
            major = abs(Y*2 - round(Y*2)) < 1e-6
            cv2.line(img, (fy(Y), 0), (fy(Y), h-1), (90, 90, 90) if major else (205, 205, 205), 1)
            if major: cv2.putText(img, "%.1f" % Y, (fy(Y)+3, 16), font, 0.5, (0, 120, 0), 1, cv2.LINE_AA)
        for Z in np.arange(0, 1.31, 0.1):
            major = abs(Z*2 - round(Z*2)) < 1e-6
            cv2.line(img, (0, fz(Z)), (w-1, fz(Z)), (90, 90, 90) if major else (205, 205, 205), 1)
            cv2.putText(img, "%.1f" % Z, (3, fz(Z)-3), font, 0.45, (0, 120, 0), 1, cv2.LINE_AA)
    # re-draw the magenta strokes on top of the grid
    src = np.asarray(c).astype(np.int32)
    m = ((src[..., 0]-src[..., 1]) > 28) & ((src[..., 2]-src[..., 1]) > 28)
    img[m] = (200, 0, 200)
    cv2.imwrite(f"refs/derived/grid_{name}.png", img)
    print(name, img.shape)

view('side', 'side'); view('top', 'top'); view('front', 'fr'); view('rear', 'fr')

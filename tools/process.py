import sys, os, numpy as np, cv2
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from cfg import CFG
import grade as G   # reuse grade() / P presets  (grade.py guards its batch loop)

SRC = r'C:\Users\rhkal\AppData\Local\Temp\claude\C--Users-rhkal\c50d7345-d0a9-4127-98ac-6b742ef4643e\images'
OUT = r'C:\Users\rhkal\cougar-xr7\img'
DBG = r'C:\Users\rhkal\AppData\Local\Temp\claude\C--Users-rhkal\c50d7345-d0a9-4127-98ac-6b742ef4643e\scratchpad\dbg'
os.makedirs(DBG, exist_ok=True)


def poly_mask(shape, pts, s):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts, np.float64) * s).astype(np.int32)], 255)
    return m


def privacy_blur(img, regions, s, protect=None):
    """Strongly blur each region (feathered) so plates / faces / signage are unreadable."""
    out = img.astype(np.float32)
    for pts in regions:
        m = poly_mask(img.shape, pts, s)
        x, y, w, h = cv2.boundingRect(m)
        sig = max(6.0, 0.33 * min(w, h)) if min(w, h) < 120 * s else max(10.0, 0.18 * min(w, h))
        sig = min(sig, 40 * s)
        k = int(sig * 6) | 1
        pad = int(sig * 3)
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(img.shape[1], x + w + pad), min(img.shape[0], y + h + pad)
        patch = cv2.GaussianBlur(img[y0:y1, x0:x1], (k, k), sig).astype(np.float32)
        # blur twice for text so edges don't survive
        patch = cv2.GaussianBlur(patch, (k, k), sig)
        fm = cv2.GaussianBlur(m[y0:y1, x0:x1].astype(np.float32) / 255, (0, 0), max(2, sig * .25))
        if protect is not None:
            fm = fm * (1 - protect[y0:y1, x0:x1])
        fm = fm[..., None]
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - fm) + patch * fm
    return np.clip(out, 0, 255).astype(np.uint8)


def car_mask(img, pts, s, grab=True, band=0.018):
    """Hand-drawn outline -> GrabCut-refined mask (computed at <=1400px wide)."""
    H, W = img.shape[:2]
    k = min(1.0, 1400 / W)
    small = cv2.resize(img, (round(W * k), round(H * k)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    P = poly_mask(small.shape, pts, s * k)
    bw = max(5, int(sw * band))
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * bw + 1, 2 * bw + 1))
    sure_fg = cv2.erode(P, ker)
    probable = cv2.dilate(P, ker)
    m = np.full((sh, sw), cv2.GC_BGD, np.uint8)
    m[probable > 0] = cv2.GC_PR_BGD
    m[P > 0] = cv2.GC_PR_FGD
    m[sure_fg > 0] = cv2.GC_FGD
    if grab:
        bgd = np.zeros((1, 65)); fgd = np.zeros((1, 65))
        cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8) * 255
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    if n > 1:
        fg = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8) * 255
    # fill holes
    inv = 255 - fg
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n):
        x, y, w, h = st[i, :4]
        if x > 0 and y > 0 and x + w < sw and y + h < sh:
            fg[lab == i] = 255
    fg = cv2.GaussianBlur(fg, (0, 0), 1.2)
    return cv2.resize(fg, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255


def treat_background(img, alpha, bg):
    """Darken + desaturate + distance-weighted blur on everything that is not the car."""
    f = img.astype(np.float32) / 255
    a = alpha[..., None]
    w = img.shape[1]
    inv = 1 - a

    def mblur(sig):
        num = cv2.GaussianBlur(f * inv, (0, 0), sig)
        den = cv2.GaussianBlur(inv, (0, 0), sig)[..., None]
        return np.where(den > 1e-3, num / np.maximum(den, 1e-3), cv2.GaussianBlur(f, (0, 0), sig))

    s1, s2 = bg['blur'] * w * .5, bg['blur'] * w * 1.8
    b1, b2 = mblur(s1), mblur(s2)
    dist = cv2.distanceTransform((alpha < .5).astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip(dist / (0.22 * w), 0, 1)[..., None]
    t = t * t * (3 - 2 * t)
    bgi = b1 * (1 - t) + b2 * t
    lum = (bgi[..., 0] * .2126 + bgi[..., 1] * .7152 + bgi[..., 2] * .0722)[..., None]
    bgi = lum + (bgi - lum) * (1 - bg['desat'])
    bgi *= bg['dark']
    bgi = np.where(bgi < .26, bgi, .26 + (bgi - .26) * .35)   # tame bright backgrounds so nothing glows around the car
    car = np.clip(f * 1.04, 0, 1)
    return np.clip(car * a + bgi * (1 - a), 0, 1)


def run(name, review=False):
    c = CFG[name]
    img = np.array(Image.open(os.path.join(SRC, c['src'])).convert('RGB'))
    H, W = img.shape[:2]
    s = W / 1000.0
    alpha = None
    if c.get('car'):
        alpha = car_mask(img, c['car'], s, c.get('grab', True), c.get('band', 0.018))   # outline is traced on the untouched photo
    prot = None
    if alpha is not None:
        prot = cv2.dilate(alpha, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    img = privacy_blur(img, c.get('blur', []), s, protect=prot)     # signage etc: background only
    img = privacy_blur(img, c.get('plates', []), s)                  # plates / faces: everywhere
    if review and alpha is not None:
        ov = img.copy().astype(np.float32)
        ov[..., 0] = ov[..., 0] * (1 - .45 * alpha) + 255 * .45 * alpha
        cv2.polylines(ov, [np.round(np.array(c['car']) * s).astype(np.int32)], True, (0, 255, 255), max(1, int(s)))
        v = Image.fromarray(np.clip(ov, 0, 255).astype(np.uint8)); v.thumbnail((1100, 1100))
        v.save(os.path.join(DBG, name + '_mask.jpg'), quality=85)
    if c.get('crop'):
        x0, y0, x1, y1 = [int(round(v * s)) for v in c['crop']]
        x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(W, x1), min(H, y1)
        img = img[y0:y1, x0:x1]
        alpha = alpha[y0:y1, x0:x1] if alpha is not None else None
    h, w = img.shape[:2]
    tw = 2200 if w > 2000 else (1280 if h > w else 1600)
    th = round(h * tw / w)
    img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_LANCZOS4 if tw > w else cv2.INTER_AREA)
    if alpha is not None:
        alpha = np.clip(cv2.resize(alpha, (tw, th), interpolation=cv2.INTER_LINEAR), 0, 1)
        out = treat_background(img, alpha, c['bg'])
        img = (out * 255).astype(np.uint8)
    g = G.grade(Image.fromarray(img), G.P[c['preset']]).filter(ImageFilter.UnsharpMask(1.0, 45, 3))
    g.save(os.path.join(OUT, name + '.jpg'), quality=84, optimize=True, progressive=True)
    t = g.copy(); t.thumbnail((900, 900))
    t.save(os.path.join(OUT, name + '-sm.jpg'), quality=80, optimize=True, progressive=True)
    return g


if __name__ == '__main__':
    names = [n for n in sys.argv[1:] if not n.startswith('-')] or list(CFG)
    for n in names:
        run(n, review=True)
        print('done', n)

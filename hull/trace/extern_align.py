# An external model (PCA-aligned triangles) given its proper orientation: small rotations about the three axes searched so
# its orthographic silhouettes from above, the side and behind best match our confirmed views (mean IoU of the three),
# using vertex splats on a reduced grid; then centred, scaled to a given length and written with the rotation used.
# Usage: python extern_align.py <in.npz> <layout.json> <vederi.json> <views.json> <length_m> <out.npz>
import sys, json, numpy as np, cv2
IN, LJ, VJ, SJ, LEN, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6]
z = np.load(IN); key = [k for k in z.files if k.startswith("v|")][0]; V0 = z[key].astype(float); T = z["t" + key[1:]]
LAY = json.load(open(LJ)); SP = json.load(open(SJ)); Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
def sil(spec, key):
    if "faces" in spec:
        F = json.load(open(spec["faces"])); m = np.zeros(spec.get("size", [860, 3260]), np.uint8)
        for t in F:
            for f in F[t]:
                cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
                for h in f.get("holes", []): cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
    elif "zone" in spec:
        zz = np.load(spec["zone"]); nm = json.load(open(spec["names"])); g = [int(k) for k, t in nm.items() if t.startswith("G")]; m = ((zz > 0) & ~np.isin(zz, g)).astype(np.uint8)
    else: zz = np.load(spec["npz"]); m = np.any([zz[t] for t in zz.files], 0).astype(np.uint8)
    m = cv2.warpAffine(m, AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST); ys, xs = np.nonzero(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; return cv2.resize(m, (200, int(200 * m.shape[0] / m.shape[1])), interpolation=cv2.INTER_AREA) > 0
REF = {k: sil(SP[k], k) for k in ("top", "side", "back")}
# model axes after PCA: 0 length, 1 width, 2 height; canvas axes per view (as in extern_compare: flips found there)
AX = {"top": (1, 0), "side": (2, 0), "back": (1, 2)}; FL = {"top": (True, True), "side": (True, True), "back": (False, False)}
P = V0[np.random.default_rng(0).choice(len(V0), min(len(V0), 120000), replace=False)]
def R(a, b, c):
    ca, sa, cb, sb, cc, sc = np.cos(a), np.sin(a), np.cos(b), np.sin(b), np.cos(c), np.sin(c)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]]); Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]]); Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
def score(rot):
    Q = P @ rot.T; s = 0
    for k, ref in REF.items():
        u = Q[:, AX[k][0]] * (-1 if FL[k][0] else 1); v = Q[:, AX[k][1]] * (-1 if FL[k][1] else 1)
        H, W = ref.shape; iu = ((u - u.min()) / np.ptp(u) * (W - 1)).astype(int); iv = ((v - v.min()) / np.ptp(v) * (H - 1)).astype(int)
        m = np.zeros((H, W), np.uint8); m[iv, iu] = 1; m = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
        s += (m & ref).sum() / max((m | ref).sum(), 1)
    return s / len(REF)
best = (score(np.eye(3)), 0, 0, 0); print("start %.3f" % best[0])
for step in (np.radians(8), np.radians(3), np.radians(1)):
    improved = True
    while improved:
        improved = False
        for d in [(step, 0, 0), (-step, 0, 0), (0, step, 0), (0, -step, 0), (0, 0, step), (0, 0, -step)]:
            a, b, c = best[1] + d[0], best[2] + d[1], best[3] + d[2]; v = score(R(a, b, c))
            if v > best[0] + 1e-4: best = (v, a, b, c); improved = True
print("best %.3f rot deg %s" % (best[0], np.degrees(best[1:]).round(1)))
rot = R(*best[1:]); V = V0 @ rot.T; V -= (V.min(0) + V.max(0)) / 2; V *= LEN / np.ptp(V[:, 0])
np.savez_compressed(OUT, **{"v|nava": V.astype(np.float32), "t|nava": T, "rot": rot}); print("extents m", np.ptp(V, 0).round(1))

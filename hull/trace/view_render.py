# A version's parts seen orthographically from one side (back: from the stern, top: from above, front: from the bow),
# painted far to near, each triangle carrying its part; the arms shaded by depth so near and far strands read apart.
# Fitted onto a reference sheet: the in-plane orientation (axis swap / flips), uniform scale and shift searched on the
# silhouette (IoU) with vertex splats, then the full triangles painted once. Writes the part-label map, the depth map,
# the fit and a coloured sheet with a legend.
# SIL=<mask.npy> gives the reference silhouette (dark parts of a reference are lost by a brightness threshold).
# Usage: python view_render.py <mesh.npz> <sheet.png> <out_prefix> <back|top|front> [part_prefix ...  (default: all but SRC)]
import sys, os, json, numpy as np, cv2
MESH, SHEET, OP, VIEW = sys.argv[1:5]; z = np.load(MESH); ref = cv2.imread(SHEET); H, W = ref.shape[:2]
PRE = tuple(sys.argv[5:]); names = [k[2:] for k in z.files if k.startswith("v|") and (k[2:].startswith(PRE) if PRE else not k.startswith("v|SRC"))]
PLANE, DEP, NEAR = {"back": ((0, 2), 1, -1), "front": ((0, 2), 1, 1), "top": ((0, 1), 2, 1)}[VIEW]   # NEAR: +1 = larger depth coordinate is nearer
GROUP = [("CORP", ("C",), (70, 70, 230)), ("V placa", ("V",), (40, 160, 240)), ("brate", ("A1|", "A2|", "A10", "A9", "A3", "A5"), None),
         ("aripi rosii A7", ("A7",), (60, 0, 200)), ("grilaj A6", ("A6",), (230, 230, 0)), ("legaturi L (AI)", ("L",), (220, 120, 40)),
         ("arc U G1", ("G1",), (200, 90, 220)), ("nacela G2", ("G2",), (255, 255, 0)), ("aripi sus U", ("U",), (60, 200, 200)),
         ("hangare H", ("H",), (120, 200, 120)), ("original grannyte", ("SRC",), (200, 200, 200))]
def group(n): return next(i for i, (_, pre, _) in enumerate(GROUP) if n.startswith(pre))
V = [z["v|" + n] for n in names]; T = [z["t|" + n].astype(int) for n in names]; allv = np.vstack(V)
dmin, dmax = allv[:, DEP].min(), allv[:, DEP].max()
SIL = os.environ.get("SIL")
if SIL: refm = np.load(SIL).astype(bool)
else: refm = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY) > 40; refm = cv2.morphologyEx(refm.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8)) > 0
def uv(p, o):                                                             # o = (swap, flip_u, flip_v): world plane coords -> sheet axes (u right, v down)
    a, b = p[..., PLANE[0]], p[..., PLANE[1]]
    if o[0]: a, b = b, a
    return a * (-1 if o[1] else 1), b * (-1 if o[2] else 1)
# coarse fit at quarter scale on vertex splats
q = 4; rq = cv2.resize(refm.astype(np.uint8), (W // q, H // q), interpolation=cv2.INTER_AREA) > 0; ys, xs = np.nonzero(rq)
pts = allv[::3]; best = None
for o in [(s_, fu, fv) for s_ in (0, 1) for fu in (0, 1) for fv in (0, 1)]:
    u, v = uv(pts, o); s0 = (xs.max() - xs.min()) / np.ptp(u)
    for s in s0 * np.linspace(0.85, 1.15, 13):
        tu = (xs.min() + xs.max()) / 2 - s * (u.min() + u.max()) / 2; tv = (ys.min() + ys.max()) / 2 - s * (v.min() + v.max()) / 2
        for du in range(-8, 9, 2):
            for dv in range(-8, 9, 2):
                m = np.zeros_like(rq); iu = np.round(u * s + tu + du).astype(int); iv = np.round(v * s + tv + dv).astype(int); ok = (iu >= 0) & (iu < rq.shape[1]) & (iv >= 0) & (iv < rq.shape[0])
                m[iv[ok], iu[ok]] = True; m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
                sc = (m & rq).sum() / max((m | rq).sum(), 1)
                if best is None or sc > best[0]: best = (sc, o, s * q, (tu + du) * q, (tv + dv) * q)
sc, o, s, tu, tv = best
lab = np.full((H, W), -1, np.int32); dep = np.full((H, W), np.nan, np.float32)
TR = np.concatenate([V[i][T[i]] for i in range(len(names))]); P = np.concatenate([np.full(len(T[i]), i) for i in range(len(names))]); D = TR[:, :, DEP].mean(1)
u, v = uv(TR, o); px = np.stack([u * s + tu, v * s + tv], 2)
for i in np.argsort(D * NEAR):                                             # far first, near painted over
    qq = np.round(px[i]).astype(np.int32); cv2.fillConvexPoly(lab, qq, int(P[i])); cv2.fillConvexPoly(dep, qq, float(D[i]))
m = lab >= 0; iou = (m & refm).sum() / max((m | refm).sum(), 1)
out = (ref * 0.25).astype(np.uint8); gi = np.array([group(n) for n in names])
f = np.clip((dep - dmin) / (dmax - dmin), 0, 1); f = f if NEAR == 1 else 1 - f    # 1 = nearest
for k, (gname, _, col) in enumerate(GROUP):
    mk = m & (gi[np.clip(lab, 0, None)] == k)
    if col is None: c = np.stack([60 + 0 * f, 85 + 170 * f, 60 + 0 * f], -1); out[mk] = (out[mk] * 0.3 + c[mk] * 0.7).astype(np.uint8)
    else: out[mk] = (out[mk] * 0.3 + np.array(col) * 0.7).astype(np.uint8)
edge = cv2.morphologyEx(refm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; out[edge] = (255, 255, 255)
side = np.zeros((H, 1000, 3), np.uint8)
for k, (gname, _, col) in enumerate(GROUP):
    y = 70 + 75 * k; cv2.rectangle(side, (30, y - 30), (90, y + 15), (60, 200, 60) if col is None else col, -1)
    cv2.putText(side, gname + (" (deschis = aproape, inchis = departe)" if col is None else ""), (110, y + 8), 0, 1.0, (235, 235, 235), 2, cv2.LINE_AA)
cv2.putText(side, "alb = silueta referintei; IoU %.3f" % iou, (30, 70 + 75 * len(GROUP)), 0, 1.0, (235, 235, 235), 2, cv2.LINE_AA)
np.save(f"{OP}_parts.npy", lab); np.save(f"{OP}_depth.npy", dep)
json.dump({"names": names, "view": VIEW, "orient": o, "s": s, "tu": tu, "tv": tv, "iou": float(iou)}, open(f"{OP}_fit.json", "w"))
cv2.imwrite(f"{OP}_piese.png", cv2.resize(np.hstack([out, side]), None, fx=0.5, fy=0.5)); print("FIT %s orient %s s %.4f IoU %.3f" % (VIEW, o, s, iou))

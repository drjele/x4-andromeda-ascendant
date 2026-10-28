# Component 103+118 with a W section at the back (asked: it is two surfaces there - the blade 117/118 and the strip 103 -
# side by side, both smooth): every section curve of the piece (ps_banda103.py) fitted by the best 4-segment polyline
# (dynamic programming over the breakpoints: least squared distance of the curve to the segments); its 5 points (two ends
# + three corners) are five rails, each smoothed along the piece with twicing; where the blade is absent the W flattens
# into the V by itself. Mesh as ps_103_v.py: sections perpendicular to the middle rail, the polyline through the 5 rail
# points with rounded corners, THICK thick, rounded long edges, ribs with a shallow groove. _S built, _D mirrored.
# Usage: blender -b <file.blend> --python ps_103_w.py -- <banda103.npz> <out.blend> <dx> [name]
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX = a[1], float(a[2]); NAME = a[3] if len(a) > 3 else "piesa_comp_103_118"
env = lambda k, d: float(os.environ.get(k, d))
TH, RF, STEP, RIBW, GR, SG, NSEG = env("V103_GROSIME", "2.5"), env("V103_RAZA", "3"), 1.0, env("V103_NERVURA", "5"), env("V103_SANT", "0.6"), env("V103_NET", "20"), int(env("W103_SEGMENTE", "4"))
C, ys = D["C"], D["ys"]; K, NU = C.shape[:2]
def polyfit(Q):                                                        # best NSEG-segment polyline through Q (indices of corners)
    n = len(Q); E = np.full((n, n), np.inf)
    for i in range(n):
        for j in range(i + 1, n):
            d = Q[j] - Q[i]; L = np.linalg.norm(d)
            if L < 1e-9: E[i, j] = 0; continue
            w = Q[i + 1:j] - Q[i]; E[i, j] = float(np.sum((w[:, 0] * d[1] - w[:, 1] * d[0]) ** 2) / L ** 2)
    best = np.full((NSEG + 1, n), np.inf); arg = np.zeros((NSEG + 1, n), int); best[0, 0] = 0
    for s_ in range(1, NSEG + 1):
        for j in range(1, n):
            c = best[s_ - 1, :j] + E[:j, j]; i = int(np.argmin(c)); best[s_, j], arg[s_, j] = c[i], i
    idx = [n - 1]
    for s_ in range(NSEG, 0, -1): idx.append(arg[s_, idx[-1]])
    return idx[::-1]
BR = np.array([polyfit(C[k]) for k in range(K)])                        # (K, NSEG + 1) breakpoints per section
R3 = lambda P2: np.stack([P2[:, 0], ys, P2[:, 1]], 1)
rails = [R3(C[np.arange(K), BR[:, r]]) for r in range(NSEG + 1)]
def gs(X, sg):
    n = int(3 * sg); k = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); k /= k.sum()
    Z = np.vstack([2 * X[:1] - X[n:0:-1], X, 2 * X[-1:] - X[-2:-n - 2:-1]]); return np.stack([np.convolve(Z[:, i], k, "valid") for i in range(3)], 1)
rails = [2 * gs(r, SG) - gs(gs(r, SG), SG) for r in rails]
def resample(P, step):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, s[-1], step)
    return np.stack([np.interp(u, s, P[:, i]) for i in range(3)], 1)
rails = [resample(r, 0.25) for r in rails]
SP = resample(rails[NSEG // 2], STEP); tg = np.gradient(SP, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
def cut(R, p, n):
    d = (R - p) @ n; i = np.nonzero(np.sign(d[:-1]) != np.sign(d[1:]))[0]
    if not len(i): return R[np.argmin(np.abs(d))]
    i = i[np.argmin(np.linalg.norm(R[i] - p, axis=1))]; w = d[i] / (d[i] - d[i + 1]); return R[i] * (1 - w) + R[i + 1] * w
def fillet_line(pts, rf, na=10, nc=7):                                 # polyline with rounded corners (circle arcs, radius <= rf)
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        a_, b_, c_ = pts[k - 1], pts[k], pts[k + 1]; u1, u2 = (a_ - b_), (c_ - b_); l1, l2 = np.linalg.norm(u1), np.linalg.norm(u2); u1, u2 = u1 / max(l1, 1e-9), u2 / max(l2, 1e-9)
        ang = np.arccos(np.clip(u1 @ u2, -1, 1)); r_ = min(rf, 0.4 * min(l1, l2) * np.tan(ang / 2)) if 1e-3 < ang < np.pi - 1e-3 else 0
        if r_ <= 1e-3:                                                  # no room to round: same point count, collapsed corner
            out += [out[-1] + (b_ - out[-1]) * t for t in np.linspace(0, 1, na)[1:]] + [b_] * (nc - 1); continue
        dt = r_ / np.tan(ang / 2); t1, t2 = b_ + u1 * dt, b_ + u2 * dt; bis = (u1 + u2) / np.linalg.norm(u1 + u2); cc = b_ + bis * r_ / np.sin(ang / 2)
        out += [out[-1] + (t1 - out[-1]) * t for t in np.linspace(0, 1, na)[1:]]
        for t in np.linspace(0, 1, nc)[1:-1]: v = (t1 - cc) * (1 - t) + (t2 - cc) * t; out.append(cc + v / np.linalg.norm(v) * r_)
        out.append(t2)
    out += [out[-1] + (pts[-1] - out[-1]) * t for t in np.linspace(0, 1, na)[1:]]
    return np.array(out)
rings = []
for p, n in zip(SP, tg):
    pts = [cut(r, p, n) for r in rails]; cl = fillet_line(pts, RF); tc = np.gradient(cl, axis=0); tc /= np.maximum(np.linalg.norm(tc, axis=1), 1e-9)[:, None]
    off = np.cross(n, tc); off /= np.maximum(np.linalg.norm(off, axis=1), 1e-9)[:, None]
    e1 = [cl[-1] + (np.cos(t) * off[-1] + np.sin(t) * tc[-1]) * TH / 2 for t in np.linspace(0, np.pi, 7)[1:-1]]
    e0 = [cl[0] - (np.cos(t) * off[0] + np.sin(t) * tc[0]) * TH / 2 for t in np.linspace(0, np.pi, 7)[1:-1]]
    rings.append(np.vstack([cl + off * TH / 2, e1, (cl - off * TH / 2)[::-1], e0]))
X = np.array(rings); KR, M = X.shape[:2]
s_ = np.arange(KR) * STEP; ph = np.mod(s_, RIBW) / RIBW; groove = 1 - GR / TH * np.exp(-0.5 * (np.minimum(ph, 1 - ph) * RIBW / 0.6) ** 2)
cen = X.mean(1, keepdims=True); X = cen + (X - cen) * groove[:, None, None] ** 0.3
col = bpy.data.collections.get(os.environ.get("COLECTIE", "PS_PIESE")) or bpy.data.collections.new(os.environ.get("COLECTIE", "PS_PIESE"))
src = bpy.data.objects["R034 103_S"]; mat = src.material_slots[src.data.polygons[0].material_index].material
for side, sg in (("S", 1), ("D", -1)):
    V = X.reshape(-1, 3).copy(); V[:, 0] *= sg; V = np.vstack([V, X[0].mean(0) * [sg, 1, 1], X[-1].mean(0) * [sg, 1, 1]]); V[:, 0] += DX
    Fc = [(k * M + i, k * M + (i + 1) % M, (k + 1) * M + (i + 1) % M, (k + 1) * M + i) for k in range(KR - 1) for i in range(M)]
    Fc += [(KR * M, (i + 1) % M, i) for i in range(M)] + [(KR * M + 1, (KR - 1) * M + i, (KR - 1) * M + (i + 1) % M) for i in range(M)]
    if sg < 0: Fc = [f[::-1] for f in Fc]
    nm = "%s_%s" % (NAME, side)
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
    me = bpy.data.meshes.new(nm); me.from_pydata(V.tolist(), [], Fc); bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bnd = sum(1 for e in bm.edges if e.is_boundary); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(nm, me); col.objects.link(o)
    print("W103 %s: %d sectiuni, %d puncte pe sectiune, muchii libere %d" % (nm, KR, M, bnd))
seg_len = np.array([[np.linalg.norm(C[k, BR[k, r + 1]] - C[k, BR[k, r]]) for r in range(NSEG)] for k in range(K)])
for yq in (200, 0, -100, -200):
    k = int(np.argmin(np.abs(ys - yq))); print("  y %4d: tronsoane W %s m" % (yq, np.round(seg_len[k]).astype(int).tolist()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

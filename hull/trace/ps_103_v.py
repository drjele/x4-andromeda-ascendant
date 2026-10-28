# Component 103+118 made of V ribs, like the red nacelles (asked), keeping its current general shape and texture: three
# rails taken from the piece's section curves (ps_banda103.py) - the inner edge, the V's fold (the point farthest from the
# chord), the outer edge - smoothed with twicing (one smooth line each); stations every STEP m along the fold rail, each
# section in the plane perpendicular to it: the V through the three rail points (straight arms, the fold rounded with
# radius RF), THICK thick, rounded ends; ribs RIBW m long, a shallow groove where two ribs meet (so the ribs read with a
# single texture). _S built, _D mirrored. Ship coordinates (x + DX).
# Usage: blender -b <file.blend> --python ps_103_v.py -- <banda103.npz> <out.blend> <dx> [name]
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT, DX = a[1], float(a[2]); NAME = a[3] if len(a) > 3 else "piesa_comp_103_118"
env = lambda k, d: float(os.environ.get(k, d))
TH, RF, STEP, RIBW, GR, SG = env("V103_GROSIME", "2.5"), env("V103_RAZA", "3"), 1.0, env("V103_NERVURA", "5"), env("V103_SANT", "0.6"), env("V103_NET", "20")
C, ys = D["C"], D["ys"]; K, NU = C.shape[:2]
ch = C[:, -1] - C[:, 0]; chn = ch / np.linalg.norm(ch, axis=1)[:, None]
dist = np.abs((C[..., 0] - C[:, :1, 0]) * chn[:, None, 1] - (C[..., 1] - C[:, :1, 1]) * chn[:, None, 0]); kf = np.argmax(dist, axis=1)
R3 = lambda P2: np.stack([P2[:, 0], ys, P2[:, 1]], 1)
rails = [R3(C[:, 0]), R3(C[np.arange(K), kf]), R3(C[:, -1])]               # inner, fold, outer
def gs(X, sg):
    n = int(3 * sg); k = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); k /= k.sum()
    Z = np.vstack([2 * X[:1] - X[n:0:-1], X, 2 * X[-1:] - X[-2:-n - 2:-1]]); return np.stack([np.convolve(Z[:, i], k, "valid") for i in range(3)], 1)
rails = [2 * gs(r, SG) - gs(gs(r, SG), SG) for r in rails]
def resample(P, step):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; u = np.arange(0, s[-1], step)
    return np.stack([np.interp(u, s, P[:, i]) for i in range(3)], 1)
rails = [resample(r, 0.25) for r in rails]
F_ = resample(rails[1], STEP); tg = np.gradient(F_, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
def cut(R, p, n):                                                      # where rail R crosses the plane (p, n), nearest to p
    d = (R - p) @ n; i = np.nonzero(np.sign(d[:-1]) != np.sign(d[1:]))[0]
    if not len(i): return R[np.argmin(np.abs(d))]
    i = i[np.argmin(np.linalg.norm(R[i] - p, axis=1))]; w = d[i] / (d[i] - d[i + 1]); return R[i] * (1 - w) + R[i + 1] * w
NA_, NC = 14, 8; rings = []
for p, n in zip(F_, tg):
    A, Bp = cut(rails[0], p, n), cut(rails[2], p, n); arms = [A - p, Bp - p]; L_ = [np.linalg.norm(v) for v in arms]; u_ = [v / max(l, 1e-6) for v, l in zip(arms, L_)]
    ang = np.arccos(np.clip(u_[0] @ u_[1], -1, 1)); rf = min(RF, 0.45 * min(L_) * np.tan(ang / 2) if ang > 1e-3 else RF); dt = rf / np.tan(max(ang, 1e-3) / 2)
    T1, T2 = p + u_[0] * dt, p + u_[1] * dt; bis = (u_[0] + u_[1]); bis /= max(np.linalg.norm(bis), 1e-9); cc = p + bis * rf / np.sin(max(ang, 1e-3) / 2)
    cl = [A + (T1 - A) * t for t in np.linspace(0, 1, NA_)]           # centre line: inner end -> fillet -> outer end
    for t in np.linspace(0, 1, NC)[1:-1]:
        v = (T1 - cc) * (1 - t) + (T2 - cc) * t; cl.append(cc + v / np.linalg.norm(v) * rf)
    cl += [T2 + (Bp - T2) * t for t in np.linspace(0, 1, NA_)]
    cl = np.array(cl); tc = np.gradient(cl, axis=0); tc /= np.linalg.norm(tc, axis=1)[:, None]; off = np.cross(n, tc); off /= np.linalg.norm(off, axis=1)[:, None]
    e1 = [cl[-1] + (np.cos(t) * off[-1] + np.sin(t) * tc[-1]) * TH / 2 for t in np.linspace(0, np.pi, 7)[1:-1]]
    e0 = [cl[0] - (np.cos(t) * off[0] + np.sin(t) * tc[0]) * TH / 2 for t in np.linspace(0, np.pi, 7)[1:-1]]
    rings.append(np.vstack([cl + off * TH / 2, e1, (cl - off * TH / 2)[::-1], e0]))
X = np.array(rings); KR, M = X.shape[:2]
s_ = np.arange(KR) * STEP; ph = np.mod(s_, RIBW) / RIBW; groove = 1 - GR / TH * np.exp(-0.5 * (np.minimum(ph, 1 - ph) * RIBW / 0.6) ** 2)   # groove at rib joints
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
    print("V103 %s: %d sectiuni (%.0f m pe indoitura), %d nervuri de %.0f m, grosime %.1f m, %d varfuri, muchii libere %d" % (nm, KR, s_[-1], int(s_[-1] / RIBW) + 1, RIBW, TH, len(me.vertices), bnd))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

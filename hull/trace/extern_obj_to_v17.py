# An external OBJ (any axes and scale) brought into our world frame (x across, y bow+, z up) and onto a reference model
# already there: all its objects merged to one triangle set, PCA axes (length, width, height), small rotations fitted on
# our confirmed silhouettes (extern_align.py), scaled to the length, then the right-handed turn among the four that keep
# the axes (identity, 180 deg about x/y/z) chosen by the best 3-view silhouette match with the reference model.
# Writes the whole model (objects kept apart) as an OBJ in the world frame + a triangles npz.
# Usage: python extern_obj_to_v17.py <in.obj> <ref.obj> <layout.json> <vederi.json> <views.json> <length_m> <out_prefix>
import sys, subprocess, numpy as np, cv2
IN, REF, LJ, VJ, SJ, LEN, OP = sys.argv[1:8]; LEN = float(LEN)
V = []; objs = []; cur = None
for l in open(IN, errors="ignore"):
    if l.startswith("v "): V.append(l.split()[1:4])
    elif l.startswith("o ") or l.startswith("g "): cur = [l.split(None, 1)[1].strip(), []]; objs.append(cur)
    elif l.startswith("f "):
        if cur is None: cur = ["mesh", []]; objs.append(cur)
        ids = [int(x.split("/")[0]) for x in l.split()[1:]]; ids = [i - 1 if i > 0 else len(V) + i for i in ids]
        for k in range(1, len(ids) - 1): cur[1].append((ids[0], ids[k], ids[k + 1]))
V = np.array(V, float); objs = [(n, np.array(t, int)) for n, t in objs if t]
T = np.vstack([t for _, t in objs]); print("objects", len(objs), "verts", len(V), "tris", len(T))
used = np.unique(T); c = V[used]; A = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
cen = (V[T].mean(1) * A[:, None]).sum(0) / A.sum(); w, E = np.linalg.eigh(np.cov((c - cen).T)); E = E[:, ::-1]
if np.linalg.det(E) < 0: E[:, 2] *= -1
P = (V - cen) @ E; np.savez_compressed(OP + "_pca.npz", **{"v|nava": P.astype(np.float32), "t|nava": T})
subprocess.run([sys.executable, "extern_align.py", OP + "_pca.npz", LJ, VJ, SJ, str(LEN), OP + "_al.npz"], check=True)
a = np.load(OP + "_al.npz"); Q = a["v|nava"].astype(float)
Q = np.stack([Q[:, 1], Q[:, 0], -Q[:, 2]], 1)                              # length -> y, width -> x, a right-handed swap
R = np.array([l.split()[1:4] for l in open(REF) if l.startswith("v ")], float); R = R[np.random.default_rng(0).choice(len(R), 150000)]
def sil(P, i, j, n=300, box=None):
    lo, hi = box; u = (P[:, i] - lo[i]) / (hi[i] - lo[i]); v = (P[:, j] - lo[j]) / (hi[j] - lo[j]); m = np.zeros((n, n), np.uint8)
    ok = (u >= 0) & (u < 1) & (v >= 0) & (v < 1); m[(v[ok] * (n - 1)).astype(int), (u[ok] * (n - 1)).astype(int)] = 1; return cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
box = (R.min(0), R.max(0)); best = None
for name, M in [("id", np.diag([1, 1, 1])), ("x180", np.diag([1, -1, -1])), ("y180", np.diag([-1, 1, -1])), ("z180", np.diag([-1, -1, 1]))]:
    q = Q @ M; q = q - (q.min(0) + q.max(0)) / 2 + (box[0] + box[1]) / 2; qs = q[np.random.default_rng(1).choice(len(q), min(len(q), 150000))]; s = 0
    for i, j in ((0, 1), (1, 2), (0, 2)):
        A_ = sil(R, i, j, box=box); B_ = sil(qs, i, j, box=box); s += (A_ & B_).sum() / (A_ | B_).sum()
    print("turn", name, "IoU %.3f" % (s / 3))
    if best is None or s > best[0]: best = (s, name, q)
s, name, q = best; print("chosen", name, "%.3f" % (s / 3))
with open(OP + "_in_V17.obj", "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(p) for p in q))
    for n, t in objs: f.write("o %s\n" % n); f.write("".join("f %d %d %d\n" % tuple(x + 1) for x in t))
print("WROTE", OP + "_in_V17.obj", q.min(0).round(0), q.max(0).round(0))

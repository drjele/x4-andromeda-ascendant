# The objects of the second reference that the first one does not have (details only it carries, e.g. the ribs on the
# arc): the second model's objects brought into the common frame (the same normalisation + alignment as ref_compare.py),
# each object's surface sampled and measured against the first model; an object whose points lie mostly farther than
# DIST m from it is an extra. Writes the extras as one OBJ (objects kept apart) and lists them.
# Usage: python extract_extras.py <a_medie.obj> <b_in_world.obj> <transformari.json> <dist_m> <share> <out.obj>
import sys, json, numpy as np
from scipy.spatial import cKDTree
A_OBJ, B_OBJ, TJ, DIST, SHARE, OUT = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
T = {k: np.array(v) for k, v in json.load(open(TJ)).items()}; rng = np.random.default_rng(0)
VA = np.array([l.split()[1:4] for l in open(A_OBJ) if l.startswith("v ")], float); tree = cKDTree(VA[rng.choice(len(VA), min(len(VA), 600000), replace=False)])
V, objs, cur = [], [], None
for l in open(B_OBJ):
    if l.startswith("v "): V.append(l.split()[1:4])
    elif l.startswith("o "): cur = [l[2:].strip(), []]; objs.append(cur)
    elif l.startswith("f "): cur[1].append([int(x.split("/")[0]) - 1 for x in l.split()[1:4]])
V = np.array(V, float); V = ((V - (T["lb"] + T["hb"]) / 2) * (T["Em"] / (T["hb"] - T["lb"]))) @ T["R"].T + T["t"]
keep = []
for name, F in objs:
    F = np.array(F); Tr = V[F]; a = np.linalg.norm(np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0]), axis=1)
    if a.sum() <= 0: continue
    i = rng.choice(len(F), 3000, p=a / a.sum()); r1, r2 = rng.random(3000), rng.random(3000); s_ = np.sqrt(r1)
    P = Tr[i, 0] * (1 - s_)[:, None] + Tr[i, 1] * (s_ * (1 - r2))[:, None] + Tr[i, 2] * (s_ * r2)[:, None]
    d, _ = tree.query(P); share = (d > DIST).mean()
    if share > SHARE: keep.append((name, F, share, len(F)))
used = np.unique(np.concatenate([F.ravel() for _, F, _, _ in keep])) if keep else np.array([], int); idx = {v: k for k, v in enumerate(used)}
with open(OUT, "w") as f:
    f.write("".join("v %.3f %.3f %.3f\n" % tuple(V[u]) for u in used))
    for name, F, share, n in keep:
        f.write("o %s\n" % name); f.write("".join("f %d %d %d\n" % (idx[a] + 1, idx[b] + 1, idx[c] + 1) for a, b, c in F))
for name, F, share, n in sorted(keep, key=lambda k: -k[3]): print("%-32s %6d tris  %3.0f%% departe" % (name, n, 100 * share))
print("EXTRAS", len(keep), "objects of", len(objs))

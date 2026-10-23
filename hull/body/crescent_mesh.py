# Horseshoe swept from its inner edge outward: a straight inner wall, a flat top to the centreline,
# then a gentle outer slope into the hull. Offsets go outward, away from the bend, so nothing folds.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
P = json.load(open(f"{D}/crescent.json"))["dorsal_crescent"]
SINK = 2.0; NT = 400; NS = 40

def smooth(a, s):
    r = int(3 * s); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    return np.stack([np.convolve(np.pad(a[:, c], r, mode="edge"), k, "valid") for c in range(a.shape[1])], 1) if a.ndim > 1 else np.convolve(np.pad(a, r, mode="edge"), k, "valid")

pts = np.array(P["points"], float); full = np.vstack([pts[::-1] * [-1, 1], pts[1:]])
halves = np.r_[P["half"][::-1], P["half"][1:]]; heights = np.r_[P["height"][::-1], P["height"][1:]]
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(full, axis=0), axis=1))]; T = seg / seg[-1]
t = np.linspace(0, 1, NT)
C = smooth(np.stack([np.interp(t, T, full[:, 0]), np.interp(t, T, full[:, 1])], 1), 18)
W = smooth(np.interp(t, T, halves), 12); H = smooth(np.interp(t, T, heights), 12)
tan = np.gradient(C, axis=0); tan /= np.linalg.norm(tan, axis=1)[:, None]
nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
inner_pt = np.array(P["inner"], float)
sgn = np.sign(((inner_pt - C) * nrm).sum(1)); sgn[sgn == 0] = 1; nrm_in = nrm * sgn[:, None]
E = smooth(C + nrm_in * W[:, None], 22)            # the inner edge, smoothed
etan = np.gradient(E, axis=0); etan /= np.linalg.norm(etan, axis=1)[:, None]
out = np.stack([-etan[:, 1], etan[:, 0]], 1)
out *= np.sign(((C - E) * out).sum(1))[:, None]    # point from the inner edge toward the centreline
out = smooth(out, 15); out /= np.linalg.norm(out, axis=1)[:, None]

bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name == "dorsal_crescent"]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
def hull(x, y):
    hit = tree.ray_cast(Vector((x, y, 3000)), Vector((0, 0, -1)), 6000)[0]
    return hit
bm = bmesh.new(); rows = []
for i in range(NT):
    w, h = W[i], H[i]; reach = w * (1 + P["outer"])
    row = []
    for j in range(NS + 1):
        s = reach * (j / NS) ** 1.0
        q = E[i] + out[i] * s
        base = hull(q[0], q[1])
        if base is None: base = Vector((q[0], q[1], 0))
        if s <= w: lift = h
        else:
            v = min(1.0, (s - w) / (reach - w)); lift = h * (1 - v * v * (3 - 2 * v)) - SINK * v ** 6
        row.append(base + Vector((0, 0, lift)))
    # the straight inner wall: a vertex at the hull under the inner edge
    b0 = hull(E[i][0], E[i][1]) or Vector((E[i][0], E[i][1], 0))
    rows.append([bm.verts.new(b0 - Vector((0, 0, SINK)))] + [bm.verts.new(v) for v in row])
for a, b in zip(rows, rows[1:]):
    for j in range(len(a) - 1):
        bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
bm.normal_update()
if sum(f.normal.z for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("dorsal_crescent"); bm.to_mesh(me)
for pp in me.polygons: pp.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("dorsal_crescent", me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("CRESCENT", len(me.polygons))

# Fine rails along each arm: the double ribs on the outer flank behind the pod, a line over the aft loop
# and the paired lines along the upper member; thin tubes set half into the arm surface, tapering at both ends.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Matrix
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
A = json.load(open(f"{D}/arms/a_params.json"))["members"]["arm"]; R = json.load(open(f"{D}/arms/a_deco.json"))["ribs"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("ribs_r", "ribs_l")]: bpy.data.objects.remove(o)
def catmull(pts, n):
    p = np.array(pts, float); p = np.vstack([p[:1], p, p[-1:]]); out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2]); return np.array(out)
C = catmull(A["path"], 10); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; f = s / s[-1]
Sec = np.array(A["sections"], float); W = np.interp(f, Sec[:, 0], Sec[:, 1]); H = np.interp(f, Sec[:, 0], Sec[:, 2])
bm = bmesh.new(); K = 12
for rib in R:
    sel = (C[:, 1] >= rib["y"][0]) & (C[:, 1] <= rib["y"][1]) & ((C[:, 2] < 100) if rib["lower"] else (C[:, 2] > 150))
    idx = np.where(sel)[0]; rings = []
    for n, i in enumerate(idx):
        t = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]; t /= np.linalg.norm(t)
        w = np.cross(t, [0, 0, 1.0]); w /= np.linalg.norm(w); w = w if w[0] > 0 else -w; u = np.cross(t, w); u = u if u[2] > 0 else -u
        a = math.radians(rib["angle"]); nrm = w * math.cos(a) / (W[i] / 2) + u * math.sin(a) / (H[i] / 2); nrm /= np.linalg.norm(nrm)
        c = C[i] + w * W[i] / 2 * math.cos(a) + u * H[i] / 2 * math.sin(a) + nrm * (rib["r"] - rib["sink"])
        q = n / max(len(idx) - 1, 1); r = rib["r"] * min(1.0, 4 * q, 4 * (1 - q)) ** 0.5 + 0.2
        side = np.cross(t, nrm)
        rings.append([bm.verts.new(c + (nrm * math.cos(b) + side * math.sin(b)) * r) for b in np.linspace(0, 2 * math.pi, K, endpoint=False)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(K): bm.faces.new((r0[k], r0[(k + 1) % K], r1[(k + 1) % K], r1[k]))
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("ribs_r"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("ribs_r", me))
ml = me.copy(); ml.name = "ribs_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("ribs_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("RIBS ok")

# Scales along the outer underside of each lower arm: overlapping leaves, each rooted in the arm at its
# front and lifting off toward its back edge, like shingles pointing aft.
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector, Matrix
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
A = json.load(open(f"{D}/arms/a_params.json"))["members"]["arm"]; S = json.load(open(f"{D}/arms/a_deco.json"))["scales"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("scales_r", "scales_l")]: bpy.data.objects.remove(o)
def catmull(pts, n):
    p = np.array(pts, float); p = np.vstack([p[:1], p, p[-1:]]); out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2]); return np.array(out)
C = catmull(A["path"], 10); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; f = s / s[-1]
Sec = np.array(A["sections"], float); W = np.interp(f, Sec[:, 0], Sec[:, 1]); H = np.interp(f, Sec[:, 0], Sec[:, 2])
front = (C[:, 1] > -700) & (C[:, 2] < -100)
bm = bmesh.new()
for y in np.linspace(*S["y"], S["count"]):
    i = np.where(front)[0][np.argmin(np.abs(C[front, 1] - y))]
    t = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]; t /= np.linalg.norm(t)
    w = np.cross(t, [0, 0, 1.0]); w /= np.linalg.norm(w); w = w if w[0] > 0 else -w; u = np.cross(t, w) if np.cross(t, w)[2] > 0 else np.cross(w, t)
    a = math.radians(S["angle"]); p = C[i] + w * W[i] / 2 * math.cos(a) + u * H[i] / 2 * math.sin(a)
    n = w * math.cos(a) / (W[i] / 2) + u * math.sin(a) / (H[i] / 2); n /= np.linalg.norm(n)
    back = -t if t[1] > 0 else t; back = back - n * back.dot(n); back /= np.linalg.norm(back); side = np.cross(n, back)
    L, R = S["length"], S["width"] / 2; rows = []
    for k in range(13):
        q = k / 12; hw = R * min(1.0, 3.0 * q) ** 0.5 * (1 - q) ** 0.6 + 0.3
        lift = -S["sink"] + S["lift"] * q * q
        row = []
        for j in range(9):
            v = -1 + 2 * j / 8; c = p + back * (q * L - 0.25 * L) + side * v * hw + n * (lift - 0.15 * S["lift"] * v * v)
            row.append((bm.verts.new(c + n * S["thick"] / 2 * (1 - abs(v) ** 4) * (1 - q) ** 0.3), bm.verts.new(c - n * S["thick"] / 2 * (1 - abs(v) ** 4) * (1 - q) ** 0.3)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(8):
            bm.faces.new((r0[j][0], r0[j + 1][0], r1[j + 1][0], r1[j][0])); bm.faces.new((r0[j][1], r1[j][1], r1[j + 1][1], r0[j + 1][1]))
        for j in (0, 8): bm.faces.new((r0[j][0], r1[j][0], r1[j][1], r0[j][1]))
    for r in (rows[0], rows[-1]):
        for j in range(8): bm.faces.new((r[j][0], r[j][1], r[j + 1][1], r[j + 1][0]))
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.05); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("scales_r"); bm.to_mesh(me)
for pp in me.polygons: pp.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("scales_r", me))
ml = me.copy(); ml.name = "scales_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("scales_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("SCALES ok")

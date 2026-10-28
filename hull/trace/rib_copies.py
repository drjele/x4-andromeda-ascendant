# New ribs as copies of the copied ribs, recoloured and fitted beside them (the user's idea): every gap between copied
# ribs k and k+1 is split into n equal slots, n = round(gap width / copied rib width) (at least 1), so each copy keeps
# about the width of a real rib; in each slot a copy of the nearer copied rib (rib k for the first half of the slots,
# rib k+1 for the second) is turned and resized onto that slot: its own corner frame (point, two arm ends, width) mapped
# onto the slot's two faces, which are interpolated between rib k's front face and rib k+1's back face (corner by corner).
# So the copies sit side by side, touching each other and the copied ribs, with the real ribs' curved V shape, and the
# angle/size changing gradually from one copied rib to the next. Lighter red. One side, mirrored.
# Usage: blender -b <step2.blend> --python rib_copies.py -- <corners.json> <out.blend> <dx> <k...|all>
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, OUT, DX = a[0], a[1], float(a[2]); R = json.load(open(CJ))
KS = list(range(len(R) - 1)) if a[3:] == ["all"] else [int(x) for x in a[3:]]; sc = bpy.context.scene
def rib(k):
    o = bpy.data.objects["nervura_copiata_%02d_S" % k]; return np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0], [tuple(p.vertices) for p in o.data.polygons]
def face(k, f): c = np.array(R[k][f]); return np.array([c[1], c[0], c[2]])     # point, end1, end2
def frame(k):
    fb, ff = face(k, "spate"), face(k, "fata"); p, e1, e2 = (fb + ff) / 2; u, v = e1 - p, e2 - p; n = np.cross(u, v); n /= np.linalg.norm(n)
    hb, hf = np.dot(fb[0] - p, n), np.dot(ff[0] - p, n)
    if hf < hb: n, hb, hf = -n, -hb, -hf
    return p, u, v, n, hb, hf
def coords(k, P):
    p, u, v, n, hb, hf = frame(k); ab = np.linalg.solve(np.stack([u, v, n], 1), (P - p).T).T; return ab[:, 0], ab[:, 1], (ab[:, 2] - hb) / (hf - hb)
def rebuild(A_, B_, t, F0, F1):
    s0 = F0[0] + A_[:, None] * (F0[1] - F0[0]) + B_[:, None] * (F0[2] - F0[0]); s1 = F1[0] + A_[:, None] * (F1[1] - F1[0]) + B_[:, None] * (F1[2] - F1[0])
    return s0 * (1 - t[:, None]) + s1 * t[:, None]
old = bpy.data.collections.get("NERVURI_NOI")
if old:
    for o in list(old.objects): bpy.data.objects.remove(o)
    bpy.data.collections.remove(old)
col = bpy.data.collections.new("NERVURI_NOI"); sc.collection.children.link(col)
m = bpy.data.materials.get("nervura_noua_rosu_deschis") or bpy.data.materials.new("nervura_noua_rosu_deschis")
m.diffuse_color = (0.85, 0.12, 0.10, 1); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.12, 0.10, 1)
tot = 0
for k in KS:
    F0, F1 = face(k, "fata"), face(k + 1, "spate"); width = np.linalg.norm(F1.mean(0) - F0.mean(0))
    rw = 0.5 * (np.linalg.norm(face(k, "fata").mean(0) - face(k, "spate").mean(0)) + np.linalg.norm(face(k + 1, "fata").mean(0) - face(k + 1, "spate").mean(0)))
    n = max(1, int(round(width / rw)))
    for j in range(n):
        f0, f1 = j / n, (j + 1) / n; S0 = F0 * (1 - f0) + F1 * f0; S1 = F0 * (1 - f1) + F1 * f1
        src = k if (j + 0.5) / n < 0.5 else k + 1; P, F = rib(src); A_, B_, t = coords(src, P); V = rebuild(A_, B_, t, S0, S1)
        for side in (1, -1):
            W = V.copy(); W[:, 0] *= side; FF = F if side > 0 else [f[::-1] for f in F]
            me = bpy.data.meshes.new("n"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], FF); me.materials.append(m)
            for p_ in me.polygons: p_.use_smooth = True
            ob = bpy.data.objects.new("nervura_noua_%02d_%d%s" % (k, j, "_S" if side > 0 else "_D"), me); col.objects.link(ob)
    tot += n
    print("GOL %02d (intre %d si %d): %.1f m -> %d copii de cate %.1f m (nervura copiata %.1f m)" % (k, k, k + 1, width, n, width / n, rw))
print("TOTAL %d nervuri noi pe parte" % tot); bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

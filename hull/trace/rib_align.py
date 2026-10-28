# Step A: the copied ribs aligned onto the guide lines. For every copied rib and each of its 3 corners (end1, point,
# end2; middle of the back and front faces) the target is the nearest point of that corner's guide (the fitted Bezier).
# The rib is then rebuilt in its own corner frame (a, b along its arms, t across its width) with both faces moved by the
# corner's correction, so its 3 corners land exactly on the guides while its curved V shape and its width are kept.
# The original copies are kept hidden (backup); the aligned corners are written for the next steps. One side, mirrored.
# Usage: blender -b <step2.blend> --python rib_align.py -- <corners.json> <guides.json> <out.blend> <aligned.json> <dx>
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, GJ, OUT, AJ, DX = a[0], a[1], a[2], a[3], float(a[4])
R = json.load(open(CJ)); Gd = json.load(open(GJ)); sc = bpy.context.scene
def bez(c, t): c = np.array(c); t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
guides = [bez(r["control"], np.linspace(0, 1, 20000)) for r in Gd["rails"]]     # rail i = corner i (end1, point, end2)
def face(k, f): c = np.array(R[k][f]); return np.array([c[1], c[0], c[2]])     # point, end1, end2
def frame(k):
    fb, ff = face(k, "spate"), face(k, "fata"); p, e1, e2 = (fb + ff) / 2; u, v = e1 - p, e2 - p; n = np.cross(u, v); n /= np.linalg.norm(n)
    hb, hf = np.dot(fb[0] - p, n), np.dot(ff[0] - p, n)
    if hf < hb: n, hb, hf = -n, -hb, -hf
    return p, u, v, n, hb, hf
def rebuild(A_, B_, t, F0, F1):
    s0 = F0[0] + A_[:, None] * (F0[1] - F0[0]) + B_[:, None] * (F0[2] - F0[0]); s1 = F1[0] + A_[:, None] * (F1[1] - F1[0]) + B_[:, None] * (F1[2] - F1[0])
    return s0 * (1 - t[:, None]) + s1 * t[:, None]
bk = bpy.data.collections.new("NERVURI_COPIATE_ORIGINAL"); sc.collection.children.link(bk)
out = []; moves = []
for k in range(len(R)):
    fb, ff = face(k, "spate"), face(k, "fata"); mid = (fb + ff) / 2
    tgt = np.array([guides[[1, 0, 2][i]][np.argmin(np.linalg.norm(guides[[1, 0, 2][i]] - mid[i], axis=1))] for i in range(3)])   # face order (point, end1, end2) -> rails (1, 0, 2)
    d = tgt - mid; moves.append(np.linalg.norm(d, axis=1))
    p, u, v, n, hb, hf = frame(k)
    for side in ("_S", "_D"):
        o = bpy.data.objects["nervura_copiata_%02d%s" % (k, side)]; P = np.array([o.matrix_world @ x.co for x in o.data.vertices]) - [DX, 0, 0]
        sg = 1 if side == "_S" else -1; Pl = P * [sg, 1, 1]
        ab = np.linalg.solve(np.stack([u, v, n], 1), (Pl - p).T).T; t = (ab[:, 2] - hb) / (hf - hb)
        F0, F1 = (fb, ff) if True else (ff, fb); V = rebuild(ab[:, 0], ab[:, 1], t, F0 + d, F1 + d) * [sg, 1, 1] + [DX, 0, 0]
        c = o.copy(); c.data = o.data.copy(); bk.objects.link(c); c.name = "orig_" + o.name
        Mi = o.matrix_world.inverted()
        for i, x in enumerate(o.data.vertices): x.co = Mi @ __import__("mathutils").Vector(V[i])
        o.data.update()
    out.append({"nume": R[k]["nume"], "spate": [(fb + d)[[1, 0, 2][i]].tolist() for i in range(3)], "fata": [(ff + d)[[1, 0, 2][i]].tolist() for i in range(3)], "latime_m": R[k]["latime_m"]})
json.dump(out, open(AJ, "w"), indent=1)
bpy.context.view_layer.layer_collection.children["NERVURI_COPIATE_ORIGINAL"].exclude = True
M = np.array(moves); print("ALINIERE: mutare colturi m (capat1, varf, capat2): medie %s, max %s" % (np.round(M.mean(0), 2).tolist(), np.round(M.max(0), 2).tolist()))
chk = [max(np.min(np.linalg.norm(guides[i] - ((np.array(o_["spate"])[i] + np.array(o_["fata"])[i]) / 2), axis=1)) for i in range(3)) for o_ in out]
print("VERIFICARE: distanta maxima colt aliniat -> ghidaj: %.3f m" % max(chk))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

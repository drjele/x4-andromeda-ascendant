# Step 1 of the nacelle: the 6 corners of copied ribs. A rib is a thin bar bent into a V (rounded point), about 10 m wide
# along the row. Its width direction = the rib's thinnest principal axis (it runs along the row); the bar split into its
# two faces by that coordinate (the half toward the previous rib and the half toward the next); on each face the V's
# 3 corners: the two arm ends (the pair of face points farthest apart along the bar) and the point (the face point farthest from the
# line through the two ends). Marked with small spheres on the chosen ribs (back face: dark, front face: light; colour per
# corner: green/yellow = arm ends, blue = point), beside the untouched reference. Corners of all ribs saved (JSON).
# Usage: blender -b <graph.blend> --python rib_corners.py -- <out.blend> <out.json> <dx> <rib numbers to mark...>
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, JS, DX = a[0], a[1], float(a[2]); MARK = [int(x) for x in a[3:]]
ribs = sorted([o for o in bpy.data.objects if o.name.startswith("nervura_copiata_") and o.name.endswith("_S")], key=lambda o: o.name)
res = []; prev = None
for o in ribs:
    P = np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0]; c = P.mean(0)
    ev, E = np.linalg.eigh(np.cov((P - c).T)); w = E[:, 0]                  # width direction (along the row)
    if prev is not None and np.dot(w, c - prev) < 0: w = -w                 # pointing from the previous rib to the next
    s = (P - c) @ w; faces = []
    for sel in (s < 0, s >= 0):                                             # back face (toward previous), front face (toward next)
        idx = np.where(sel)[0]; F = P[sel]; q = F - np.outer((F - c) @ w, w)    # flattened onto the rib's plane
        # the arm ends = the pair farthest apart ALONG the bar (shortest paths over the rib's own edges), not in a straight
        # line: on a V with one longer arm the straight-line farthest pair is point-to-end
        pos = {v: n for n, v in enumerate(idx)}; nn = len(idx); D = np.full((nn, nn), np.inf); np.fill_diagonal(D, 0)
        for e in o.data.edges:
            u_, v_ = e.vertices
            if u_ in pos and v_ in pos: d_ = np.linalg.norm(q[pos[u_]] - q[pos[v_]]); D[pos[u_], pos[v_]] = D[pos[v_], pos[u_]] = min(D[pos[u_], pos[v_]], d_)
        for m_ in range(nn): D = np.minimum(D, D[:, m_:m_ + 1] + D[m_:m_ + 1, :])   # all shortest paths (Floyd)
        Dg = np.where(np.isinf(D), -1, D); i, j = np.unravel_index(np.argmax(Dg), Dg.shape)
        ab = (q[j] - q[i]) / np.linalg.norm(q[j] - q[i]); off = (q - q[i]) - np.outer((q - q[i]) @ ab, ab); k = int(np.argmax(np.linalg.norm(off, axis=1)))
        e1, e2 = F[i], F[j]
        if prev is not None and res:                                        # arm ends kept in the same order as the previous rib
            pe = res[-1]["fata"][0]
            if np.linalg.norm(e1 - pe[0]) + np.linalg.norm(e2 - pe[1]) > np.linalg.norm(e2 - pe[0]) + np.linalg.norm(e1 - pe[1]): e1, e2 = e2, e1
        faces.append([e1.tolist(), F[k].tolist(), e2.tolist()])             # [arm end 1, point, arm end 2]
    res.append({"nume": o.name, "spate": faces[0], "fata": faces[1], "latime_m": float(np.ptp(s))}); prev = c
json.dump(res, open(JS, "w"), indent=1)
sc = bpy.context.scene; mc = bpy.data.collections.new("COLTURI_NERVURI"); sc.collection.children.link(mc)
def mat(n, c):
    m = bpy.data.materials.new(n); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
cols = {("spate", 0): (0.0, 0.45, 0.1, 1), ("spate", 1): (0.0, 0.2, 0.6, 1), ("spate", 2): (0.6, 0.45, 0.0, 1),
        ("fata", 0): (0.3, 1.0, 0.4, 1), ("fata", 1): (0.4, 0.7, 1.0, 1), ("fata", 2): (1.0, 0.9, 0.3, 1)}
mats = {k: mat("colt_%s_%d" % k, v) for k, v in cols.items()}
for o in [o for o in bpy.data.objects if o.name.startswith(("sina_", "varf_"))]: o.hide_set(True); o.hide_render = True
for r_ in MARK:
    r = res[r_]
    for face in ("spate", "fata"):
        for i, p in enumerate(r[face]):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.6, location=tuple(np.array(p) + [DX, 0, 0])); s_ = bpy.context.active_object
            for c in s_.users_collection: c.objects.unlink(s_)
            mc.objects.link(s_); s_.data.materials.append(mats[(face, i)]); s_.name = "colt_nervura%02d_%s_%s" % (r_, face, ["capat1", "varf", "capat2"][i])
for r_ in MARK: print("NERVURA %02d: latime pe rand %.1f m; colturi spate %s; fata %s" % (r_, res[r_]["latime_m"], np.round(res[r_]["spate"], 0).tolist(), np.round(res[r_]["fata"], 0).tolist()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

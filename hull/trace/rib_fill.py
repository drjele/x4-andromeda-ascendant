# The nacelle completed on its rib graph: the 3 rails (green, blue, yellow) carried on past the first rib, curving smoothly
# (quadratic, leaving along their own direction) into one common point ahead (the sharp end); new ribs placed half-way
# between the copied ribs (and along the extension, getting smaller), each one a copied rib carried onto the rails' corners
# there (same curved shape), widened across the row until it touches its copied neighbours, lighter red. Drawn beside the
# untouched reference with the copied ribs and the rails. One side, mirrored.
# Usage: blender -b <graph.blend> --python rib_fill.py -- <corners.json> <out.blend> <dx> [ext_ribs]
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, OUT, DX = a[0], a[1], float(a[2]); NEXT = int(a[3]) if len(a) > 3 else 4
D = json.load(open(CJ)); K = np.array(D["corners"]); C = np.array(D["centres"]); sc = bpy.context.scene
G, B, Y = 0, 1, 2                                                           # rail indices: green, blue, yellow
sp = np.median(np.linalg.norm(np.diff(C, axis=0), axis=1))
# extension: each rail from its first point along its own direction, into the common apex ahead
dirs = [(K[0, i] - K[1, i]) / np.linalg.norm(K[0, i] - K[1, i]) for i in range(3)]
apex = K[0].mean(0) + np.mean(dirs, 0) / np.linalg.norm(np.mean(dirs, 0)) * NEXT * sp
ext = np.zeros((NEXT, 3, 3))
for i in range(3):
    P0, P2 = K[0, i], apex; P1 = P0 + dirs[i] * NEXT * sp * 0.5
    for j in range(NEXT):
        t = (j + 1) / (NEXT + 1); ext[NEXT - 1 - j, i] = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * P1 + t ** 2 * P2
rails = np.concatenate([[[apex] * 3], ext, K])                              # apex first, then the extension, then the ribs' corners
out = bpy.data.collections.get("GRAF_NERVURI")
for o in [o for o in out.objects if o.name.startswith("sina_")]: bpy.data.objects.remove(o)
cols = {G: (0.1, 0.9, 0.2, 1), B: (0.1, 0.5, 1.0, 1), Y: (1.0, 0.85, 0.1, 1)}
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = c; m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c; return m
light = mat("nervura_noua_rosu_deschis", (0.85, 0.12, 0.10, 1)); nc = bpy.data.collections.new("NERVURI_NOI"); sc.collection.children.link(nc)
# rib thickness: the copied ribs' extent along the row
th = 2.0
for o in [o for o in out.objects if o.name.startswith("nervura_copiata_")][:5]:
    P = np.array([v.co for v in o.data.vertices]); t_ = C[1] - C[0]; t_ /= np.linalg.norm(t_); th = max(th, min(np.ptp(P @ t_), 6.0))
def plate(p, q, r, name, side):
    # the V: two thin strips, yellow->blue and green->blue, as one closed solid of thickness th across the row
    n = np.cross(q - p, r - p); n /= max(np.linalg.norm(n), 1e-9); h = n * th / 2
    V = np.array([p - h, q - h, r - h, p + h, q + h, r + h]); V[:, 0] *= side
    F = [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    if side < 0: F = [f[::-1] for f in F]
    me = bpy.data.meshes.new(name); me.from_pydata((V + [DX, 0, 0]).tolist(), [], F); me.materials.append(light); ob = bpy.data.objects.new(name, me); nc.objects.link(ob)
def rib_src(k):                                                            # copied rib k (side S), world coords without the DX shift
    o = bpy.data.objects["nervura_copiata_%02d_S" % k]; P = np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0]
    return P, [tuple(p.vertices) for p in o.data.polygons]
def frame(c3):                                                             # corners -> origin, 2 in-plane edges, unit normal
    y, b, g = c3[Y], c3[B], c3[G]; n = np.cross(b - y, g - y); return y, b - y, g - y, n / np.linalg.norm(n)
def mapped(k, tgt, scale_n):
    # rib k carried onto the target corners: each point written as corner Y + a*(B-Y) + b*(G-Y) + c*normal in rib k's own
    # corner frame, rebuilt with the target corners (same curvature), its thickness across the row scaled to fill the gap
    P, F = rib_src(k); y, e1, e2, n = frame(K[k]); M = np.stack([e1, e2, n], 1); abc = np.linalg.solve(M, (P - y).T).T
    y2, f1, f2, n2 = frame(tgt); return y2 + abc[:, :1] * f1 + abc[:, 1:2] * f2 + abc[:, 2:3] * n2 * scale_n, F
def add(V, F, name, side):
    V = V.copy(); V[:, 0] *= side; F = F if side > 0 else [f[::-1] for f in F]
    me = bpy.data.meshes.new(name); me.from_pydata((V + [DX, 0, 0]).tolist(), [], F); me.materials.append(light); ob = bpy.data.objects.new(name, me); nc.objects.link(ob)
    for p_ in me.polygons: p_.use_smooth = True
# thickness of a copied rib across the row, and the gap to fill between two copied ribs
def thick(k):
    P, _ = rib_src(k); n = frame(K[k])[3]; return np.ptp((P - K[k][Y]) @ n)
for side in (1, -1):
    for i in range(3):
        cu = bpy.data.curves.new("sina", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.2; s_ = cu.splines.new("POLY"); s_.points.add(len(rails) - 1)
        for k in range(len(rails)): s_.points[k].co = (*(rails[k, i] * [side, 1, 1] + [DX, 0, 0]), 1)
        ob = bpy.data.objects.new("sina_%d%s" % (i + 1, "_S" if side > 0 else "_D"), cu); cu.materials.append(mat("sina_%d" % i, cols[i])); out.objects.link(ob)
    n = 0
    for k in range(len(K) - 1):                                             # between copied ribs k and k+1
        mid = (K[k] + K[k + 1]) / 2; nrm = frame(mid)[3]
        gap = abs(np.dot(K[k + 1].mean(0) - K[k].mean(0), nrm)) - 0.5 * (thick(k) + thick(k + 1))
        tk = thick(k); V, F = mapped(k, mid, max(gap + 1.0, 0.5) / max(tk, 0.1))   # +1 m overlap: it touches both neighbours
        add(V, F, "nervura_noua_%02d%s" % (k, "_S" if side > 0 else "_D"), side); n += 1
    for k in range(NEXT):                                                   # the extension: rib 0's shape, getting smaller to the point
        tgt = ext[k]; nxt = ext[k + 1] if k + 1 < NEXT else K[0]; nrm = frame(tgt)[3]
        gap = abs(np.dot(nxt.mean(0) - tgt.mean(0), nrm)); V, F = mapped(0, tgt, max(gap, 0.5) / max(thick(0), 0.1))
        add(V, F, "nervura_varf_%02d%s" % (k, "_S" if side > 0 else "_D"), side)
print("COMPLETAT: varf la %.0f m in fata primei nervuri; %d nervuri noi (forma nervurilor copiate, latite pana le ating) + %d pe prelungire, pe fiecare parte" % (np.linalg.norm(apex - K[0].mean(0)), n, NEXT))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

# Step 3 of the nacelle: new ribs between copied ribs, as continuations of them. Construction for the new rib between
# copied ribs k and k+1:
#  * rib k's points written in its own corner frame: origin = its point corner (mid of back/front), a and b = coordinates
#    along its two arm-end directions (end1 - point, end2 - point), t = position across its width (0 = back face plane,
#    1 = front face plane, measured along the frame's normal);
#  * rebuilt between two REAL faces: at t = 0 the front face of rib k (its 3 corners), at t = 1 the back face of rib k+1
#    (its 3 corners): p = (1 - t) * (P0 + a (E1_0 - P0) + b (E2_0 - P0)) + t * (P1 + a (E1_1 - P1) + b (E2_1 - P1)).
# So the new rib starts exactly where rib k ends and ends exactly where rib k+1 begins (touching both, full width, the
# slopes on every axis continued from one rib's face to the next) and keeps rib k's curved V shape. Checks printed: the
# gap between the new rib's faces and the neighbours' faces (should be ~0) and the deviation of its corners from the guides.
# Extension (--ext M): ahead of rib 0, M segments along the guides' extensions down to the point where they meet,
# alternating copied-rib red and new-rib red, each one rib 0's shape rebuilt between two consecutive sections (3 corners
# taken on the 3 extension curves), the first section = rib 0's outer face, the last = the meeting point (pointed end).
# Usage: blender -b <step2.blend> --python rib_new.py -- <corners.json> <guides.json> <out.blend> <dx> <k...|all> [--ext M]
import bpy, sys, json, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; CJ, GJ, OUT, DX = a[0], a[1], a[2], float(a[3]); EXT = 0
if "--ext" in a: i_ = a.index("--ext"); EXT = int(a[i_ + 1]); a = a[:i_] + a[i_ + 2:]
KS = list(range(len(json.load(open(CJ))) - 1)) if a[4:] == ["all"] else [int(x) for x in a[4:]]
R = json.load(open(CJ)); Gd = json.load(open(GJ)); sc = bpy.context.scene
def rib(k):
    o = bpy.data.objects["nervura_copiata_%02d_S" % k]; return np.array([o.matrix_world @ v.co for v in o.data.vertices]) - [DX, 0, 0], [tuple(p.vertices) for p in o.data.polygons]
def face(k, f): c = np.array(R[k][f]); return c[1], c[0], c[2]                # point, end1, end2
def frame(k):
    pb, e1b, e2b = face(k, "spate"); pf, e1f, e2f = face(k, "fata"); p, e1, e2 = (pb + pf) / 2, (e1b + e1f) / 2, (e2b + e2f) / 2
    u, v = e1 - p, e2 - p; n = np.cross(u, v); n /= np.linalg.norm(n); hb, hf = np.dot(pb - p, n), np.dot(pf - p, n)
    if hf < hb: n, hb, hf = -n, -hb, -hf
    return p, u, v, n, hb, hf
def coords(k, P):
    p, u, v, n, hb, hf = frame(k); ab = np.linalg.solve(np.stack([u, v, n], 1), (P - p).T).T
    return ab[:, 0], ab[:, 1], (ab[:, 2] - hb) / (hf - hb)
def rebuild(A_, B_, t, F0, F1):
    (p0, e10, e20), (p1, e11, e21) = F0, F1
    s0 = p0 + A_[:, None] * (e10 - p0) + B_[:, None] * (e20 - p0); s1 = p1 + A_[:, None] * (e11 - p1) + B_[:, None] * (e21 - p1)
    return s0 * (1 - t[:, None]) + s1 * t[:, None]
col = bpy.data.collections.get("NERVURI_NOI") or bpy.data.collections.new("NERVURI_NOI")
if col.name not in sc.collection.children: sc.collection.children.link(col)
m = bpy.data.materials.get("nervura_noua_rosu_deschis") or bpy.data.materials.new("nervura_noua_rosu_deschis")
m.diffuse_color = (0.85, 0.12, 0.10, 1); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.85, 0.12, 0.10, 1)
def bez(c, t): c = np.array(c); t = np.atleast_1d(t)[:, None]; return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
guides = [bez(r["control"], np.linspace(0, 1, 4000)) for r in Gd["rails"]]       # end1 (green), point (blue), end2 (yellow)
for k in KS:
    P, F = rib(k); A_, B_, t = coords(k, P)
    F0 = face(k, "fata"); F1 = face(k + 1, "spate"); V = rebuild(A_, B_, t, F0, F1)
    for side in (1, -1):
        W = V.copy(); W[:, 0] *= side; FF = F if side > 0 else [f[::-1] for f in F]
        me = bpy.data.meshes.new("n"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], FF); me.materials.append(m)
        for p_ in me.polygons: p_.use_smooth = True
        ob = bpy.data.objects.new("nervura_noua_%02d%s" % (k, "_S" if side > 0 else "_D"), me); col.objects.link(ob)
    # checks: the new rib's back face vs rib k's front face, its front face vs rib k+1's back face (corner distances)
    nb = rebuild(np.array([0.0, 1, 0]), np.array([0.0, 0, 1]), np.zeros(3), F0, F1); nf = rebuild(np.array([0.0, 1, 0]), np.array([0.0, 0, 1]), np.ones(3), F0, F1)
    g1 = max(np.linalg.norm(nb[i] - np.array(F0)[i]) for i in range(3)); g2 = max(np.linalg.norm(nf[i] - np.array(F1)[i]) for i in range(3))
    mid = (nb + nf) / 2; gd = [np.min(np.linalg.norm(guides[j] - mid[[1, 0, 2][j]], axis=1)) for j in range(3)]
    width = np.linalg.norm(np.array(F1).mean(0) - np.array(F0).mean(0)); thk = np.linalg.norm(np.array(face(k, "fata")).mean(0) - np.array(face(k, "spate")).mean(0))
    print("NERVURA NOUA %02d (intre %d si %d): latime %.1f m (nervura copiata %.1f m); atinge nervura %d: %.2f m, nervura %d: %.2f m; colturi fata de ghidaje m: capat1 %.1f varf %.1f capat2 %.1f"
          % (k, k, k + 1, width, thk, k, g1, k + 1, g2, gd[0], gd[1], gd[2]))
if EXT:
    dark = bpy.data.materials.get("nervura_copiata") or m
    P, F = rib(0); c0 = P.mean(0); c1 = rib(1)[0].mean(0)
    fb, ff = np.array(face(0, "spate")), np.array(face(0, "fata"))
    outer = ("spate", "fata")[int(np.linalg.norm(ff.mean(0) - c1) > np.linalg.norm(fb.mean(0) - c1))]     # rib 0's face away from rib 1
    A_, B_, t = coords(0, P)
    if outer == "fata": t = 1 - t                                         # t = 0 at the face toward rib 1, 1 at the outer face
    ext = [np.array(r["extension_control"]) for r in Gd["rails"]]      # per rail (end1, point, end2): rail start -> meeting point
    sections = [face(0, outer)]
    for j in range(1, EXT + 1):
        u = j / EXT; e = [bez(ext[i], u)[0] for i in range(3)]; sections.append((e[1], e[0], e[2]))   # (point, end1, end2)
    # the outer face of rib 0 is ~half a rib behind the extension curves' start: the first section is the real face
    for j in range(EXT):
        V = rebuild(A_, B_, t, sections[j], sections[j + 1]); mt = m if j % 2 == 0 else dark
        for side in (1, -1):
            W = V.copy(); W[:, 0] *= side; FF = F if side > 0 else [f[::-1] for f in F]
            me = bpy.data.meshes.new("n"); me.from_pydata((W + [DX, 0, 0]).tolist(), [], FF); me.materials.append(mt)
            for p_ in me.polygons: p_.use_smooth = True
            ob = bpy.data.objects.new("nervura_varf_%02d%s" % (j, "_S" if side > 0 else "_D"), me); col.objects.link(ob)
    print("PRELUNGIRE: %d segmente pana la varful comun (fata exterioara a nervurii 0 = %s), lungime %.0f m" % (EXT, outer, np.linalg.norm(np.array(sections[-1]).mean(0) - np.array(sections[0]).mean(0))))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

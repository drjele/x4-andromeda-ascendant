# The red nacelle rebuilt from its own ribs, beside the untouched reference ship: the original ribs of one side copied
# exactly (dark red); between every two neighbouring ribs a new rib (lighter red) that bridges them: lofted with straight
# walls from the real outline of one rib's facing side to the next rib's, so it touches both and its slopes on every axis
# follow theirs; the row ends in a final triangular rib drawn to a point (the whole ends sharp); everything mirrored to the other side (exact symmetry). The reference ship is not modified: the new ribs go into
# their own collection, shifted beside the ship by DX.
# Usage: blender -b <ship.blend> --python ribs_between.py -- <out.blend> <dx>
import bpy, bmesh, sys, numpy as np
from mathutils import Matrix, Vector, Quaternion
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DX = a[0], float(a[1]); sc = bpy.context.scene
imgs = {}
def red_share(o):
    me = o.data
    if not me.materials or not me.uv_layers: return 0
    uv = me.uv_layers.active.data; n = 0
    for p in me.polygons:
        m = me.materials[p.material_index]; tl = [x for x in m.node_tree.nodes if x.type == "TEX_IMAGE"] if m and m.node_tree else []
        if not tl or not tl[0].image: return 0
        t = tl[0].image
        if t.name not in imgs: imgs[t.name] = np.array(t.pixels[:], np.float32).reshape(t.size[1], t.size[0], t.channels)
        A = imgs[t.name]; u, v = uv[p.loop_start].uv; c = A[int((v % 1) * (A.shape[0] - 1)), int((u % 1) * (A.shape[1] - 1)), :3]
        n += c[0] > 0.25 and c[0] > 1.8 * max(c[1], c[2])
    return n / len(me.polygons)
def inbk(o): return any(c.name == "BACKUP_sterse" for c in o.users_collection)
ribs = [o for o in sc.objects if o.type == "MESH" and not inbk(o) and o.name.endswith("_S") and len(o.data.polygons) < 400 and red_share(o) > 0.95]
def world(o): return np.array([o.matrix_world @ v.co for v in o.data.vertices])
def frame(P):
    c = P.mean(0); ev, E = np.linalg.eigh(np.cov((P - c).T)); E = E[:, ::-1]
    if np.linalg.det(E) < 0: E[:, 2] *= -1
    return c, E
data = [(o, world(o)) for o in ribs]
C = np.array([P.mean(0) for _, P in data]); order = [int(np.argmax(C[:, 1]))]; left = set(range(len(C))) - set(order)
while left:
    j = min(left, key=lambda i: np.linalg.norm(C[i] - C[order[-1]])); order.append(j); left.remove(j)
data = [data[i] for i in order]
out = bpy.data.collections.new("NACELA_NOUA"); sc.collection.children.link(out)
def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.45; m.diffuse_color = (*rgb, 1); return m
dark, light = mat("nervura_rosu_inchis", (0.30, 0.02, 0.03)), mat("nervura_rosu_deschis", (0.80, 0.08, 0.07))
def add(P, faces, name, m, mirror):
    me = bpy.data.meshes.new(name); V = P.copy()
    if mirror: V[:, 0] *= -1; faces = [f[::-1] for f in faces]
    me.from_pydata((V + [DX, 0, 0]).tolist(), [], faces); me.materials.append(m); ob = bpy.data.objects.new(name, me); out.objects.link(ob)
    for p in me.polygons: p.use_smooth = False
faces_of = lambda o: [tuple(p.vertices) for p in o.data.polygons]
# frames carried along the row (tangent from rib to rib, U/V transported: no twist)
C = np.array([P.mean(0) for _, P in data]); T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
U = [np.cross(T[0], [0, 0, 1.0])]; U[0] /= np.linalg.norm(U[0])
for k in range(1, len(C)):
    u = U[-1] - T[k] * np.dot(U[-1], T[k]); U.append(u / np.linalg.norm(u))
U = np.array(U); V = np.cross(T, U); NA = 40; TH = np.linspace(-np.pi, np.pi, NA, endpoint=False)
def hull2d(pts):                                                          # convex hull (monotone chain; Blender has no scipy)
    P = sorted(set(map(tuple, np.round(pts, 4)))); 
    def cross(o, a_, b_): return (a_[0] - o[0]) * (b_[1] - o[1]) - (a_[1] - o[1]) * (b_[0] - o[0])
    lo, up = [], []
    for p_ in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p_) <= 0: lo.pop()
        lo.append(p_)
    for p_ in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p_) <= 0: up.pop()
        up.append(p_)
    return np.array(lo[:-1] + up[:-1])
def face(k, front):
    # the real outline of rib k's face toward its next (front) or previous (back) neighbour: its points in that slice of the
    # rib, convex hull in the plane across the row, radius per angle from the rib's centre, placed at the face's depth
    P = data[k][1]; s_ = (P - C[k]) @ T[k]; th = np.ptp(s_); sel = s_ > s_.max() - 0.3 * th if front else s_ < s_.min() + 0.3 * th
    q = P[sel] - C[k]; x, y = q @ U[k], q @ V[k]; H_ = hull2d(np.stack([x, y], 1)); hx, hy = H_[:, 0], H_[:, 1]
    an = np.arctan2(hy, hx); o = np.argsort(an); R = np.interp(TH, an[o], np.hypot(hx, hy)[o], period=2 * np.pi)
    d = s_.max() if front else s_.min()
    return C[k] + d * T[k] + R[:, None] * (np.cos(TH)[:, None] * U[k] + np.sin(TH)[:, None] * V[k])
def solid(rings, apex=None):
    # rings lofted with straight walls (flat slopes between the outlines), closed at both ends (or drawn to a point)
    V_ = np.vstack(rings); F = []; n = len(rings)
    for r in range(n - 1):
        for i in range(NA): a_, b_ = r * NA + i, r * NA + (i + 1) % NA; F.append((a_, b_, b_ + NA, a_ + NA))
    F.append(tuple(range(NA))[::-1])
    if apex is None: F.append(tuple((n - 1) * NA + i for i in range(NA)))
    else:
        V_ = np.vstack([V_, apex]); ai = len(V_) - 1; F += [((n - 1) * NA + i, (n - 1) * NA + (i + 1) % NA, ai) for i in range(NA)]
    return V_, F
n_new = 0
for k, (o, P) in enumerate(data):
    for mir in (False, True): add(P, faces_of(o), "nervura_%02d%s" % (k, "_D" if mir else "_S"), dark, mir)
    if k + 1 < len(data):                                                  # the bridge: touches both ribs, walls follow their outlines
        Vb, Fb = solid([face(k, True), face(k + 1, False)])
        for mir in (False, True): add(Vb, Fb, "nervura_%02d_intre%s" % (k, "_D" if mir else "_S"), light, mir)
        n_new += 1
# the final rib: a triangle (pyramid) from the first rib's outer face to a point ahead, so the whole ends sharp
sp = np.median(np.linalg.norm(np.diff(C, axis=0), axis=1)); f0 = face(0, False); apex = f0.mean(0) - T[0] * 3 * sp
Vf, Ff = solid([f0], apex)
for mir in (False, True): add(Vf, Ff, "nervura_finala_triunghi%s" % ("_D" if mir else "_S"), dark, mir)
print("NERVURI: %d copiate (roșu închis) + %d noi intre ele (roșu deschis), pe fiecare parte" % (len(data), n_new))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

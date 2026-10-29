# The rim rebuilt from its confirmed guides (asked: the old rim copy is no longer needed - rebuild the rim from the guide).
# Between the outer and the inner outline (ghid_rama.py): every outer point paired with the inner point its inward normal
# reaches (nearest, kept in order), K rows across; top flat at z ZP, bottom = the guide's section (quarter ellipse from the
# outer edge at ZP down to ZP - H at the inner edge), vertical inner wall; one closed piece. Replaces OBJ (keeps its location,
# material and collection) and removes the named leftovers.
# Usage: blender -b <in> --python rama_din_ghidaj.py -- <out.blend> <ghid_rama.npz> <OBJ> [remove ...] ; env RK=12
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, G, NAME = a[0], np.load(a[1]), a[2]; K = int(os.environ.get("RK", "12"))
E = G["contur_rama_exterior"]; Iz = G["contur_rama_interior"]; Ij = G["contur_rama_interior_jos"]; ZP = float(E[0, 2]); H = ZP - float(Ij[0, 2])
def resample(p, step=1.0):
    c = np.vstack([p, p[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]; u = np.arange(0, d[-1], step)
    return np.c_[np.interp(u, d, c[:, 0]), np.interp(u, d, c[:, 1])]
O = resample(E[:, :2]); Ii = resample(Iz[:, :2], 0.5); N, M = len(O), len(Ii)
tg = np.roll(O, -1, 0) - np.roll(O, 1, 0); tg /= np.linalg.norm(tg, axis=1)[:, None]; nin = np.c_[tg[:, 1], -tg[:, 0]]   # clockwise: inward = right
RW = float(np.median(np.min(np.linalg.norm(O[:, None, :] - Ii[None, ::8, :], axis=2), axis=1)))
tgt = O + RW * nin; idx = np.argmin(np.linalg.norm(tgt[:, None, :] - Ii[None, :, :], axis=2), axis=1)
t = np.unwrap(idx * 2 * np.pi / M) * M / (2 * np.pi)                                # position along the inner outline, unwrapped
t = np.maximum.accumulate(t - t[0]); keep = np.r_[True, np.diff(t) > 0]             # in order; where it holds, spread evenly
ii = np.arange(N); t = np.interp(ii, np.r_[ii[keep], N], np.r_[t[keep], M])         # closes on itself after one turn
tf = (t + idx[0]) % M; i0 = np.floor(tf).astype(int); f_ = (tf - i0)[:, None]; P_in = Ii[i0] * (1 - f_) + Ii[(i0 + 1) % M] * f_
s = np.linspace(0, 1, K + 1); zb = ZP - H * np.sqrt(np.clip(1 - (1 - s) ** 2, 0, 1))
bm = bmesh.new()
bot = [[bm.verts.new((*(O[i] + (P_in[i] - O[i]) * s[k]), zb[k])) for k in range(K + 1)] for i in range(N)]
top = [[bot[i][0]] + [bm.verts.new((*(O[i] + (P_in[i] - O[i]) * s[k]), ZP)) for k in range(1, K + 1)] for i in range(N)]
for i in range(N):
    j = (i + 1) % N
    for k in range(K):
        bm.faces.new((bot[i][k], bot[j][k], bot[j][k + 1], bot[i][k + 1]))          # bottom
        bm.faces.new((top[i][k], top[i][k + 1], top[j][k + 1], top[j][k]))          # top
    bm.faces.new((bot[i][K], bot[j][K], top[j][K], top[i][K]))                      # inner wall
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.triangulate(bm, faces=bm.faces)
nm = sum(1 for e in bm.edges if not e.is_manifold)
old = bpy.data.objects[NAME]; loc = old.location.copy(); mats = list(old.data.materials); cols = list(old.users_collection)
bpy.data.objects.remove(old)
me = bpy.data.meshes.new(NAME); bm.to_mesh(me); bm.free()
for m in mats: me.materials.append(m)
o = bpy.data.objects.new(NAME, me); o.location = loc
for c in cols: c.objects.link(o)
for n in a[3:]:
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
print("RAMA DIN GHIDAJ: %d puncte pe contur, %d randuri, latime %.1f m, inaltime la interior %.1f m; %d fete, muchii ne-manifold %d; scoase: %s" % (
    N, K, RW, H, len(me.polygons), nm, ", ".join(a[3:]) or "-"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

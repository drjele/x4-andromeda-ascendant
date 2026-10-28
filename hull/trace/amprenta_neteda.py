# The reference's imprint on the body smoothed at a chosen scale (asked: the copy without holes is full of ribs - smooth
# it): imprint = laid-on piece minus the body (same mesh, corp_pe_ref.py); averaged on a 3D grid (CELL m) and blurred
# with a gaussian of SIGMA m (separable, numpy), sampled back at every vertex (trilinear) and added to the body again -
# ribs narrower than about SIGMA go, the reference's large shape stays. One copy per SIGMA, side by side to the right
# (every STEP m), named <laid>_s<SIGMA>; distance to the laid piece and roughness reported.
# Usage: blender -b <f.blend> --python amprenta_neteda.py -- <out.blend> <body> <laid> <sigma,...> [cell] [step]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BODY, LAID = a[0], a[1], a[2]; SG = [float(v) for v in a[3].split(",")]
CELL = float(a[4]) if len(a) > 4 else 4.0; STEP = float(a[5]) if len(a) > 5 else 2400.0
b, l = bpy.data.objects[BODY], bpy.data.objects[LAID]
get = lambda o: (lambda v: (o.data.vertices.foreach_get("co", v), v.reshape(-1, 3))[1])(np.zeros(len(o.data.vertices) * 3))
V0, VL = get(b), get(l); D = VL - V0
lo = V0.min(0) - 3 * max(SG); sh = np.ceil((V0.max(0) + 3 * max(SG) - lo) / CELL).astype(int) + 2
idx = ((V0 - lo) / CELL).astype(int); flat = np.ravel_multi_index(idx.T, sh)
S = np.zeros((np.prod(sh), 3), np.float32); W = np.zeros(np.prod(sh), np.float32)
np.add.at(S, flat, D.astype(np.float32)); np.add.at(W, flat, 1.0)
def blur(G, s):
    n = int(3 * s / CELL) + 1; k = np.exp(-0.5 * (np.arange(-n, n + 1) * CELL / s) ** 2); k /= k.sum()
    for ax in range(3): G = np.apply_along_axis(lambda x: np.convolve(x, k, "same"), ax, G)
    return G
def sample(G, P):                                                      # trilinear
    f = (P - lo) / CELL - 0.5; i0 = np.floor(f).astype(int); t = f - i0; out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (t[:, 0] if dx else 1 - t[:, 0]) * (t[:, 1] if dy else 1 - t[:, 1]) * (t[:, 2] if dz else 1 - t[:, 2])
                ii = np.clip(i0 + [dx, dy, dz], 0, np.array(sh) - 1); out = out + w[..., None] * G[ii[:, 0], ii[:, 1], ii[:, 2]] if G.ndim == 4 else out + w * G[ii[:, 0], ii[:, 1], ii[:, 2]]
    return out
def rough(V):
    m = bpy.data.meshes.new("t"); m.from_pydata(V.tolist(), [], [list(p.vertices) for p in b.data.polygons]); bm = bmesh.new(); bm.from_mesh(m)
    ang = np.degrees([x.calc_face_angle(0) for x in bm.edges if len(x.link_faces) == 2]); bm.free(); bpy.data.meshes.remove(m); return np.percentile(ang, 95)
Sg, Wg = S.reshape(*sh, 3), W.reshape(sh)
print("AMPRENTA: %d varfuri, mutare medie %.1f m; asperitate corp %.1f, lipit %.1f grade (95%%)" % (len(V0), np.linalg.norm(D, axis=1).mean(), rough(V0), rough(VL)))
for k, s in enumerate(SG):
    Bs = np.stack([blur(Sg[..., c].astype(np.float64), s) for c in range(3)], -1); Bw = blur(Wg.astype(np.float64), s)
    Ds = sample(Bs, V0) / np.maximum(sample(Bw, V0), 1e-9)[:, None]; V = V0 + Ds
    c = l.copy(); c.data = l.data.copy(); c.name = "%s_s%g" % (LAID, s); c.data.vertices.foreach_set("co", V.ravel()); c.data.update()
    for col in l.users_collection: col.objects.link(c)
    c.location.x += STEP * (k + 1); d = np.linalg.norm(V - VL, axis=1)
    print("SIGMA %4.1f m: fata de piesa lipita medie %.2f / 95%% %.2f / max %.2f m; asperitate 95%% %.1f grade" % (s, d.mean(), np.percentile(d, 95), d.max(), rough(V)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

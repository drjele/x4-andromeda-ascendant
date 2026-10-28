# The front arm's end widened into a funnel, as drawn from above: the arm's outer line keeps its curve (circle fit) until it
# meets the nacelle's end line, and the arm's old rounded end is carried onto that new outline by a smooth (harmonic)
# displacement in the top view, heights kept; the nacelle and the rest of the arm stay where they are. Points that land
# on or past the nacelle's end plane are put exactly on it. Built on _D, _S is its mirror (same vertex order).
# Usage: blender -b <arm.blend> --python arm_funnel_end.py -- <deplasare.npz> <out.blend>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; G = np.load(a[0]); OUT = a[1]
U, s, cx, cy, c0 = G["U"], float(G["s"]), float(G["cx"]), float(G["cy"]), float(G["c0"])
MX = -1700.0; n = np.array([-0.975, 0.219, -0.027]); n /= np.linalg.norm(n); p0 = np.array([-1568., 216., 288.])
D, Sd = bpy.data.objects["brat_fata_D"], bpy.data.objects["brat_fata_S"]
def co(o):
    v = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", v); return v.reshape(-1, 3)
assert np.allclose(np.array(D.matrix_world), np.eye(4)) and np.allclose(np.array(Sd.matrix_world), np.eye(4))
P, Q = co(D), co(Sd); M_ = P.copy(); M_[:, 0] = 2 * MX - M_[:, 0]
print("simetrie inainte: abatere max %.4f m" % np.abs(M_ - Q).max())
bk = bpy.data.collections["BRAT_PIESE"]
for o in (D, Sd):
    k = o.copy(); k.data = o.data.copy(); k.name = o.name + "_plan"; bk.objects.link(k)
px = c0 + (P[:, 0] - cx) / s; py = c0 - (P[:, 1] - cy) / s
h, w = U.shape[:2]; ok = (px >= 0) & (px < w - 1) & (py >= 0) & (py < h - 1)
x0, y0 = np.floor(px[ok]).astype(int), np.floor(py[ok]).astype(int); fx, fy = (px[ok] - x0)[:, None], (py[ok] - y0)[:, None]
d = U[y0, x0] * (1 - fx) * (1 - fy) + U[y0, x0 + 1] * fx * (1 - fy) + U[y0 + 1, x0] * (1 - fx) * fy + U[y0 + 1, x0 + 1] * fx * fy
N = P.copy(); N[ok, 0] += d[:, 0] * s; N[ok, 1] -= d[:, 1] * s
mv = np.linalg.norm(N - P, axis=1) > 1e-6
dist = (N - p0) @ n; hz = n.copy(); hz[2] = 0; hz /= np.linalg.norm(hz)
snap = mv & (dist > 0); N[snap] -= (dist[snap] / (hz @ n))[:, None] * hz      # moved horizontally onto the plane
print("varfuri mutate %d, mutare max %.1f m; puse pe planul capatului %d; dincolo de plan dupa: %d" % (mv.sum(), np.linalg.norm(N - P, axis=1).max(), snap.sum(), ((N - p0) @ n > 0.01).sum()))
D.data.vertices.foreach_set("co", N.ravel()); D.data.update()
Mm = N.copy(); Mm[:, 0] = 2 * MX - Mm[:, 0]; Sd.data.vertices.foreach_set("co", Mm.ravel()); Sd.data.update()
bpy.context.view_layer.layer_collection.children["BRAT_PIESE"].exclude = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

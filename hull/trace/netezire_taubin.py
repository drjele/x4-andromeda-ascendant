# Smoothing without shrinking (asked: the copy without holes is full of ribs - smooth it): Taubin's lambda / mu passes
# (one neighbour-average step in, one slightly larger step back out) over the whole mesh, vectorised; narrow ribs and
# steps go, the overall size stays. One copy per strength (number of passes), placed side by side to the right of the
# source (every STEP m), named <src>_net<N>; for each: distance to the source (mean / 95 % / max) and how rough it still
# is (95 % of the angles between neighbour faces). Usage: blender -b <f.blend> --python netezire_taubin.py -- <out.blend>
#        <object> <passes,...> [step]
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SRC = a[0], a[1]; NS = [int(v) for v in a[2].split(",")]; STEP = float(a[3]) if len(a) > 3 else 2400.0
LAM, MU = 0.5, -0.53
src = bpy.data.objects[SRC]; me = src.data
v0 = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", v0); v0 = v0.reshape(-1, 3)
e = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get("vertices", e); e = e.reshape(-1, 2)
deg = np.bincount(e.ravel(), minlength=len(v0)).astype(float)[:, None]
def avg(V):
    S = np.zeros_like(V); np.add.at(S, e[:, 0], V[e[:, 1]]); np.add.at(S, e[:, 1], V[e[:, 0]]); return S / np.maximum(deg, 1)
def rough(V):
    o_ = bpy.data.meshes.new("t"); o_.from_pydata(V.tolist(), [], [list(p.vertices) for p in me.polygons]); bm = bmesh.new(); bm.from_mesh(o_)
    ang = np.degrees([x.calc_face_angle(0) for x in bm.edges if len(x.link_faces) == 2]); bm.free(); bpy.data.meshes.remove(o_); return np.percentile(ang, 95)
onx = np.abs(v0[:, 0] - (v0[:, 0].max() + v0[:, 0].min()) / 2) < 1e-3     # vertices on the middle stay on it (symmetry)
print("SURSA %s: %d varfuri, asperitate 95%% %.1f grade" % (SRC, len(v0), rough(v0)))
V = v0.copy(); done = 0
for k, N in enumerate(sorted(NS)):
    while done < N:
        V = V + LAM * (avg(V) - V); V = V + MU * (avg(V) - V); done += 1
    V[onx, 0] = v0[onx, 0]
    d = np.linalg.norm(V - v0, axis=1)
    c = src.copy(); c.data = me.copy(); c.name = "%s_net%d" % (SRC, N); c.data.vertices.foreach_set("co", V.ravel())
    for col in src.users_collection: col.objects.link(c)
    c.location.x += STEP * (k + 1); c.data.update()
    print("NET %4d treceri: abatere fata de sursa medie %.2f / 95%% %.2f / max %.2f m; asperitate 95%% %.1f grade" % (N, d.mean(), np.percentile(d, 95), d.max(), rough(V)))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

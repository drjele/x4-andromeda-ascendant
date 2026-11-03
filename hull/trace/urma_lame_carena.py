# Where the blades and their columns go through at_PS_carena over the whole animation (asked: at_PS_carena gets doors / segments in
# front of the blades, sliding inwards towards its middle axis): blade surface points (vertices, each face's centre, every frame)
# and column side points that lie inside the carena's closed volume (ray parity, two directions agree), S side, per set; saved as points (x, y, z, frame) for the
# door outline. Usage: blender -b <scene> --python urma_lame_carena.py -- <out.npz>   env FS=1 (frame step)
import bpy, sys, os, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree as BV
OUT = sys.argv[sys.argv.index("--") + 1]; FS = int(os.environ.get("FS", 1)); sc = bpy.context.scene
car = bpy.data.objects["at_PS_carena"]; mw = car.matrix_world; me = car.data
T = BV.FromPolygons([mw @ v.co for v in me.vertices], [list(p.vertices) for p in me.polygons])
lo = np.array([min((mw @ v.co)[i] for v in me.vertices) for i in range(3)]); hi = np.array([max((mw @ v.co)[i] for v in me.vertices) for i in range(3)])
def par(p, d):                                                            # number of crossings along d (ray parity)
    n, q = 0, p.copy()
    while True:
        r = T.ray_cast(q, d)
        if r[0] is None: return n
        n += 1; q = r[0] + d * 1e-3
def inside(p): return par(p, Vector((0, 0, 1))) % 2 == 1 and par(p, Vector((0.6, 0.3, -0.74)).normalized()) % 2 == 1
SETS = {"fata": ["at_lama_007_S", "at_lama_008_S"], "spate": ["at_lama_009_S", "at_lama_010_S", "at_lama_013_S", "at_lama_014_S"]}
COLS = {"fata": "at_spinare_fata_S", "spate": "at_spinare_spate_S"}
loc = {}
for s, obs in SETS.items():
    for n in obs:
        m = bpy.data.objects[n].data; P = [v.co.copy() for v in m.vertices] + [p.center.copy() for p in m.polygons]
        for e in m.edges:
            a, b = m.vertices[e.vertices[0]].co, m.vertices[e.vertices[1]].co; k = int((a - b).length // 1.0)
            P += [a.lerp(b, (j + 1) / (k + 1)) for j in range(k)]
        loc[n] = np.array([tuple(p) for p in P])
ring = np.array([(6 * math.cos(t), 6 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
out = {s: [] for s in SETS}
for f in range(sc.frame_start, sc.frame_end + 1, FS):
    sc.frame_set(f)
    for s, obs in SETS.items():
        for n in obs:
            M = np.array(bpy.data.objects[n].matrix_world); W = loc[n] @ M[:3, :3].T + M[:3, 3]
            k = np.all((W >= lo - 1) & (W <= hi + 1), axis=1)
            for p in W[k]:
                if inside(Vector(p)): out[s].append((*p, f))
        c = bpy.data.objects[COLS[s]]; top = c.matrix_world.translation; L = c.matrix_world.to_scale().z
        for z in np.arange(top.z - L, top.z, 1.0):
            for dx, dy in ring:
                p = Vector((top.x + dx, top.y + dy, z))
                if lo[2] - 1 <= z <= hi[2] + 1 and inside(p): out[s].append((*p, f))
for s in out:
    A = np.array(out[s]); A[:, 0] -= mw.translation.x
    print("URMA %s: %d puncte in carenă, x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f, cadre %d..%d" % (s, len(A), A[:, 0].min(), A[:, 0].max(), A[:, 1].min(), A[:, 1].max(), A[:, 2].min(), A[:, 2].max(), A[:, 3].min(), A[:, 3].max()))
    out[s] = A
np.savez(OUT, **out)

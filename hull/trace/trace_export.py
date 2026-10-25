# Export the user's traces (one annotation layer per part) and the parts, both flattened onto each traced view's plane (metres, camera right/up),
# for compare_trace.py. Usage: blender -b --python trace_export.py -- <trace.blend> <out.npz>
import bpy, sys, numpy as np
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]; SRC, OUT = args
CAMS = {"top": (0, 0, 6000), "bottom": (0, 0, -6000), "side": (-6000, 0, 0), "front": (0, 6000, 0), "back": (0, -6000, 0)}
bpy.ops.wm.open_mainfile(filepath=SRC); sc = bpy.context.scene; gp = sc.grease_pencil; data = {}
def basis(view):
    loc = Vector(CAMS[view]); rot = (-loc).to_track_quat("-Z", "Y").to_matrix(); return np.array([rot.col[0], rot.col[1]])
def view_of(pts):
    # annotation strokes lie on the plane through the 3D cursor (origin) facing the view: z = 0 from above, x = 0 from the side
    spread = pts.max(0) - pts.min(0); axis = int(np.argmin(spread))
    return {2: "top", 0: "side", 1: "front"}[axis] if spread[axis] < 0.5 else None
views = set(); n = 0
for lay in gp.layers if gp else []:
    for fr in lay.frames:
        for st in fr.strokes:
            if len(st.points) < 2: continue
            pts = np.array([p.co for p in st.points]); view = view_of(pts)
            if view is None: print("SKIP stroke not flat", lay.info); continue
            data[f"stroke|{view}|{lay.info}|{n}"] = (pts @ basis(view).T).astype(np.float32); views.add(view); n += 1
for view in views:
    B = basis(view)
    for o in bpy.data.collections["nava"].objects:
        me = o.data; me.calc_loop_triangles(); M = np.array(o.matrix_world)
        v = np.array([x.co for x in me.vertices]); v = v @ M[:3, :3].T + M[:3, 3]
        data[f"verts|{view}|{o.name}"] = (v @ B.T).astype(np.float32)
        data[f"tris|{view}|{o.name}"] = np.array([t.vertices for t in me.loop_triangles], np.int32)
np.savez_compressed(OUT, **data); print("EXPORT", sorted(views), n)

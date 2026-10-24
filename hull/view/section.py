# Cross-sections of the built pieces: every mesh edge cut by a plane, written as 2D segments per part.
# Usage: blender -b --python section.py -- <out.json> <name>:<axis x|y|z>:<value> ...  (then section_draw.py)
import bpy, json, sys
import numpy as np
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
args = sys.argv[sys.argv.index("--") + 1:]; OUT = args[0]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]; out = {}
meshes = {}
for o in sc.objects:
    if o.type != "MESH" or o.name == "source_edited": continue
    me = o.data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    E = np.empty(len(me.edges) * 2, int); me.edges.foreach_get("vertices", E); meshes[o.name] = (V, E.reshape(-1, 2))
for spec in args[1:]:
    name, axis, val = spec.split(":"); ax = "xyz".index(axis); val = float(val); keep = [i for i in range(3) if i != ax]; segs = {}
    for on, (V, E) in meshes.items():
        d = V[:, ax] - val; a, b = E[:, 0], E[:, 1]; m = (d[a] * d[b]) < 0
        if not m.any(): continue
        t = d[a[m]] / (d[a[m]] - d[b[m]]); P = V[a[m]] + (V[b[m]] - V[a[m]]) * t[:, None]
        segs[on] = P[:, keep].round(2).tolist()
    out[name] = {"axis": axis, "value": val, "points": segs}
json.dump(out, open(OUT, "w")); print("SECTIONS", list(out))

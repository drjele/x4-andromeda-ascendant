# Contacts over the whole animation on a block of the board (asked: nothing through anything): the moving pieces (blades, hinges,
# carena doors, arm doors) against every other piece and each other, S and D, triangle overlaps per pair, frame step FS plus the key
# frames. Usage: blender -b <scene> --python contacte_ansamblu.py -- <colectie> <prefix>   env FS=2
import bpy, sys, os
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; C, PR = a[0], a[1]; FS = int(os.environ.get("FS", 2)); sc = bpy.context.scene
obs = [o for o in bpy.data.collections[C].objects if o.type == "MESH"]
mov = [o for o in obs if o.name.startswith((PR + "lama_", PR + "spinare_", PR + "usa_"))]; fix = [o for o in obs if o not in mov]
def bvw(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); w = o.matrix_world; r = BV.FromPolygons([w @ v.co for v in m.vertices], [list(p.vertices) for p in m.polygons]); e.to_mesh_clear(); return r
TF = {o.name: bvw(o) for o in fix}; res = {}
SIB = lambda n: n.startswith((PR + "lama_", PR + "spinare_"))
for f in sorted(set(range(1, sc.frame_end + 1, FS)) | {6, 9, 18, 25, 44, 53, 56, 68, 101, 106, 109, 118, 125, 140, 144, 149, 152, 168}):
    sc.frame_set(f); TM = {o.name: bvw(o) for o in mov}; names = list(TM)
    for i, n in enumerate(names):
        for h, t in TF.items():
            k = len(TM[n].overlap(t))
            if k: res.setdefault((n, h), []).append((f, k))
        for m in names[i + 1:]:
            if n[-1] != m[-1]: continue
            if "spinare" in n + m and "lama" in n + m and ("fata" in n + m or "spate" in n + m): continue   # a hinge holds its own blades
            if SIB(n) and SIB(m): continue
            k = len(TM[n].overlap(TM[m]))
            if k: res.setdefault((n, m), []).append((f, k))
for (n, h), L in sorted(res.items()):
    fr = [f for f, _ in L]; print("CONTACT %s x %s: cadre %d..%d (%d), max %d" % (n, h, min(fr), max(fr), len(fr), max(k for _, k in L)))
print("CONTACT gata, perechi: %d, %d mobile x %d fixe" % (len(res), len(mov), len(fix)))

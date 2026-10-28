# The new body laid onto the reference (asked: make the body like R002 169_C, only without holes): a copy of the exploded
# new body moved onto the exploded reference; each vertex projected along its normal (both ways) onto the reference
# surface when that lies within LIM m - there it takes the reference's shape; where the reference has a hole (no hit)
# the body's own smooth surface stays and covers it. The moves blurred over the mesh (BLUR passes of neighbour averages)
# only near the hole borders, so the patches meet the reference without a step. Placed back where the new piece is (that
# one hidden), name piesa_169_C_pe_ref. Usage: blender -b <f.blend> --python corp_pe_ref.py -- <out.blend> [lim] [blur]
import bpy, bmesh, sys, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; LIM = float(a[1]) if len(a) > 1 else 12.0; BLUR = int(a[2]) if len(a) > 2 else 8
er, en = bpy.data.objects["expl_R002 169_C"], bpy.data.objects["expl_piesa_comp_169_C"]
on, orr = bpy.data.objects["piesa_comp_169_C"], bpy.data.objects["R002 169_C"]
bm_r = bmesh.new(); bm_r.from_mesh(er.data); bm_r.transform(er.matrix_world); tree = BVHTree.FromBMesh(bm_r)
cen_ref = -4.68 + (er.location.x - orr.location.x); cen_new = -1700.0 + (en.location.x - on.location.x); dx = cen_ref - cen_new
o = en.copy(); o.data = en.data.copy(); o.name = "piesa_169_C_pe_ref"
col = bpy.data.collections.get("PS_PE_REF") or bpy.data.collections.new("PS_PE_REF")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for x in list(col.objects): bpy.data.objects.remove(x)
col.objects.link(o)
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); bm.verts.ensure_lookup_table(); bm.normal_update()
n = len(bm.verts); D = np.zeros((n, 3)); hit = np.zeros(n, bool)
for i, v in enumerate(bm.verts):
    p = v.co + Vector((dx, 0, 0)); best = None
    for sg in (1, -1):
        r = tree.ray_cast(p, v.normal * sg, LIM)
        if r[0] is not None and (best is None or r[3] < best[1]): best = (r[0], r[3])
    if best: D[i] = np.array(best[0] - p); hit[i] = True
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
far = np.where(hit, 0, 10 ** 6).astype(float)                            # distance (in edges) to the nearest hole border
for _ in range(BLUR):
    far = np.minimum(far, np.array([min(far[j] for j in nb[i]) + 1 for i in range(n)]))
Ds = D.copy()
for _ in range(BLUR):
    Ds = np.array([(Ds[i] + Ds[nb[i]].sum(0)) / (1 + len(nb[i])) for i in range(n)])
w = np.clip(np.array([min(far[j] for j in nb[i]) for i in range(n)]) / BLUR, 0, 1)   # deep inside the reference: its exact shape
Dm = np.where(hit[:, None] & (w[:, None] >= 1), D, Ds)
for i, v in enumerate(bm.verts): v.co += Vector(Dm[i])
bm.transform(o.matrix_world.inverted()); bm.to_mesh(o.data); bm.free()
en.hide_set(True); en.hide_render = True
print("PE REF: %d varfuri, %.0f %% lipite de referinta (pana la %.0f m pe normala), %.0f %% raman ale corpului (gauri / unde referinta lipseste); mutare medie %.1f m" % (
    n, 100 * hit.mean(), LIM, 100 * (1 - hit.mean()), np.linalg.norm(D[hit], axis=1).mean()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

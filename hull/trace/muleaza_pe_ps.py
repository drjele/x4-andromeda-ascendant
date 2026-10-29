# A piece moulded onto gp_PS's top (asked: gp_comp_055_S to follow gp_PS's surface): every vertex moved in z by how far the
# PS surface (ray straight down) is from the piece's own underside vertex nearest in plan - the underside lies on the surface,
# the thickness above it kept. Then mirrored onto the _D piece; the exploded gpe_ copies get the same shape.
# Usage: blender -b <in> --python muleaza_pe_ps.py -- <out.blend> <piece e.g. gp_comp_055_S>
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, N = a[0], a[1]
o = bpy.data.objects[N]; ps = bpy.data.objects["gp_PS"]; inv = ps.matrix_world.inverted(); mw = o.matrix_world
W = [mw @ v.co for v in o.data.vertices]; zb = min(w.z for w in W)
def surf(w):
    ok, loc, _, _ = ps.ray_cast(inv @ Vector((w.x, w.y, w.z + 300)), inv.to_3x3() @ Vector((0, 0, -1)))
    return (ps.matrix_world @ loc).z if ok else None
before = [w.z - s for w in W if w.z < zb + 0.05 for s in [surf(w)] if s is not None]
from mathutils.bvhtree import BVHTree
bm0 = bmesh.new(); bm0.from_mesh(o.data); bm0.transform(mw); T = BVHTree.FromBMesh(bm0)     # the piece as it was (world)
def under(w):                                                          # the piece's own underside at (x, y): first hit from below
    loc, _, _, _ = T.ray_cast(Vector((w.x, w.y, zb - 50)), Vector((0, 0, 1)))
    return loc.z if loc is not None else zb
from mathutils.kdtree import KDTree
B = [i for i, w in enumerate(W) if abs(w.z - under(w)) < 0.05]          # the underside's own vertices: moved onto the surface
dB = {}; miss = 0
for i in B:
    s = surf(W[i])
    if s is None: miss += 1; continue
    dB[i] = s - W[i].z
kd = KDTree(len(dB))
for j, i in enumerate(dB): kd.insert(Vector((W[i].x, W[i].y, 0)), i)
kd.balance()
for v, w in zip(o.data.vertices, W):                                     # every other vertex: the move of the nearest underside
    _, i, _ = kd.find(Vector((w.x, w.y, 0))); v.co.z += dB[i]            # vertex (in plan) - walls and top follow, no spikes
o.data.update(); bpy.context.view_layer.update()
W2 = [o.matrix_world @ v.co for v in o.data.vertices]; after = [W2[i].z - surf(W2[i]) for i in dB]
before = [W[i].z - surf(W[i]) for i in dB]
print("MULAT %s: joc sub piesa inainte %.2f..%.2f m, dupa %.3f..%.3f m (%d puncte fara PS dedesubt)" % (N, min(before), max(before), min(after), max(after), miss))
for pre in ("gpe_",):                                                    # the exploded copy: same shape
    k = bpy.data.objects.get(pre + N[3:])
    if k: old = k.data; k.data = o.data.copy(); k.data.name = k.name; bpy.data.meshes.remove(old)
sd, td = N[-1], "D" if N[-1] == "S" else "S"
for pre in ("gp_", "gpe_"):                                             # the other side: mirror
    src = bpy.data.objects.get(pre + N[3:]); t = bpy.data.objects.get(pre + N[3:-1] + td)
    if not (src and t): continue
    me = src.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); old = t.data; t.data = me; me.name = t.name; bpy.data.meshes.remove(old)
    print("OGLINDIT pe", t.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT)

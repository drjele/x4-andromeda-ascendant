# The whole PS put together from the pieces rebuilt from the original (asked: assemble completely - with the arms, the hood
# on top and whatever else is needed): every piece (npz, ship coordinates, centred) twice - assembled at XA and exploded at
# XE (each piece moved by its own offset) - in the collection PS_ORIGINAL_COMPLET, with its material, UVs projected from
# above, smooth shading only under 25 degrees. Pieces: name=file:vkey,fkey:material:dx,dy,dz (the exploded offset).
# Usage: blender -b <f.blend> --python asamblare_completa.py -- <out.blend> <xa> <xe> <piece> ...
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, XA, XE = a[0], float(a[1]), float(a[2]); sc = bpy.context.scene
col = bpy.data.collections.get("PS_ORIGINAL_COMPLET") or bpy.data.collections.new("PS_ORIGINAL_COMPLET")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
for spec in a[3:]:
    name, rest = spec.split("="); fn, keys, mat, off = rest.split(":"); vk, fk = keys.split(","); dx, dy, dz = [float(t) for t in off.split(",")]
    Z = np.load(fn); v = Z[vk].astype(float); f = Z[fk]
    me = bpy.data.meshes.new(name); me.from_pydata(v.tolist(), [], f.tolist()); me.validate()
    b = bmesh.new(); b.from_mesh(me); fb = sum(1 for e in b.edges if e.is_boundary); nm = sum(1 for e in b.edges if not e.is_manifold and not e.is_boundary); b.free()
    me.materials.append(bpy.data.materials[mat]); L = me.uv_layers.new(name="UVMap")
    li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
    for tag, X0, D in (("asm", XA, (0, 0, 0)), ("expl", XE, (dx, dy, dz))):
        o = bpy.data.objects.new("%s_%s" % (tag, name), me); col.objects.link(o); o.location = (X0 + D[0], D[1], D[2])
        bpy.context.view_layer.objects.active = o
        for s in bpy.context.selected_objects: s.select_set(False)
        o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
    print("PIESA %s: %d fete, muchii libere %d, nemanifold %d; %s; explodat cu (%.0f, %.0f, %.0f)" % (name, len(me.polygons), fb, nm, mat, dx, dy, dz))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

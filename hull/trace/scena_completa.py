# One light scene with everything to compare (asked: the reference model, what we have built and the confirmed front arms,
# together): objects copied (appended) from their files into their own collections - the reference ship's collections from
# its file (not the deleted backups), the confirmed front arms and nacelles - plus the new pieces from npz (ship
# coordinates, centred) placed at the work spot XN, with their material, UVs from above, smooth shading under 25 degrees.
# Usage: blender -b --factory-startup --python scena_completa.py -- <out.blend> <xn>
#        coll:<file.blend>:<collection,...>:<new collection>   obj:<file.blend>:<object,...>:<new collection>
#        npz:<name>=<file>:<vkey,fkey>:<material>:<new collection>
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, XN = a[0], float(a[1]); sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
tot = 0
for spec in a[2:]:
    kind, rest = spec.split(":", 1)
    if kind in ("coll", "obj"):
        fn, names, dest = rest.split(":"); names = names.split(","); dc = coll(dest)
        with bpy.data.libraries.load(fn, link=False) as (src, dst):
            if kind == "coll": dst.collections = [c for c in src.collections if c in names]
            else: dst.objects = [o for o in src.objects if o in names]
        objs = [o for c in dst.collections for o in c.all_objects] if kind == "coll" else list(dst.objects)
        n = 0
        for o in objs:
            if o.type != "MESH" or o.name in dc.objects: continue
            dc.objects.link(o); o.hide_set(False); o.hide_viewport = False; o.hide_render = False; n += len(o.data.polygons)
        for c in (dst.collections if kind == "coll" else []):
            for o in list(c.objects): c.objects.unlink(o)
            bpy.data.collections.remove(c)
        tot += n; print("ADUS %s din %s: %d obiecte, %d fete -> %s" % (",".join(names), fn.split("/")[-1], len(objs), n, dest))
    else:
        nm, rest2 = rest.split("=", 1); fn, keys, mat, dest = rest2.split(":"); vk, fk = keys.split(","); dc = coll(dest)
        Z = np.load(fn); v = Z[vk].astype(float); me = bpy.data.meshes.new(nm); me.from_pydata(v.tolist(), [], Z[fk].tolist()); me.validate()
        if bpy.data.materials.get(mat): me.materials.append(bpy.data.materials[mat])
        L = me.uv_layers.new(name="UVMap"); li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (v[li][:, :2] / 256.0).ravel())
        o = bpy.data.objects.new(nm, me); dc.objects.link(o); o.location.x = XN
        for s in bpy.context.selected_objects: s.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
        tot += len(me.polygons); print("PIESA %s: %d fete la x %.0f -> %s" % (nm, len(me.polygons), XN, dest))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SCENA %s: %d fete in total" % (OUT, tot))

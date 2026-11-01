# The new surfaces placed twice next to their guides: assembled (as they sit on the ship) and exploded (each piece pushed apart
# by its own offset), each its own object (pieces stay separate), in its own collection; materials made if missing.
# Usage: blender -b <f.blend> --python suprafete_explodat.py -- <out.blend> <collection> <x assembled> <x exploded> \
#        <npz:key:material:r,g,b:dx,dy,dz (exploded offset)> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, COL, XA, XE = a[0], a[1], float(a[2]), float(a[3])
col = bpy.data.collections.get(COL) or bpy.data.collections.new(COL)
if COL not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
for spec in a[4:]:
    path, key, mn, rgb, off = spec.split(":"); Z = np.load(path); rgb = [float(q) for q in rgb.split(",")] + [1]; off = [float(q) for q in off.split(",")]
    m = bpy.data.materials.get(mn) or bpy.data.materials.new(mn); m.diffuse_color = rgb; m.use_fake_user = True
    me = bpy.data.meshes.new(key); me.from_pydata(Z[key + "__v"].astype(float).tolist(), [], Z[key + "__f"].tolist()); me.validate(); me.materials.append(m)
    for tag, x, d in (("asamblat", XA, (0, 0, 0)), ("explodat", XE, off)):
        o = bpy.data.objects.new("nou_%s_%s" % (key, tag), me); col.objects.link(o); o.location = (x + d[0], d[1], d[2]); o.color = rgb
        for s in bpy.context.selected_objects: s.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
        print("SUPRAFATA %s: %d fete la x %.0f" % (o.name, len(me.polygons), x + d[0]))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

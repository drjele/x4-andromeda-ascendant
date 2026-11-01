# The pieces confirmed so far assembled in one block (asked: the new left / right arms smoothed and assembled with the PS and the red
# nacelles, to see what is ok so far): the confirmed board's pieces (linked copies of PIESE_DIN_GHIDAJE_ASAMBLAT's gp_*: PS, frame,
# hull, hood, back arms, ears, 055 pads) + the new front arms and nacelles from npz, every piece its own object, in collection
# ASAMBLAT_NOU at x X0 (ship coordinates + X0).
# Usage: blender -b <f.blend> --python asamblare_noua.py -- <out.blend> <x0> <npz:key:material:r,g,b> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, X0 = a[0], float(a[1])
col = bpy.data.collections.get("ASAMBLAT_NOU") or bpy.data.collections.new("ASAMBLAT_NOU")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
src = bpy.data.collections["PIESE_DIN_GHIDAJE_ASAMBLAT"]; n = 0
for o in src.objects:
    if not o.name.startswith("gp_"): continue                              # (the old front arms and nacelles are replaced)
    c = bpy.data.objects.new("an_" + o.name[3:], o.data); col.objects.link(c); c.location = (X0 + o.location.x + 1600, o.location.y, o.location.z)
    c.rotation_euler = o.rotation_euler; c.scale = o.scale; c.color = o.color; n += 1
def smooth_by_angle(o):
    for s in bpy.context.selected_objects: s.select_set(False)
    bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.shade_smooth_by_angle(angle=0.436); o.select_set(False)
for spec in a[2:]:
    path, key, mn, rgb = spec.split(":"); Z = np.load(path); rgb = [float(q) for q in rgb.split(",")] + [1]
    m = bpy.data.materials.get(mn) or bpy.data.materials.new(mn); m.diffuse_color = rgb; m.use_fake_user = True
    me = bpy.data.meshes.new("an_" + key); me.from_pydata(Z[key + "__v"].astype(float).tolist(), [], Z[key + "__f"].tolist()); me.validate(); me.materials.append(m)
    o = bpy.data.objects.new("an_" + key, me); col.objects.link(o); o.location.x = X0; o.color = rgb; smooth_by_angle(o); n += 1
print("ASAMBLAT_NOU: %d piese la x %.0f" % (n, X0)); bpy.ops.wm.save_as_mainfile(filepath=OUT)

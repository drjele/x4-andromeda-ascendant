# Experiment (asked: from the original keep only the surface you can see, make it one surface/object that looks the same,
# then smooth it, organic): the reference PS pieces (the ones in PS_EXPLODAT) copied, in world place, joined; one voxel
# remesh (VOX m) makes a single closed surface of their union; only its largest connected shell kept (the outside - what a
# camera sees; shells hidden inside are separate and dropped). UVs carried over from the joined originals (Data Transfer,
# nearest face) and each face given the material of the nearest original face, so it looks the same. A smoothed copy
# (Laplacian, volume kept). Both placed next to the exploded sets (raw at X, smoothed at X + 2400), collection
# EXPERIMENT_VIZIBIL; distance to the original surface measured. The original is not touched.
# Usage: blender -b <file.blend> --python ps_vizibil.py -- <out.blend> <x> [vox]
import bpy, bmesh, sys, os, numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT, XP = a[0], float(a[1]); VOX = float(a[2]) if len(a) > 2 else 2.0; sc = bpy.context.scene
names = sorted(o.name[5:] for o in bpy.data.collections["PS_EXPLODAT"].objects if o.name.startswith("expl_R") and o.type == "MESH")
col = bpy.data.collections.get("EXPERIMENT_VIZIBIL") or bpy.data.collections.new("EXPERIMENT_VIZIBIL")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
cps = []
for n in names:
    o = bpy.data.objects[n]; c = o.copy(); c.data = o.data.copy(); col.objects.link(c); c.data.transform(o.matrix_world); c.matrix_world.identity(); cps.append(c)
bpy.ops.object.select_all(action="DESELECT")
for c in cps: c.hide_set(False); c.select_set(True)
bpy.context.view_layer.objects.active = cps[0]; bpy.ops.object.join(); J = bpy.context.view_layer.objects.active; J.name = "exp_original_unit"
print("ORIGINAL: %d piese unite, %d fete" % (len(names), len(J.data.polygons)))
V = J.copy(); V.data = J.data.copy(); V.name = "exp_ps_vizibil"; col.objects.link(V)
bpy.ops.object.select_all(action="DESELECT"); V.select_set(True); bpy.context.view_layer.objects.active = V
GR = float(os.environ.get("VIZ_GROSIME", "4"))                         # the pieces are open sheets: thickened first so they make
if GR > 0:                                                              # volumes that overlap (one union, not one shell per piece)
    sm = V.modifiers.new("gros", "SOLIDIFY"); sm.thickness = GR; sm.offset = 0.0; bpy.ops.object.modifier_apply(modifier=sm.name)
V.data.remesh_voxel_size = VOX; V.data.use_remesh_preserve_volume = False; bpy.ops.object.voxel_remesh()
nf0 = len(V.data.polygons)                                              # the shells: split by Blender (loose parts), the biggest kept
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
parts = [o for o in bpy.context.selected_objects]; parts.sort(key=lambda o: len(o.data.polygons), reverse=True); V = parts[0]; V.name = "exp_ps_vizibil"
for o in parts[1:]: bpy.data.objects.remove(o)
print("VIZIBIL: remesh %.1f m -> %d invelisuri, pastrat cel exterior (%d fete din %d)" % (VOX, len(parts), len(V.data.polygons), nf0))
bj = bmesh.new(); bj.from_mesh(J.data); bj.faces.ensure_lookup_table(); tree = BVHTree.FromBMesh(bj); mat_j = [f.material_index for f in bj.faces]
V.data.materials.clear()
for m in J.data.materials: V.data.materials.append(m)
mi = [mat_j[tree.find_nearest(p.center)[2]] for p in V.data.polygons]; V.data.polygons.foreach_set("material_index", mi)
V.data.uv_layers.new(name="UVMap"); md = V.modifiers.new("uv", "DATA_TRANSFER"); md.object = J; md.use_object_transform = True
md.use_loop_data = True; md.data_types_loops = {"UV"}; md.loop_mapping = "POLYINTERP_NEAREST"
bpy.context.view_layer.objects.active = V; bpy.ops.object.modifier_apply(modifier=md.name)
for p in V.data.polygons: p.use_smooth = True
S = V.copy(); S.data = V.data.copy(); S.name = "exp_ps_vizibil_netezit"; col.objects.link(S)
ms = S.modifiers.new("net", "LAPLACIANSMOOTH"); ms.lambda_factor = float(os.environ.get("VIZ_LAMBDA", "2.0")); ms.iterations = int(os.environ.get("VIZ_ITER", "12")); ms.use_volume_preserve = True
bpy.context.view_layer.objects.active = S; bpy.ops.object.modifier_apply(modifier=ms.name)
def dev(O):
    v = np.zeros(len(O.data.vertices) * 3); O.data.vertices.foreach_get("co", v); v = v.reshape(-1, 3)[::25]
    d = np.array([tree.find_nearest(p)[3] for p in v]); return d.mean(), np.percentile(d, 95), d.max()
print("ABATERE fata de original: brut medie %.2f / 95%% %.2f / max %.2f m; netezit medie %.2f / 95%% %.2f / max %.2f m" % (dev(V) + dev(S)))
v = np.zeros(len(J.data.vertices) * 3); J.data.vertices.foreach_get("co", v); cx = float(np.mean(v.reshape(-1, 3)[:, 0]))
bpy.data.objects.remove(J)
V.location.x = XP - cx; S.location.x = XP + 2400 - cx
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

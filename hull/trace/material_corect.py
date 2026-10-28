# Materials as on the reference (asked: the right texture, not black): the new body pieces get the reference body's material
# (R002 169_C is all Material_8, the light 512 px texture - not Material_6, the dark one); the rebuilt 055 pads replace the
# old meshes with the reference 055's Material_7; UVs projected from above (the textures are near uniform). The 103_118
# pieces are left out for now (hidden, with their exploded copies). Usage: blender -b <f.blend> --python material_corect.py
# -- <out.blend> <055.npz> [hide ...]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; P55 = np.load(a[1]); HIDE = a[2:] or ["103_118"]; DX = -1700.0
def uv(me):
    me.uv_layers.clear() if hasattr(me.uv_layers, "clear") else None
    while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
    L = me.uv_layers.new(name="UVMap"); co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); L.data.foreach_set("uv", (co[li][:, :2] / 256.0).ravel())
def mat(o, name):
    o.data.materials.clear(); o.data.materials.append(bpy.data.materials[name])
    for p in o.data.polygons: p.material_index = 0
for n in ("piesa_169_C_PS", "piesa_169_C_brat_S", "piesa_169_C_brat_D"):
    o = bpy.data.objects[n]; mat(o, "Material_8"); uv(o.data); print("MATERIAL %s: Material_8 (ca R002 169_C)" % n)
for n, sx in (("piesa_comp_055_S", 1), ("piesa_comp_055_D", -1)):
    o = bpy.data.objects[n]; v = P55["v"].astype(float) * [sx, 1, 1] + [DX, 0, 0]; f = P55["f"] if sx > 0 else P55["f"][:, ::-1]
    me = bpy.data.meshes.new(n); me.from_pydata(v.tolist(), [], f.tolist()); me.validate()
    for p in me.polygons: p.use_smooth = True
    o.data = me; mat(o, "Material_7"); uv(me); o.location = (0, 0, 0); print("055 %s inlocuit: %d fete, Material_7" % (n, len(me.polygons)))
for o in bpy.data.objects:
    if any(h in o.name for h in HIDE) and ("piesa_comp" in o.name):
        o.hide_set(True); o.hide_render = True; print("SCOS", o.name)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

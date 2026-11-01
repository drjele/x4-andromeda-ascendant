# Decorations added as their own objects in ASAMBLAT_NOU (each piece separate), both sides: mesh from an npz (ship coords), material
# (and the source's per-face materials + its own triangle UVs when given, else UVs from above x,y/256), placed at X0 like the rest.
# Old objects named in REMOVE are deleted first.
# Usage: blender -b <f.blend> --python adauga_decor.py -- <out.blend> <x0> <remove,...|-> <name|npz|vkey_S|vkey_D|fkey|material|src_npz or -> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, X0 = a[0], float(a[1]); col = bpy.data.collections["ASAMBLAT_NOU"]
for nm in ([] if a[2] == "-" else a[2].split(",")):
    if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm]); print("SCOS", nm)
for spec in a[3:]:
    name, path, kS, kD, kf, mat, src = spec.split("|"); Z = np.load(path); SRC = np.load(src) if src != "-" else None
    for sd, kv in (("S", kS), ("D", kD)):
        nm = "an_%s_%s" % (name, sd)
        if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
        V = Z[kv] if kv in Z.files else Z[kS] * [-1, 1, 1]
        F = Z[kf] if (sd == "S" or kf + "_D" not in Z.files) else Z[kf + "_D"]
        if sd == "D" and kv not in Z.files: F = F[:, ::-1]
        if kf == "f_S" and sd == "D" and "f_D" in Z.files: F = Z["f_D"]
        me = bpy.data.meshes.new(nm); me.from_pydata(V.tolist(), [], F.tolist()); me.validate()
        if SRC is not None and "mats" in SRC.files:
            for m in SRC["mats"]: me.materials.append(bpy.data.materials[str(m)])
            if "mi" in SRC.files and len(SRC["mi"]) == len(me.polygons): me.polygons.foreach_set("material_index", SRC["mi"].astype(np.int32))
        else: me.materials.append(bpy.data.materials[mat])
        uv = me.uv_layers.new(name="UVMap")
        if SRC is not None and "tri_uv" in SRC.files and len(SRC["tri_uv"]) == len(me.polygons):
            T = SRC["tri_uv"] if sd == "S" or kv in Z.files and False else SRC["tri_uv"][:, ::-1]
            if sd == "S": T = SRC["tri_uv"]
            uv.data.foreach_set("uv", T.reshape(-1).astype(np.float32))
        else:
            li = np.zeros(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", li); uv.data.foreach_set("uv", (V[li][:, :2] / 256.0).ravel().astype(np.float32))
        for p in me.polygons: p.use_smooth = True
        o = bpy.data.objects.new(nm, me); col.objects.link(o); o.location.x = X0; print("DECOR", nm, len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

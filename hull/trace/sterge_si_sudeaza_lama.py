# Board tidy after the blade (asked: delete lama_referinta_pe_noi and the on-ship blade guides g_lama_lama_*, keep only the separate
# guides g_lamasep_lama_* and weld them there): removes those objects, then welds g_lamasep_lama_* into one curve body
# g_lamasep_sudat_S (same points; the old names kept in its "linii" property, like sudeaza_ghidaje.py).
# Usage: blender -b <in.blend> --python sterge_si_sudeaza_lama.py -- <out.blend>
import bpy, sys, json
OUT = sys.argv[sys.argv.index("--") + 1]
gone = [o.name for o in bpy.data.objects if o.name == "lama_referinta_pe_noi" or o.name.startswith("g_lama_lama_")]
for n in gone: bpy.data.objects.remove(bpy.data.objects[n])
src = sorted([o for o in bpy.data.objects if o.name.startswith("g_lamasep_lama_") and o.type == "CURVE"], key=lambda o: o.name)
cu = bpy.data.curves.new("g_lamasep_sudat_S", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = src[0].data.bevel_depth; names = []
for o in src:
    for m in o.data.materials:
        if m and m.name not in [x.name for x in cu.materials]: cu.materials.append(m)
    for sp in o.data.splines:
        s = cu.splines.new("POLY"); s.points.add(len(sp.points) - 1)
        for p, q in zip(s.points, sp.points): p.co = (*(o.matrix_world @ q.co.xyz), 1)
        names.append(o.name)
w = bpy.data.objects.new("g_lamasep_sudat_S", cu); w["linii"] = json.dumps(names); w.color = src[0].color
for c in src[0].users_collection: c.objects.link(w)
for o in src: bpy.data.objects.remove(o)
print("STERS %d (%s ...), SUDAT %d linii in g_lamasep_sudat_S" % (len(gone), ", ".join(gone[:2]), len(names)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

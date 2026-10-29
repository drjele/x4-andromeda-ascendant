# The big ears cleaned of what is extra: the part inside the PS and the back arms taken out (EXACT boolean difference on
# the assembled gp_ pieces); the trimmed shape then given to the exploded (gpe_) and fit (pot_) copies. Body untouched.
# Usage: blender -b <in> --python curata_urechi.py -- <out.blend>
import bpy, bmesh, sys
OUT = sys.argv[sys.argv.index("--") + 1]
body = [bpy.data.objects[n] for n in ("gp_PS", "gp_brat_spate_D", "gp_brat_spate_S")]
for sd in ("D", "S"):
    o = bpy.data.objects["gp_ureche_" + sd]; v0 = sum(1 for _ in o.data.polygons)
    for b in body:
        m = o.modifiers.new("b", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = b; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = o
        for ob in bpy.context.view_layer.objects: ob.select_set(ob == o)
        bpy.ops.object.modifier_apply(modifier="b")
    bm = bmesh.new(); bm.from_mesh(o.data); nm = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume(); bm.free()
    for pre in ("gpe_", "pot_"):
        k = bpy.data.objects.get("%sureche_%s" % (pre, sd))
        if k is None: continue
        old = k.data; k.data = o.data.copy(); k.data.name = k.name; bpy.data.meshes.remove(old)
    print("CURATAT ureche_%s: %d -> %d fete, ne-manifold %d, volum %.0f m3" % (sd, v0, len(o.data.polygons), nm, vol))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

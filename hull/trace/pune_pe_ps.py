# A component laid on gp_PS (asked: put sep_comp_055_S on gp_PS): its place in plan taken from the old exploded set (its
# offset from sep_PS minus the explode lift), then dropped / raised in z until its underside just sits on gp_PS's top
# (rays straight down from every underside vertex). Copied into the assembled (gp_) and exploded (gpe_, +LIFT z) blocks.
# Usage: blender -b <in> --python pune_pe_ps.py -- <out.blend> <object> <explode lift z (old set)> [gpe lift z]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, N, LZ = a[0], a[1], float(a[2]); LE = float(a[3]) if len(a) > 3 else 50.0
src = bpy.data.objects[N]; ps0 = bpy.data.objects["sep_PS"]; gp = bpy.data.objects["gp_PS"]
off = src.location - ps0.location - Vector((0, 0, LZ))                  # its place relative to the PS, assembled
off.x = 0 if abs(off.x) < 200 else off.x                               # the old set was moved apart in x only for showing
base = gp.location + off; inv = gp.matrix_world.inverted(); gaps = []
V = [src.matrix_world @ v.co - src.location + base for v in src.data.vertices]; zmin = min(v.z for v in V)
for w in [v for v in V if v.z < zmin + 3]:                               # the underside
    ok, loc, nrm, _ = gp.ray_cast(inv @ (w + Vector((0, 0, 200))), Vector((0, 0, -1)))
    if ok: gaps.append(w.z - (gp.matrix_world @ loc).z)
dz = -min(gaps) if gaps else 0.0
for pre, col, lift in (("gp_", "PIESE_DIN_GHIDAJE_ASAMBLAT", 0.0), ("gpe_", "PIESE_DIN_GHIDAJE_EXPLODAT", LE)):
    n = pre + N.replace("sep_", ""); o0 = bpy.data.objects.get(n)
    if o0: bpy.data.objects.remove(o0)
    o = src.copy(); o.data = src.data.copy(); o.name = n; o.data.name = n
    for c in o.users_collection: c.objects.unlink(o)
    bpy.data.collections[col].objects.link(o)
    ref = bpy.data.objects[pre + "PS"].location
    o.location = ref + off + Vector((0, 0, dz + lift))
print("PUS PE PS: %s, deplasare fata de PS %s, ridicat %.2f m ca sa stea pe gp_PS (%d puncte de sprijin, joc max %.2f m)" % (
    N, tuple(round(v, 1) for v in off), dz, len(gaps), (max(gaps) - min(gaps)) if gaps else 0))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

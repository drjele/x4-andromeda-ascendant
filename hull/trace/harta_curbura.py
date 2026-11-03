# Curvature heat map of a piece (asked: clean lines / surfaces pass - show WHERE a surface bends abruptly or waves, not guess): per
# vertex the largest turn of the normal per metre to its neighbours (deg/m), as vertex colours blue (flat) -> red (>= KMAX deg/m),
# rendered alone from above, below and both sides (orthographic). Prints the share of the surface over KMAX/2 and KMAX.
# Usage: blender -b <f.blend> --python harta_curbura.py -- <out_prefix> <piece> [KMAX=3]
import bpy, sys, bmesh, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, N = a[0], a[1]; KMAX = float(a[2]) if len(a) > 2 else 3.0
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.show_cavity = False
p = bpy.data.objects[N]
for o in sc.objects: o.hide_render = o is not p
me = p.data; bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.normal_update()
k = np.zeros(len(bm.verts))
for v in bm.verts:
    best = 0.0
    for e in v.link_edges:
        w = e.other_vert(v); L = (w.co - v.co).length
        if L > 1e-4: best = max(best, np.degrees(v.normal.angle(w.normal, 0)) / max(L, .5))
    k[v.index] = best
t = np.clip(k / KMAX, 0, 1)
col = np.c_[np.clip(1.5 - np.abs(4 * t - 3), 0, 1), np.clip(1.5 - np.abs(4 * t - 2), 0, 1), np.clip(1.5 - np.abs(4 * t - 1), 0, 1), np.ones(len(t))]
ca = me.color_attributes.get("curbura") or me.color_attributes.new("curbura", "FLOAT_COLOR", "POINT")
ca.data.foreach_set("color", col.astype(np.float32).ravel()); me.color_attributes.active_color = ca
sh.color_type = "VERTEX"
print("CURBURA %s: peste %.1f grade/m: %.1f%% din varfuri, peste %.1f: %.1f%%, max %.1f" % (N, KMAX / 2, 100 * (k > KMAX / 2).mean(), KMAX, 100 * (k > KMAX).mean(), k.max()))
mw = p.matrix_world; pts = [mw @ Vector(b) for b in p.bound_box]; lo = Vector([min(q[i] for q in pts) for i in range(3)]); hi = Vector([max(q[i] for q in pts) for i in range(3)])
c = (lo + hi) / 2; ext = hi - lo; sc.render.resolution_x, sc.render.resolution_y = 1200, 900
cam = bpy.data.cameras.new("c"); co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co; cam.clip_end = 50000; cam.type = "ORTHO"
for n, d, sc_ in (("sus", (0, -.001, 1), max(ext.x, ext.y / .75)), ("jos", (0, -.001, -1), max(ext.x, ext.y / .75)), ("stanga", (-1, 0, .001), max(ext.y, ext.z / .75)), ("spate", (0, -1, .001), max(ext.x, ext.z / .75))):
    co.location = c + Vector(d).normalized() * ext.length * 2; co.rotation_euler = (c - co.location).to_track_quat("-Z", "Y").to_euler(); cam.ortho_scale = sc_ * 1.08
    sc.render.filepath = "%s_%s.png" % (OUT, n); bpy.ops.render.render(write_still=True)

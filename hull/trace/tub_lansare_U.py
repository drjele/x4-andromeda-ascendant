# An S launch tube in the U at the back of an_PS (asked: its mouth at the innermost point of the U, centred horizontally and
# vertically, facing backwards): rays along +y at x = 0 find the U's bottom wall (the deepest y over the PS thickness = the
# innermost point); the wall's z span there gives the vertical centre. Box TW x TH x TL (game macro launchtube_arg_s_01:
# 40 x 30 x 80 m), mouth flush with the wall at x = 0, running TL m forwards into the body.
# Ship coords = world + X0 on x (ASAMBLAT_NOU pieces have location x -X0, mesh in ship coords).
# Asked next: move it a little further back and hollow an_PS where the tube is, so nothing obstructs it: the mouth goes SH m
# further back (env SH) and, with SCOB=1, an_PS gets a boolean cut = the tube's box grown by CL m on the sides (exact solver).
# Usage: blender -b <scene.blend> --python tub_lansare_U.py -- <out.blend> [x0=1600]   env TW=40 TH=30 TL=80 PROUD=0.5 SH=0 SCOB=0 CL=0.3
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; X0 = float(a[1]) if len(a) > 1 else 1600.0
TW, TH, TL = (float(os.environ.get(k, d)) for k, d in (("TW", 40), ("TH", 30), ("TL", 80)))
V, F = [], []
for n in ("an_PS", "an_PS_rama", "an_PS_carena", "an_capac_086"):
    o = bpy.data.objects[n]; b = len(V); V += [tuple(o.matrix_world @ v.co + Vector((X0, 0, 0))) for v in o.data.vertices]
    F += [[b + i for i in p.vertices] for p in o.data.polygons]
bvh = BVHTree.FromPolygons([Vector(p) for p in V], F); Va = np.array(V)
hits = []
for z in np.arange(Va[:, 2].min(), Va[:, 2].max(), 0.5):
    h = bvh.ray_cast(Vector((0, -400, z)), Vector((0, 1, 0)), 600)
    if h[0] is not None and h[1].y < -0.5: hits.append((z, h[0].y))   # a face looking backwards = the U's bottom wall
hits = np.array(hits)
# the wall = the contiguous z run of hits close to the U's bottom (within 3 m of its median y)
ym = np.median(hits[:, 1]); w = hits[np.abs(hits[:, 1] - ym) < 3]; zlo, zhi = w[:, 0].min(), w[:, 0].max(); zc = (zlo + zhi) / 2
yin = w[:, 1].max()                                                    # innermost point of the U at x = 0
x0, x1 = -TW / 2, TW / 2; z0, z1 = zc - TH / 2, zc + TH / 2
# the mouth must be visible (asked: the tube was hidden inside an_PS - the U's wall bows, 3..7 m behind the centre point): first
# hits along +y over the whole front face, the mouth PROUD m behind the furthest-back one, so it stands out of the wall everywhere
PROUD = float(os.environ.get("PROUD", 0.5)); fy = []
for xx in np.linspace(x0, x1, 9):
    for zz in np.linspace(z0, z1, 7):
        h = bvh.ray_cast(Vector((xx, -400, zz)), Vector((0, 1, 0)), 600)
        if h[0] is not None: fy.append(h[0].y)
SH = float(os.environ.get("SH", 0)); y0 = min(fy) - PROUD - SH; y1 = y0 + TL
print("PERETE pe fata tubului: y %.1f .. %.1f -> gura la y %.1f (iese %.1f .. %.1f m din perete)" % (min(fy), max(fy), y0, PROUD, max(fy) - y0))
Vt = [(x, y, z) for z in (z0, z1) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
Ft = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
nm = "an_launchtube_s_01"
if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm])
mt = bpy.data.materials.get("tub_lansare") or bpy.data.materials.new("tub_lansare"); mt.diffuse_color = (0.35, 0.45, 0.6, 1)
me = bpy.data.meshes.new(nm); me.from_pydata(Vt, [], Ft); me.materials.append(mt); o = bpy.data.objects.new(nm, me)
bpy.data.collections["ASAMBLAT_NOU"].objects.link(o); o.location = (-X0, 0, 0); o.color = (0.35, 0.45, 0.6, 1)
o["x4_macro"] = "launchtube_arg_s_01_macro"; o["dimensiuni_m"] = "40 x 30 x 80 (lat x inalt x lung)"; o["fata"] = "spre spate (-y)"
if os.environ.get("SCOB") == "1":                                       # hollow an_PS along the tube (its box + CL, open behind)
    CL = float(os.environ.get("CL", .3)); ps = bpy.data.objects["an_PS"]
    cv = [(x, y, z) for z in (z0 - CL, z1 + CL) for x, y in ((x0 - CL, y0 - 60), (x1 + CL, y0 - 60), (x1 + CL, y1 + CL), (x0 - CL, y1 + CL))]
    cm = bpy.data.meshes.new("scob_tub"); cm.from_pydata(cv, [], Ft); co = bpy.data.objects.new("scob_tub", cm)
    bpy.context.scene.collection.objects.link(co); co.location = (-X0, 0, 0)
    n0 = len(ps.data.polygons); md = ps.modifiers.new("scob", "BOOLEAN"); md.operation = "DIFFERENCE"; md.solver = "EXACT"; md.object = co
    bpy.context.view_layer.objects.active = ps; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(co); bpy.data.meshes.remove(cm)
    import bmesh; bm = bmesh.new(); bm.from_mesh(ps.data); nm_ = sum(not e.is_manifold for e in bm.edges); bm.free()
    print("SCOBIT an_PS: fete %d -> %d, muchii ne-manifold %d, cutie x %.1f..%.1f z %.1f..%.1f pana la y %.1f" % (n0, len(ps.data.polygons), nm_, x0 - CL, x1 + CL, z0 - CL, z1 + CL, y1 + CL))
# room left around it: the PS surfaces above / below / beside the tube
up = bvh.ray_cast(Vector((0, y0 + TL / 2, zc)), Vector((0, 0, 1)), 500); dn = bvh.ray_cast(Vector((0, y0 + TL / 2, zc)), Vector((0, 0, -1)), 500)
# U width at the mouth: the U's side walls at z = zc, y just behind the mouth
sides = [bvh.ray_cast(Vector((0, y0 - 2, zc)), Vector((s, 0, 0)), 500) for s in (-1, 1)]
print("TUB S: gura la y %.1f (fundul U-ului la x 0), perete z %.1f..%.1f -> centru z %.1f; tub x %.0f..%.0f, y %.1f..%.1f, z %.1f..%.1f"
      % (y0, zlo, zhi, zc, x0, x1, y0, y1, z0, z1))
print("SPATIU: sus %s m, jos %s m (la mijlocul tubului, pana la prima suprafata PS); U la 2 m in spatele gurii: x %s .. %s"
      % (round(up[0].z - z1, 1) if up[0] else "-", round(z0 - dn[0].z, 1) if dn[0] else "-",
         round(sides[0][0].x, 1) if sides[0][0] else "-", round(sides[1][0].x, 1) if sides[1][0] else "-"))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

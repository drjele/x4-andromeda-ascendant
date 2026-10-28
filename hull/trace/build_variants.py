# The two candidate ships side by side, each decimated to a triangle budget: A = Binkley's ship + morenostefanuto's extra
# details (in their own collection, to toggle), B = morenostefanuto's ship whole; both already at the average proportions.
# Decimation by Blender's collapse decimate per object with one shared ratio (budget / total); counts printed.
# Extras below the ship's middle height (on the lower arms) dropped; the ones kept given a little thickness (solidify,
# THICK m, centred) since they come as flat blades.
# Usage: blender -b --python build_variants.py -- <out.blend> <budget> <A_base.obj> <A_extras.obj> <B.obj> [thick_m]
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BUD, A0, AX, B0 = a[0], int(a[1]), a[2], a[3], a[4]; THICK = float(a[5]) if len(a) > 5 else 6.0
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def load(path, coll, x, col):
    c = bpy.data.collections.get(coll) or bpy.data.collections.new(coll)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z"); m = bpy.data.materials.new(coll); m.diffuse_color = col; obs = list(bpy.context.selected_objects)
    for o in obs:
        for cc in o.users_collection: cc.objects.unlink(o)
        c.objects.link(o); o.location.x += x; o.data.materials.clear(); o.data.materials.append(m)
    return obs
def tris(obs): return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
def decimate(obs, budget):
    n = tris(obs); r = min(1.0, budget / max(n, 1))
    for o in obs:
        if r < 1:
            md = o.modifiers.new("dec", "DECIMATE"); md.ratio = r; bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
    return n, tris(obs)
# B first, so its objects keep the OBJ names; the extras file names which of them are the blades
B = load(B0, "B_morenostefanuto_baza", 900, (0.2, 0.9, 0.8, 1)); A = load(A0, "A_Binkley_baza", -900, (1, 0.35, 1, 1)); AE = load(AX, "A_lame_morenostefanuto", -900, (1, 0.1, 0.1, 1))
BL_NAMES = {l[2:].strip() for l in open(AX) if l.startswith("o ")}
from mathutils import Vector
BLADES = set(o.name.split(".0")[0] if False else o.name for o in AE)
import bmesh
def open_surface(o):
    bm = bmesh.new(); bm.from_mesh(o.data); n = sum(1 for e in bm.edges if e.is_boundary); m = len(bm.edges); bm.free(); return n > 0.02 * m
def thickness(o):                                                         # mean thickness of a closed mesh: 2 * volume / area
    bm = bmesh.new(); bm.from_mesh(o.data); v = abs(bm.calc_volume()); a = sum(f.calc_area() for f in bm.faces); bm.free(); return 2 * v / max(a, 1e-9)
def blades(base, extra, label):
    zs = [v.co.z for o in base for v in o.data.vertices]; zmid = (min(zs) + max(zs)) / 2
    for o in list(extra):
        cz = sum((v.co.z for v in o.data.vertices), 0.0) / max(len(o.data.vertices), 1)
        if cz < zmid: print(label, "SCOS (jos):", o.name, "z %.0f" % cz); extra.remove(o); bpy.data.objects.remove(o); continue
        th = None if open_surface(o) else thickness(o)
        if th is None or th < THICK:
            md = o.modifiers.new("grosime", "SOLIDIFY"); md.thickness = THICK; md.offset = 0; bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
        print(label, "PASTRAT:", o.name, "z %.0f" % cz, "grosime inainte %s" % ("0 (foaie)" if th is None else "%.1f m" % th))
blades(A, AE, "A")
BE = [o for o in B if o.name in BL_NAMES]
for o in BE: B.remove(o)
cb = bpy.data.collections.new("B_lame_morenostefanuto"); sc.collection.children.link(cb)
for o in BE:
    for cc in o.users_collection: cc.objects.unlink(o)
    cb.objects.link(o)
blades(B, BE, "B")
if False:
  for o in list(AE):
    cz = sum((v.co.z for v in o.data.vertices), 0.0) / max(len(o.data.vertices), 1)
    if cz < zmid: print("SCOS (brat de jos):", o.name, "z %.0f" % cz); AE.remove(o); bpy.data.objects.remove(o)
    elif open_surface(o):                                                 # only open (single-sheet) blades get a thickness; closed rings are solid already
        md = o.modifiers.new("grosime", "SOLIDIFY"); md.thickness = THICK; md.offset = 0; bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
        print("PASTRAT + grosime:", o.name, "z %.0f" % cz)
    else: print("PASTRAT:", o.name, "z %.0f" % cz)
ne = tris(AE); na = decimate(A, BUD - ne); nbe = tris(BE); nb = decimate(B, BUD - nbe)
print("A baza %d -> %d, lame %d (total %d); B baza %d -> %d, lame %d (total %d)" % (na[0], na[1], ne, na[1] + ne, nb[0], nb[1], nbe, nb[1] + nbe))
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.clip_start = 1; sp.clip_end = 100000
for name, x in (("A: Binkley + nervuri morenostefanuto", -1500), ("B: morenostefanuto", 300)):
    t = bpy.data.curves.new(name, "FONT"); t.body = name; to = bpy.data.objects.new(name, t); sc.collection.objects.link(to); to.location = (x, -1600, 0); to.scale = (70, 70, 70)
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

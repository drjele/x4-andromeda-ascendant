# The two candidate ships built from the original files imported natively (geometry, materials and textures as their
# authors made them), placed by one affine matrix each (orientation + average proportions, fitted in ref_compare.py):
#   A = Binkley-Piratepants' ship (the GLB's ship mesh only) + morenostefanuto's blades
#   B = morenostefanuto's ship (original OBJ)
# Blades (morenostefanuto objects named in the extras file): only the upper ones kept (below the middle height dropped),
# each given THICK m of thickness where it is a sheet or thinner. Only the body is decimated toward the budget, objects
# smaller than KEEP triangles and the blades untouched, so thin details keep their shape: near-coplanar faces merged
# first (no shape change), then edge collapse (symmetric in x) only for what is still over budget.
# Usage: blender -b --python build_variants_native.py -- <out.blend> <budget> <binkley.glb> <binkley_matrix.json>
#        <moreno.obj> <moreno_matrix.json> <extras.obj> [thick_m] [B_original: B not decimated]
import bpy, bmesh, sys, json
from mathutils import Matrix
a = sys.argv[sys.argv.index("--") + 1:]; OUT, BUD, GLB, MB, MOBJ, MM, EX = a[0], int(a[1]), a[2], a[3], a[4], a[5], a[6]
THICK = float(a[7]) if len(a) > 7 else 8.0; KEEP = 3000; GAP = 900; PLANAR_DEG = 1.0; NO_DEC_B = len(a) > 8 and a[8] == "B_original"
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c
def move(obs, c):
    for o in obs:
        for cc in o.users_collection: cc.objects.unlink(o)
        c.objects.link(o)
def tris(obs): return sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs if o.type == "MESH")
def open_surface(o):
    bm = bmesh.new(); bm.from_mesh(o.data); n = sum(1 for e in bm.edges if e.is_boundary); m = len(bm.edges); bm.free(); return n > 0.02 * m
def thickness(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); v = abs(bm.calc_volume()); ar = sum(f.calc_area() for f in bm.faces); bm.free(); return 2 * v / max(ar, 1e-9)
def apply_mods(o, md):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=md.name)
def place(obs, M, dx):
    for o in obs:
        if o.parent is None: o.matrix_world = Matrix.Translation((dx, 0, 0)) @ M @ o.matrix_world
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
BLADE_NAMES = {l[2:].strip() for l in open(EX) if l.startswith("o ")}
def blades(body, bl, label):
    zs = [(o.matrix_world @ v.co).z for o in body for i_, v in enumerate(o.data.vertices) if i_ % 50 == 0]; zmid = (min(zs) + max(zs)) / 2; kept = []
    for o in bl:
        cz = sum(((o.matrix_world @ v.co).z for v in o.data.vertices), 0.0) / max(len(o.data.vertices), 1)
        if cz < zmid: print(label, "SCOS (jos):", o.name); bpy.data.objects.remove(o); continue
        th = None if open_surface(o) else thickness(o)
        if th is None or th < THICK:
            md = o.modifiers.new("grosime", "SOLIDIFY"); md.thickness = THICK; md.offset = 0; apply_mods(o, md)
        print(label, "PASTRAT:", o.name, "grosime inainte", "0 (foaie)" if th is None else "%.1f m" % th); kept.append(o)
    return kept
def decimate(body, budget):
    # shape-keeping reduction: first near-coplanar faces merged (planar dissolve, PLANAR_DEG; no change of shape), then,
    # only if still over budget, edge collapse on the big objects; small objects untouched
    if tris(body) > budget:
        for o in body:
            if tris([o]) < KEEP: continue
            md = o.modifiers.new("plan", "DECIMATE"); md.decimate_type = "DISSOLVE"; md.angle_limit = PLANAR_DEG * 3.14159 / 180; md.delimit = {"NORMAL", "MATERIAL", "SEAM", "SHARP", "UV"}; apply_mods(o, md)
            md = o.modifiers.new("tri", "TRIANGULATE"); apply_mods(o, md)
    big = [o for o in body if tris([o]) >= KEEP]; small = tris(body) - tris(big); n = tris(big); r = min(1.0, max(budget - small, 1) / max(n, 1))
    if r < 1:
        for o in big:
            md = o.modifiers.new("dec", "DECIMATE"); md.ratio = r; md.use_symmetry = True; md.symmetry_axis = "X"; apply_mods(o, md)
    return r
# B: morenostefanuto
bpy.ops.wm.obj_import(filepath=MOBJ, forward_axis="Y", up_axis="Z"); B = [o for o in bpy.context.selected_objects if o.type == "MESH"]
place(B, Matrix(json.load(open(MM))), GAP)
BB = [o for o in B if o.name in BLADE_NAMES]; Bbody = [o for o in B if o not in BB]
move(Bbody, coll("B_morenostefanuto_corp")); BBk = blades(Bbody, BB, "B"); move(BBk, coll("B_morenostefanuto_lame"))
# A: Binkley's ship + copies of morenostefanuto's kept blades
bpy.ops.import_scene.gltf(filepath=GLB); imp = list(bpy.context.selected_objects)
ship = [o for o in imp if o.type == "MESH" and o.name == "Mesh_7"] or [max((o for o in imp if o.type == "MESH"), key=lambda o: len(o.data.polygons))]
for o in imp:
    if o not in ship: bpy.data.objects.remove(o)
for o in ship:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
place(ship, Matrix(json.load(open(MB))), -GAP); move(ship, coll("A_Binkley_corp"))
AB = []
for o in BBk:
    c = o.copy(); c.data = o.data.copy(); c.location.x -= 2 * GAP; AB.append(c); sc.collection.objects.link(c)
move(AB, coll("A_lame_morenostefanuto"))
ra = decimate(ship, BUD - tris(AB)); rb = decimate(Bbody, BUD - tris(BBk)) if not NO_DEC_B else 1.0                 # B kept at full detail when asked
print("A corp %d (ratio %.3f) + lame %d = %d;  B corp %d (ratio %.3f) + lame %d = %d" % (tris(ship), ra, tris(AB), tris(ship) + tris(AB), tris(Bbody), rb, tris(BBk), tris(Bbody) + tris(BBk)))
for scr in bpy.data.screens:
    for ar in scr.areas:
        for sp in ar.spaces:
            if sp.type == "VIEW_3D": sp.clip_start = 1; sp.clip_end = 100000; sp.shading.color_type = "TEXTURE"
for name, x in (("A: Binkley + lame morenostefanuto", -GAP - 600), ("B: morenostefanuto", GAP - 400)):
    t = bpy.data.curves.new(name, "FONT"); t.body = name; to = bpy.data.objects.new(name, t); sc.collection.objects.link(to); to.location = (x, -1600, 0); to.scale = (70, 70, 70)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

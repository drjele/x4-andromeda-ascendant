# The PS bottom rebuilt as separate pieces from the outlines of ps_fund_contururi.py (asked: sep_PS simple, fully
# smoothed, completely flat bottom; a rim ring on the edge under it; the keel with its big side the shape of its small
# side; the keel's 2 ears separate, reaching the rim). From the full PS mesh (object SRC):
#   sep_PS        - the PS above z = ZP, bottom capped flat, top and sides Taubin-smoothed (bottom plane kept),
#   sep_PS_rama   - the PS below ZP inside contur_corp (+3 m) and outside rama_interior (exact booleans): top flat on the
#                   body, bottom = the PS's own edge shape, thinning out to the edge,
#   sep_PS_carena - floor carena_jos flat at ZF, big side carena_sus at ZP, straight walls between (same point order),
#   sep_PS_ureche_D/_S - plates (EAR_T m thick, top on the body) between the keel and the rim.
# The old objects are replaced; PIESE=carena,urechi rebuilds only those. Usage:
# blender -b <in> --python ps_fund_piese.py -- <out.blend> <contururi.npz> <SRC obj> <location x> ; env EAR_T=4 TAUBIN=10
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, C, SRC, LX = a[0], np.load(a[1]), a[2], float(a[3])
ZP, ZF = C["z"]; ET, NT = float(os.environ.get("EAR_T", "4")), int(os.environ.get("TAUBIN", "10"))
PI = os.environ.get("PIESE", "corp,rama,carena,urechi").split(",")   # only these rebuilt, the others left as they are
src = bpy.data.objects[SRC]; coll = bpy.data.objects["sep_PS"].users_collection[0]; mat = list(bpy.data.objects["sep_PS"].data.materials)
mat_k = list(bpy.data.objects["sep_PS_carena"].data.materials) if "sep_PS_carena" in bpy.data.objects else mat
NUME = dict(corp=["sep_PS"], rama=["sep_PS_rama"], carena=["sep_PS_carena"], urechi=["sep_PS_ureche_D", "sep_PS_ureche_S"])
for n in [q for k_ in PI for q in NUME[k_]]:
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me); o.location = (LX, 0, 0); coll.objects.link(o); return o
def half(keep_above):                                  # the PS cut at ZP, the cut capped flat
    bm = bmesh.new(); bm.from_mesh(src.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, ZP), plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    ed = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=ed, sides=0); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); return bm
def prism(p, z0, z1):                                  # a closed polygon (x, y) extruded z0..z1
    bm = bmesh.new(); vs = [bm.verts.new((x, y, z0)) for x, y in p]; fc = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[fc]); bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.triangulate(bm, faces=bm.faces); return bm
def boolean(o, cutter_bm, op):
    c = new_obj("tmp_cut", cutter_bm, []); m = o.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = c; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.view_layer.objects: ob.select_set(ob == o)
    bpy.ops.object.modifier_apply(modifier="b"); bpy.data.objects.remove(c)
# body: above ZP, Taubin on everything but the flat bottom
made = []
if "corp" in PI:
  bm = half(True); bm.verts.ensure_lookup_table(); bm.verts.index_update()
  P = np.array([v.co[:] for v in bm.verts]); E = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
  fixed = P[:, 2] <= ZP + 0.05; n = len(P); nb = [[] for _ in range(n)]
  for i, j in E: nb[i].append(j); nb[j].append(i)
  deg = np.array([len(q) for q in nb], float); I = np.repeat(np.arange(n), [len(q) for q in nb]); J = np.concatenate([np.array(q, int) for q in nb])
  def avg(X): S = np.zeros_like(X); np.add.at(S, I, X[J]); return S / deg[:, None]
  for _ in range(NT):
      for lam in (0.5, -0.53): X = P + lam * (avg(P) - P); X[fixed] = P[fixed]; P = X
  for v, p in zip(bm.verts, P): v.co = p
  made.append(new_obj("sep_PS", bm, mat))
# rim: below ZP, inside the body outline, outside the rim's inner outline
if "rama" in PI:
    rama = new_obj("sep_PS_rama", half(False), mat); made.append(rama)
    boolean(rama, prism(np.c_[C["contur_corp"][:, 0] * 1.02, C["contur_corp"][:, 1]], ZP - 80, ZP + 1), "INTERSECT")
    boolean(rama, prism(C["rama_interior"], ZP - 80, ZP + 1), "DIFFERENCE")
# keel: floor and big side, straight walls
if "carena" in PI:
  bm = bmesh.new(); lo = [bm.verts.new((x, y, ZF)) for x, y in C["carena_jos"]]; hi = [bm.verts.new((x, y, ZP)) for x, y in C["carena_sus"]]; N = len(lo)
  for i in range(N): bm.faces.new((lo[i], lo[(i + 1) % N], hi[(i + 1) % N], hi[i]))
  bm.faces.new(lo[::-1]); bm.faces.new(hi); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.ops.triangulate(bm, faces=bm.faces)
  made.append(new_obj("sep_PS_carena", bm, mat_k))
if "urechi" in PI: made += [new_obj("sep_PS_ureche_" + s, prism(C["ureche_" + s], ZP - ET, ZP), mat_k) for s in ("D", "S")]
for o in made:
    bm = bmesh.new(); bm.from_mesh(o.data); nm = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    print("PIESA %-18s %6d fete, muchii ne-manifold %d" % (o.name, len(o.data.polygons), nm))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

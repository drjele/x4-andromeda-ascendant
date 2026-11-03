# Clean-up of the blade compartments in place (asked: black streaks on at_PS_carena and on the compartments towards it, at_usa_fata_D
# outline not clean): (1) walls doubled - a hull piece's new wall lying on the arm's compartment wall (z-fighting) is removed from the
# piece, an arm wall lying on a piece's surface is removed from the arm; (2) (no dissolve: it opened edges far from the cut); (3) shading: every edge touching a new face that bends more than ANG deg
# is sharp, so the long fan triangles left on flat faces stop taking the normals of the walls next to them (the streaks), and the
# hatches get sharp rims (skin / side) instead of smooth-shaded ones; (4) UVs of all new faces (walls, hatch sides) projected on
# each face's dominant axis (the top-down x,y/256 stretched into streaks on walls); _D twins re-mirrored. Usage: blender -b <scene> --python
# curata_compartimente.py -- <original scene before the compartments> <out.blend>   env ANG=30
import bpy, bmesh, sys, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; ORIG, OUT = a[0], a[1]; ANG = math.radians(float(os.environ.get("ANG", 30)))
PAIRS = {"at_brat_fata_S": "an_brat_fata_S.002", "at_PS": "g_PS.001", "at_PS_carena": "g_PS_carena.001", "at_ureche_S": "an_ureche_S.001", "at_PS_rama": "an_PS_rama.001"}
with bpy.data.libraries.load(ORIG) as (lf, lt): lt.meshes = list(PAIRS.values())
O = {n: lt.meshes[k] for k, n in enumerate(PAIRS)}
bvm = lambda me: BV.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in me.polygons])
near = lambda t, p, tol: (lambda r: r[0] is not None and r[3] < tol)(t.find_nearest(p))
arm = bpy.data.objects["at_brat_fata_S"]; _mS, _mD = arm.data, bpy.data.objects["at_brat_fata_D"].data   # both arms (whole pieces span S and D)
tArm = BV.FromPolygons([v.co.copy() for v in _mS.vertices] + [v.co.copy() for v in _mD.vertices], [list(p.vertices) for p in _mS.polygons] + [[k + len(_mS.vertices) for k in p.vertices] for p in _mD.polygons])                     # all hull pieces share the atelier offset: local = ship coords
def box_uv(bm, faces):                                                 # UV per face from its dominant axis (no stretched streaks on walls)
    uvl = bm.loops.layers.uv.active
    if not uvl: return
    for f in faces:
        ax = max(range(3), key=lambda k: abs(f.normal[k])); i, j = [(1, 2), (0, 2), (0, 1)][ax]
        for lp in f.loops: lp[uvl].uv = (lp.vert.co[i] / 256.0, lp.vert.co[j] / 256.0)
def sharpen(bm, newf):
    nf = set(newf); ns = 0
    for f in newf: f.smooth = True
    for e in {e for f in newf for e in f.edges}:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > ANG: e.smooth = False; ns += 1
        elif len(e.link_faces) != 2: e.smooth = False
    return ns
for on, om in O.items():
    o = bpy.data.objects[on]; me = o.data; t0 = bvm(om); bm = bmesh.new(); bm.from_mesh(me); n0 = len(bm.faces)
    bm.faces.ensure_lookup_table()
    newf = [f for f in bm.faces if not near(t0, f.calc_center_median(), 2e-3)]; dup = []
    if on == "at_brat_fata_S":                                          # arm walls lying on another piece's surface (z-fighting): that piece shows
        TH_ = [bvm(O[h]) for h in O if h != on]                          # their ORIGINAL surfaces (their new walls are handled below)
        dup = [f for f in newf if any(near(t_, f.calc_center_median(), 2e-2) for t_ in TH_)]
        bmesh.ops.delete(bm, geom=dup, context="FACES"); newf = [f for f in newf if f.is_valid]
    else:
        dup = [f for f in newf if near(tArm, f.calc_center_median(), 2e-2)]
        bmesh.ops.delete(bm, geom=dup, context="FACES"); newf = [f for f in newf if f.is_valid]
    ns = sharpen(bm, newf); box_uv(bm, newf); bm.to_mesh(me); bm.free(); me.update()
    print("CURAT %s: %d -> %d fete; noi %d, dublate cu peretele bratului scoase %d, muchii ascutite %d" % (on, n0, len(me.polygons), len(newf), len(dup), ns))
for gk in ("fata", "spate"):                                           # hatches: sharp rim between the skin and the side (basis + keys unchanged)
    me = bpy.data.objects["at_usa_%s_S" % gk].data; bm = bmesh.new(); bm.from_mesh(me); ns = sharpen(bm, list(bm.faces))
    tA0 = bvm(O["at_brat_fata_S"]); box_uv(bm, [f for f in bm.faces if not near(tA0, f.calc_center_median(), 2e-2)]); bm.to_mesh(me); bm.free()
    print("CURAT at_usa_%s_S: muchii ascutite %d" % (gk, ns))
def mirror_attrs(src, dst):                                            # D = exact mirror, keeping the shape keys of the hatches
    bm = bmesh.new(); bm.from_mesh(src)
    for v in bm.verts: v.co.x = -v.co.x
    sk = bm.verts.layers.shape
    for lay in sk.values():
        for v in bm.verts: v[lay].x = -v[lay].x
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(dst); bm.free(); dst.update()
for s_, d_ in (("at_brat_fata_S", "at_brat_fata_D"), ("at_ureche_S", "at_ureche_D"), ("at_usa_fata_S", "at_usa_fata_D"), ("at_usa_spate_S", "at_usa_spate_D")):
    S, D = bpy.data.objects[s_].data, bpy.data.objects[d_].data
    if S.shape_keys:                                                   # hatches: same vertex order on both sides -> copy keys mirrored
        assert len(S.vertices) == len(D.vertices)
        for kS, kD in zip(S.shape_keys.key_blocks, D.shape_keys.key_blocks):
            for i in range(len(S.vertices)): c = kS.data[i].co; kD.data[i].co = (-c.x, c.y, c.z)
        for i, (eS, eD) in enumerate(zip(S.edges, D.edges)): pass
        bmS = bmesh.new(); bmS.from_mesh(S); bmD = bmesh.new(); bmD.from_mesh(D); bmS.edges.ensure_lookup_table(); bmD.edges.ensure_lookup_table()
        key = lambda e: tuple(sorted(v.index for v in e.verts)); mS = {key(e): e.smooth for e in bmS.edges}
        for e in bmD.edges: e.smooth = mS.get(key(e), e.smooth)
        bmD.to_mesh(D); bmS.free(); bmD.free()
    else:
        mirror_attrs(S, D)
    print("CURAT %s = oglinda %s" % (d_, s_))
bpy.context.scene.frame_set(84); bpy.ops.wm.save_as_mainfile(filepath=OUT)

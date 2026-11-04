# Clean lines pass on the workshop pieces (asked: one more clean lines pass). (1) Thin black ticks / rows of dots on the compartment walls: slivers
# of the hull pieces (carena, PS, frame, ears) left lying exactly on an arm wall, showing through it. A host face goes when its corners, edge middles
# and inner points all lie within COV of an arm face parallel to it (the arm's face stays there, so no hole opens); same for a host's compartment end wall (door y ends YE) with an arm wall parallel within COV2 m along its normal over at least FRAC of its points (the two cross at a shallow angle: rows of dots). (2) Hinge columns: the end caps
# get flat shading and sharp rims (smooth shading gave them pie slices). Usage: blender -b <scene> --python curata_linii.py -- <out.blend>   env COV=.03 DOT=.98 COV2=.7 FRAC=.75 PUSH=.4 XE=60.2
import bpy, bmesh, sys, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree as BV
OUT = sys.argv[sys.argv.index("--") + 1]; COV, DOT, COV2 = float(os.environ.get("COV", .03)), float(os.environ.get("DOT", .98)), float(os.environ.get("COV2", .7)); YE = (-2.6, 57.6, 86.1, 134.1); FRAC = float(os.environ.get("FRAC", .75)); PUSH = float(os.environ.get("PUSH", .4)); XE = float(os.environ.get("XE", 60.2))
bpy.context.scene.frame_set(1); arms = []
for n in ("at_brat_fata_S", "at_brat_fata_D"):
    b = bmesh.new(); b.from_mesh(bpy.data.objects[n].data); arms.append(b)
TR = [BV.FromBMesh(b) for b in arms]
def on_arm(p, n):
    for t in TR:
        q = t.find_nearest(p, COV * 2)
        if q[0] is not None and q[3] < COV and abs(q[1].dot(n)) > DOT: return True
    return False
def covered(p, n):                                                       # an arm wall parallel to the face, within COV2 along its normal
    for t in TR:
        for d in (n, -n):
            q = t.ray_cast(p - d * 1e-4, d, COV2)
            if q[0] is not None and abs(q[1].dot(n)) > .95: return True
    return False
def end_wall(f):                                                         # a compartment end wall of a host, at a door's y end
    c = f.calc_center_median(); return abs(f.normal.y) > .9 and any(abs(c.y - y) < COV2 + .2 for y in YE)
def pts(f):
    V = [v.co for v in f.verts]; c = sum(V, Vector()) / len(V); P = [c] + V
    for i, a in enumerate(V):
        b = V[(i + 1) % len(V)]; m = (a + b) / 2; P += [m, (a + c) / 2, (m + c) / 2, a * .75 + b * .25, a * .25 + b * .75]
    return P
for n in ("at_PS_carena", "at_PS", "at_PS_rama", "at_ureche_S", "at_ureche_D"):
    o = bpy.data.objects[n]; b = bmesh.new(); b.from_mesh(o.data)
    W_ = [f for f in b.faces if end_wall(f) and any(covered(p, f.normal) for p in pts(f))]
    for sx in (-1, 1):                                                   # end walls partly under the arm: split at the arm's flat end, the part under it goes
        G = [f for f in W_ if f.is_valid and min(sx * v.co.x for v in f.verts) < XE < max(sx * v.co.x for v in f.verts)]
        if G:
            bmesh.ops.bisect_plane(b, geom=G + list({e for f in G for e in f.edges}) + list({v for f in G for v in f.verts}), plane_co=(sx * XE, 0, 0), plane_no=(1, 0, 0)); print("LINII %s: %d pereti impartiti la x %.1f" % (n, len(G), sx * XE))
    b.faces.ensure_lookup_table(); b.normal_update()
    dead = [f for f in b.faces if all(on_arm(p, f.normal) for p in pts(f)) or (end_wall(f) and (lambda P: sum(covered(p, f.normal) for p in P) >= FRAC * len(P))(pts(f)))]
    aS = sum(f.calc_area() for f in dead if f.calc_center_median().x < 0); aD = sum(f.calc_area() for f in dead) - aS; big = max((f.calc_area() for f in dead), default=0)
    def sliver(f):                                                       # needle lying along an end wall (a few cm wide, metres long): a dashed line on the wall
        ln = max(e.calc_length() for e in f.edges); return ln > .5 and 2 * f.calc_area() / ln < .05 and all(min(abs(v.co.y - y) for y in YE) < COV2 for v in f.verts) and min(abs(v.co.x) for v in f.verts) > 50
    dead += [f for f in b.faces if f not in set(dead) and sliver(f)]
    D_ = set(dead); push = {}
    for f in b.faces:                                                    # end walls that stay, partly behind an arm wall: pushed back PUSH m (only under the arm, |x| > 60), so they stop crossing it
        if f not in D_ and end_wall(f) and any(covered(p, f.normal) for p in pts(f)):
            y = min(YE, key=lambda t: abs(f.calc_center_median().y - t)); sg = 1 if y in (57.6, 134.1) else -1
            for v in f.verts:
                if abs(v.co.x) > 60 and all(end_wall(g) for g in v.link_faces): push[v] = sg   # not the ones shared with the skin: that opens a slit
    for v, sg in push.items(): v.co.y += sg * PUSH
    if push: print("LINII %s: %d varfuri de perete impinse %.1f m" % (n, len(push), PUSH))
    bmesh.ops.delete(b, geom=dead, context="FACES"); loose = [e for e in b.edges if not e.link_faces]; bmesh.ops.delete(b, geom=loose, context="EDGES")
    b.verts.ensure_lookup_table(); bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context="VERTS")
    b.to_mesh(o.data); o.data.update(); b.free()
    print("LINII %s: %d fete pe peretele bratului scoase, arie x<0 %.2f / x>0 %.2f m2, cea mai mare %.2f m2" % (n, len(dead), aS, aD, big))
done = set()
for o in bpy.data.collections["ATELIER_LAME"].objects:
    if not o.name.startswith("at_spinare_") or o.data in done: continue
    done.add(o.data); b = bmesh.new(); b.from_mesh(o.data); caps = [f for f in b.faces if len(f.verts) > 4]
    for f in caps:
        f.smooth = False
        for e in f.edges: e.smooth = False
    b.to_mesh(o.data); o.data.update(); b.free(); print("LINII %s: %d capace plate" % (o.name, len(caps)))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

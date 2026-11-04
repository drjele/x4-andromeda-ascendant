# Finishes on the workshop pieces (asked: solve the leftovers of the clean lines pass). (1) Arm tips: the small folded flaps at the very tip (non-manifold
# edges near it, a 5 m crease) cut out and closed with a rounded cap up to the old tip point, the skin around relaxed (falloff over RT m). (2) Texture: carena and its doors had collapsed UVs
# (streaks), the arm hundreds of seams (stair-steps in tone): both reprojected continuously from above, (x, y) / S (D mirrored); faces mapped at the walls' scale
# (256 m/uv: compartment walls, hatch sides) are kept on the arm and hatches; on the carena steep faces use their dominant axis. Hatches use the arm's mapping, so they stay invisible when closed.
# Usage: blender -b <scene> --python finisaj.py -- <out.blend>   env RC=2.5 RT=40 NR=6 SIG=8 TF=1 SARM=2665 SCAR=4720
import bpy, bmesh, sys, os, math
from mathutils import Vector
OUT = sys.argv[sys.argv.index("--") + 1]; E = lambda k, d: float(os.environ.get(k, d)); RC, RT, IT, SARM, SCAR = E("RC", 2.5), E("RT", 40), int(E("IT", 80)), E("SARM", 2665), E("SCAR", 4720); NR = int(E("NR", 6)); SIG = E("SIG", 8); TF = E("TF", 1.0)
bpy.context.scene.frame_set(1)
def tip_fix(o):
    b = bmesh.new(); b.from_mesh(o.data); tip = max(b.verts, key=lambda v: v.co.y).co.copy(); bad = set()
    near = lambda v, r: (v.co - tip).length < r
    for e in b.edges:
        if len(e.link_faces) > 2 and near(e.verts[0], 15):
            for v in e.verts: bad.add(v)
    K = {f for f in b.faces if any(near(v, RC) or v in bad for v in f.verts)}
    for _ in range(1): K |= {g for f in K for v in f.verts for g in v.link_faces}
    bmesh.ops.delete(b, geom=list(K), context="FACES"); bmesh.ops.delete(b, geom=[e for e in b.edges if not e.link_faces], context="EDGES"); bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context="VERTS")
    bd = [e for e in b.edges if e.is_boundary and near(e.verts[0], 40)]; adj = {}
    for e in bd:
        for v in e.verts: adj.setdefault(v, []).append(e)
    seen = set(); loops = []
    for e0 in bd:
        if e0 in seen: continue
        L = []; st = [e0]; seen.add(e0)
        while st:
            e = st.pop(); L.append(e)
            for v in e.verts:
                for f in adj[v]:
                    if f not in seen: seen.add(f); st.append(f)
        loops.append(L)
    for L in loops:                                                      # rounded cap: rings from the loop to the old tip point, on an ellipsoid
        ad = {}
        for e in L:
            for v in e.verts: ad.setdefault(v, []).append(e)
        v0 = L[0].verts[0]; e = L[0]; O_ = [v0]
        for _ in range(len(L) - 1): v = e.other_vert(O_[-1]); O_.append(v); e = next(x for x in ad[v] if x is not e)
        lo = next(l for l in L[0].link_loops); same = lo.vert == O_[0]         # same = the neighbour runs along our order, so the cap runs against it
        C = sum((v.co for v in O_), Vector()) / len(O_); ax = tip - C; prev = O_; mi = lo.face.material_index
        def face(q):
            f = b.faces.new(list(reversed(q)) if same else q); f.smooth = True; f.material_index = mi
        for k in range(1, NR + 1):
            th = math.pi / 2 * k / (NR + 1); cur = [b.verts.new(C + (v.co - C) * math.cos(th) + ax * math.sin(th)) for v in O_]
            for i in range(len(O_)): j = (i + 1) % len(O_); face([prev[i], prev[j], cur[j], cur[i]])
            prev = cur
        ap = b.verts.new(tip)
        for i in range(len(O_)): j = (i + 1) % len(O_); face([prev[i], prev[j], ap])
    b.verts.ensure_lookup_table(); Z = [(v, 1 - (v.co - tip).length / RT) for v in b.verts if near(v, RT) and not any(e.is_boundary for e in v.link_edges)]; old = {v: v.co.copy() for v, _ in Z}
    far = [v.co for v in b.verts if RT <= (v.co - tip).length < RT + 8]; ctr = sum(far, Vector()) / len(far); ax_ = (tip - ctr).normalized(); C_ = tip - ax_ * RT * .9   # nose smoothed as a radius over directions from a point inside it: no pucker, no shrink
    D_ = [((v.co - C_).normalized(), (v.co - C_).length) for v, _ in Z]; cs = math.cos(math.radians(3 * SIG)); s2 = 2 * math.radians(SIG) ** 2; new = []
    for (v, w), (d0, r0) in zip(Z, D_):
        sw = sr = 0.0
        for d1, r1 in D_:
            c_ = d0.dot(d1)
            if c_ > cs: g = math.exp(-math.acos(min(1, c_)) ** 2 / s2); sw += g; sr += g * r1
        t_ = min(1, max(0, (RT - (v.co - tip).length) / (RT * TF))); new.append((v, C_ + d0 * (r0 + (sr / sw - r0) * t_ * t_ * (3 - 2 * t_))))
    for v, p in new: v.co = p
    mv = max((v.co - old[v]).length for v in old); nm = sum(len(e.link_faces) > 2 and near(e.verts[0], 15) for e in b.edges); free = sum(e.is_boundary and near(e.verts[0], 40) for e in b.edges)
    for e in b.edges:
        if near(e.verts[0], RT): e.smooth = True
    b.normal_update(); b.to_mesh(o.data); o.data.update(); b.free()
    print("FINISAJ varf %s: %d fete scoase, %d bucle umplute, %d varfuri relaxate, mutare max %.2f m, ne-manifold %d, libere %d" % (o.name, len(K), len(loops), len(Z), mv, nm, free))
OFF = bpy.data.objects["at_PS"].matrix_world.translation.x
def mapped_walls(f, uv, ref=256.0):                                      # a face already at the walls' scale
    R = []
    for l in f.loops:
        d3 = (l.vert.co - l.link_loop_next.vert.co).length; d2 = (l[uv].uv - l.link_loop_next[uv].uv).length
        if d3 > 1e-3: R.append(d3 / max(d2, 1e-9))
    return bool(R) and all(abs(r - ref) < ref * .06 for r in R)
def uv_arm(o, keep=True):
    me = o.data; sg = -1 if o.name.endswith("_D") else 1; dx = o.matrix_world.translation.x - OFF; b = bmesh.new(); b.from_mesh(me); uv = b.loops.layers.uv.active; n = kept = 0
    for f in b.faces:
        if keep and mapped_walls(f, uv): kept += 1; continue
        n += 1
        for l in f.loops: c = l.vert.co; l[uv].uv = (sg * (c.x + dx) / SARM + .5, c.y / SARM + .5)
    if me.shape_keys: b.free(); return uv_loops(o, sg, dx)
    b.to_mesh(me); me.update(); b.free(); print("FINISAJ UV %s: %d reproiectate, %d pastrate" % (o.name, n, kept))
def uv_loops(o, sg, dx):                                                 # hatches: shape keys, so UVs written straight on the mesh (basis = closed position)
    me = o.data; uv = me.uv_layers.active.data; V = me.vertices; n = kept = 0
    if sg < 0:                                                           # D = the mirror of S, polygon by polygon: same UVs, so it is the same mirrored
        ms = bpy.data.objects[o.name[:-1] + "S"].data; us = ms.uv_layers.active.data
        for p, q in zip(me.polygons, ms.polygons):
            m = {ms.loops[l].vertex_index: us[l].uv.copy() for l in q.loop_indices}
            for l in p.loop_indices: uv[l].uv = m[me.loops[l].vertex_index]
        print("FINISAJ UV %s: copiat de la S" % o.name); return
    for p in me.polygons:
        R = []
        I = list(p.loop_indices)
        for i, li in enumerate(I):
            lj = I[(i + 1) % len(I)]; d3 = (V[me.loops[li].vertex_index].co - V[me.loops[lj].vertex_index].co).length; d2 = (uv[li].uv - uv[lj].uv).length
            if d3 > 1e-3: R.append(d3 / max(d2, 1e-9))
        if R and all(abs(r - 256) < 256 * .06 for r in R): kept += 1; continue
        n += 1
        for li in I: c = V[me.loops[li].vertex_index].co; uv[li].uv = (sg * (c.x + dx) / SARM + .5, c.y / SARM + .5)
    print("FINISAJ UV %s: %d reproiectate, %d pastrate" % (o.name, n, kept))
def uv_carena(o):
    me = o.data; dx = o.matrix_world.translation.x - OFF if not o.animation_data else 0.0; b = bmesh.new(); b.from_mesh(me); uv = b.loops.layers.uv.active
    for f in b.faces:
        n = f.normal; ax = 2 if abs(n.z) >= .6 else (1 if abs(n.y) >= abs(n.x) else 0)
        for l in f.loops:
            c = l.vert.co; p = (abs(c.x + dx), c.y, c.z)                 # |x|: S and D mirrored
            l[uv].uv = ((p[0], p[1]) if ax == 2 else (p[0], p[2]) if ax == 1 else (p[1], p[2]))[0] / SCAR + .5, ((p[0], p[1]) if ax == 2 else (p[0], p[2]) if ax == 1 else (p[1], p[2]))[1] / SCAR + .5
    b.to_mesh(me); me.update(); b.free(); print("FINISAJ UV %s: %d fete, de sus / pe axa dominanta" % (o.name, len(me.polygons)))
for n in ("at_brat_fata_S", "at_brat_fata_D"): tip_fix(bpy.data.objects[n])
for n in ("at_brat_fata_S", "at_brat_fata_D", "at_usa_fata_S", "at_usa_fata_D", "at_usa_spate_S", "at_usa_spate_D"): uv_arm(bpy.data.objects[n])
for n in ("at_PS_carena", "at_usa_carena_F_S", "at_usa_carena_F_D", "at_usa_carena_B_S", "at_usa_carena_B_D"): uv_carena(bpy.data.objects[n])
bpy.ops.wm.save_as_mainfile(filepath=OUT)

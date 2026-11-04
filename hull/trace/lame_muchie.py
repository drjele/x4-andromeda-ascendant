# Thin black edge all around every blade (asked): each blade's two big faces (regions between edges sharper than ANG degrees) get a ring W m wide along
# their outline (inset, same surface, so the blade's shape does not change); the ring and the side walls take a black material, the rest stays red.
# Checks: each _D still the mirror of its _S at sample frames. Usage: blender -b <scene> --python lame_muchie.py -- <out.blend> [prefix=an_]   env W=1.5 ANG=40
import bpy, bmesh, sys, os, math, numpy as np
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree as BV
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; PR = a[1] if len(a) > 1 else "an_"; W, ANG = float(os.environ.get("W", 1.5)), math.radians(float(os.environ.get("ANG", 40)))
mb = bpy.data.materials.get("lame_muchie_negru") or bpy.data.materials.new("lame_muchie_negru"); mb.diffuse_color = (.005, .005, .005, 1); mb.use_nodes = True; mb.roughness = .5
bs = mb.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value = (.005, .005, .005, 1)
L = sorted((o for o in bpy.data.objects if o.name.startswith(PR + "lama_") and o.type == "MESH"), key=lambda o: o.name)
for o in L:
    me = o.data
    if mb.name not in me.materials: me.materials.append(mb)
    ib = me.materials.find(mb.name); b = bmesh.new(); b.from_mesh(me); b.faces.ensure_lookup_table(); seen = set(); reg = []
    ORI = BV.FromBMesh(b); old = set(b.verts)                            # the original blade: the ring stays on it
    for f0 in b.faces:
        if f0 in seen: continue
        seen.add(f0); st = [f0]; R = []
        while st:
            f = st.pop(); R.append(f)
            for e in f.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) < ANG:
                    g = e.link_faces[0] if e.link_faces[1] is f else e.link_faces[1]
                    if g not in seen: seen.add(g); st.append(g)
        reg.append(R)
    reg.sort(key=lambda R: -sum(f.calc_area() for f in R)); big = reg[:2]; rest = [f for R in reg[2:] for f in R]; ar = [sum(f.calc_area() for f in R) for R in reg]
    ring = 0
    for R in big:
        RS = set(R); bd = [e for e in {e for f in R for e in f.edges} if sum(g in RS for g in e.link_faces) == 1]; ad = {}   # the outline, walked in order
        for e in bd:
            for v in e.verts: ad.setdefault(v, []).append(e)
        B = []; AR = []; TOT = []; left = set(bd); arc = 0.0
        while left:
            e0 = next(iter(left)); v = e0.verts[0]; e = e0; i0 = len(B); arc = 0.0
            while e in left:
                left.discard(e); B.append(v.co.copy()); AR.append(arc); TOT.append(i0); arc += e.calc_length(); v = e.other_vert(v); e = next((x for x in ad[v] if x is not e), e)
            for i in range(i0, len(B)): TOT[i] = arc
        kt = KDTree(len(B))
        for i, p_ in enumerate(B): kt.insert(p_, i)
        kt.balance()
        def opposite(i):                                                  # nearest outline point on the blade's other side
            best = (1e9, None)
            for co, j, dd in kt.find_range(B[i], 8 * W):
                ad_ = abs(AR[i] - AR[j]); ad_ = min(ad_, TOT[i] - ad_) if TOT[i] == TOT[j] else 1e9
                if ad_ > 2.5 * dd and dd < best[0]: best = (dd, co)
            return best
        res = bmesh.ops.inset_region(b, faces=R, use_boundary=True, use_even_offset=True, thickness=W, depth=0)
        RG = set(res["faces"]); IN = {v for f in RG for v in f.verts if any(g in RS for g in v.link_faces)}
        for c in IN:                                                      # narrow tips: the ring tapers to nothing towards the point, it never leaves the blade; corners at most 1.6 W
            a_ = next((e.other_vert(c) for e in c.link_edges if all(g in RG for g in e.link_faces) and e.other_vert(c) not in IN), None); q0 = a_.co if a_ else c.co
            co, i, _ = kt.find(q0); w_, r_ = opposite(i)
            if r_ is not None and w_ < 2.2 * W / .9: c.co = co + (r_ - co).normalized() * .45 * w_
            elif (c.co - co).length > 1.6 * W: c.co = co + (c.co - co).normalized() * 1.6 * W
        for f in res["faces"]:
            f.material_index = ib; f.smooth = False; ring += 1
            for e in f.edges: e.smooth = False                           # sharp ring edges: the red faces keep their own normals
    for f in rest: f.material_index = ib
    sn = 0
    for v in b.verts:                                                    # anything an inset pushed off the blade goes back on its surface
        q = ORI.find_nearest(v.co)
        if q[0] is not None and q[3] > 1e-3: v.co = q[0]; sn += 1
    b.to_mesh(me); me.update(); b.free()
    print("MUCHIE %s: fete mari %.0f + %.0f m2, %d regiuni de perete %.0f m2, inel %d fete, %d fete total, %d varfuri readusi pe lama" % (o.name, ar[0], ar[1], len(reg) - 2, sum(ar[2:]), ring, len(me.polygons), sn))
def world(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh(); P = np.empty(3 * len(m.vertices)); m.vertices.foreach_get("co", P); e.to_mesh_clear()
    M = np.array(o.matrix_world); return P.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
Cn = bpy.data.objects[PR + "PS"].location.x; wm = 0.0; sc = bpy.context.scene
for f in (1, 30, 84, 130):
    sc.frame_set(f)
    for o in L:
        if o.name.endswith("_S"):
            S = world(o); S[:, 0] = 2 * Cn - S[:, 0]; D = world(bpy.data.objects[o.name[:-1] + "D"])
            wm = max(wm, np.abs(D[np.lexsort(D.round(2).T)] - S[np.lexsort(S.round(2).T)]).max() if len(S) == len(D) else 1e9)
print("MUCHIE D = oglinda S, abatere max %.4f m" % wm); sc.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=OUT)

# The PS split into its 2 components the way it is made (asked: PS is flat on the bottom and the trapezoid / triangular
# keel under it is applied onto that bottom - that is the second piece). The bottom's flat level (lowest of the flat bottom
# around the keel) is a plane z = ZF; the object is cut there: above = the PS with a flat bottom (the cut capped), below =
# the keel (capped on top on the same plane, so the two sit face to face); bits below the plane outside the keel (smaller
# than MIN_V vertices) stay with the PS, flattened. Both closed. The object gets its own mesh (PS, linked, untouched).
# Usage: blender -b <in> --python ps_carena.py -- <out.blend> <obj> <ZF> <keel_name>
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; OUT, NAME, ZF, KN = a[0], a[1], float(a[2]), a[3]
o = bpy.data.objects[NAME]; o.data = o.data.copy(); mw = o.matrix_world; zl = (mw.inverted() @ Vector((0, 0, ZF))).z
def cut(keep_above):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, zl), plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    bm.edges.ensure_lookup_table(); ed = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
    bmesh.ops.holes_fill(bm, edges=ed, sides=0); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    if not keep_above:                                 # the keel = the biggest part below; slivers dropped
        parts, seen = [], set()
        for v in bm.verts:
            if v in seen: continue
            st, comp = [v], []
            seen.add(v)
            while st:
                u = st.pop(); comp.append(u)
                for e in u.link_edges:
                    w = e.other_vert(u)
                    if w not in seen: seen.add(w); st.append(w)
            parts.append(comp)
        parts.sort(key=len); drop = [v for p in parts[:-1] for v in p]
        if drop: bmesh.ops.delete(bm, geom=drop, context="VERTS")
        print("CARENA: %d bucati sub plan, pastrata cea mare (%d varfuri), scoase %d varfuri" % (len(parts), len(parts[-1]), len(drop)))
    me = bpy.data.meshes.new(NAME if keep_above else KN); bm.to_mesh(me); bm.free()
    for m in o.data.materials: me.materials.append(m)
    return me
up, dn = cut(True), cut(False)
k = bpy.data.objects.new(KN, dn); k.matrix_world = mw.copy()
for c in o.users_collection: c.objects.link(k)
o.data = up
for ob in (o, k):
    bm = bmesh.new(); bm.from_mesh(ob.data); nb = sum(1 for e in bm.edges if not e.is_manifold); bm.free()
    print("PIESA %s: %d fete, muchii ne-manifold %d" % (ob.name, len(ob.data.polygons), nb))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

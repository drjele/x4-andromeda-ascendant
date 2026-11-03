# Long thin triangles split (asked: clean surfaces pass; PS's top had diagonal shading streaks from its flat zone's corners - the zone
# was a few huge triangles, edges up to 256 m, fanned into the dense ring around it, and smooth shading smeared the normals along
# them): every edge longer than MAXL on faces facing up (normal z > NZ) split at its middle, repeated until none is left, the new
# n-gons triangulated (beauty). The new points lie on the old triangles - the shape does not move; only the shading changes.
# ZONA=x0,x1,y0,y1 (ship coords, mesh coords here): only edges whose middle lies in that box (the flat zone), so the rest of the
# mesh is not touched (splitting everywhere quadrupled PS and left 14 non-manifold edges). Duplicate faces from the fill are removed.
# Usage: blender -b <in.blend> --python imparte_triunghiuri_lungi.py -- <out.blend> <obj,...> ; env MAXL=4 NZ=0.35 IT=12 ZONA=-80,80,29,280
import bpy, sys, os, bmesh, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; E = lambda k, d: float(os.environ.get(k, d)); MAXL, NZ, IT = E("MAXL", 4), E("NZ", .35), int(E("IT", 12))
Z = [float(q) for q in os.environ["ZONA"].split(",")] if os.environ.get("ZONA") else None
def inz(e):
    if Z is None: return True
    m = (e.verts[0].co + e.verts[1].co) / 2; return Z[0] <= m.x <= Z[1] and Z[2] <= m.y <= Z[3]
for nm in a[1].split(","):
    o = bpy.data.objects[nm]; me = o.data; bm = bmesh.new(); bm.from_mesh(me); n0 = len(bm.faces)
    V0 = np.array([v.co[:] for v in bm.verts]); bm.normal_update()
    for it in range(IT):
        bm.normal_update()
        E_ = [e for e in bm.edges if e.calc_length() > MAXL and e.link_faces and all(f.normal.z > NZ for f in e.link_faces) and inz(e)]
        if not E_: break
        r = bmesh.ops.subdivide_edges(bm, edges=E_, cuts=1, use_grid_fill=False)
        ng = [f for f in bm.faces if len(f.verts) > 3]
        if ng: bmesh.ops.triangulate(bm, faces=ng, quad_method="BEAUTY", ngon_method="BEAUTY")
        seen = {}
        for f in list(bm.faces):
            k = frozenset(f.verts)
            if k in seen: bm.faces.remove(f)
            else: seen[k] = f
    bm.normal_update()
    left = sum(1 for e in bm.edges if e.calc_length() > MAXL and e.link_faces and all(f.normal.z > NZ for f in e.link_faces) and inz(e))
    free = sum(1 for e in bm.edges if len(e.link_faces) == 1); nmf = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bm.to_mesh(me); me.update()
    print("IMPARTIT %s: fete %d -> %d, muchii lungi ramase %d, libere %d, ne-manifold %d, treceri %d" % (nm, n0, len(me.polygons), left, free, nmf, it + 1))
bpy.ops.wm.save_as_mainfile(filepath=a[0])

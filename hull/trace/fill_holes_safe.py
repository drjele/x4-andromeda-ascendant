# See-through holes closed without touching the original surface: in the objects of the given collections, seams split
# by the importer welded (distance WELD), boundary loops filled, and only the NEW faces oriented — each one flipped if its
# winding runs the same way as the existing face across a shared edge (consistent neighbours) — so no original face is
# ever turned over (a global normal recalculation flips whole regions of open, curve-built meshes).
# Usage: blender -b <in.blend> --python fill_holes_safe.py -- <out.blend> <collection_prefix> [...]
import bpy, bmesh, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, PREF = a[0], tuple(a[1:]); WELD = 0.05
def boundary(bm): return sum(1 for e in bm.edges if e.is_boundary)
tot0 = tot1 = 0
for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and any(c.name.startswith(PREF) for c in o.users_collection)]:
    bm = bmesh.new(); bm.from_mesh(o.data); b0 = boundary(bm)
    if not b0: bm.free(); continue
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
    old = set(bm.faces); res = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    new = [f for f in res["faces"]]
    tri = bmesh.ops.triangulate(bm, faces=new); new = [f for f in bm.faces if f not in old]
    for _ in range(3):                                                    # orient new faces from their old neighbours, then from each other
        for f in new:
            for e in f.edges:
                nb = [g for g in e.link_faces if g is not f and (g in old or getattr(g, "tag", False))]
                if not nb: continue
                g = nb[0]; v0, v1 = e.verts
                def order(face):
                    vs = list(face.verts); i, j = vs.index(v0), vs.index(v1); return (j - i) % len(vs) == 1
                if order(f) == order(g): f.normal_flip()
                f.tag = True; break
    b1 = boundary(bm); bm.to_mesh(o.data); bm.free(); tot0 += b0; tot1 += b1
print("HOLES open edges %d -> %d" % (tot0, tot1))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

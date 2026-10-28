# Reference piece copied with its holes covered (asked: copy R002 169_C directly and cover every hole in its surface, so it
# is continuous): a copy of the reference mesh (same UVs and materials), the importer's split seams welded (WELD m), then
# every boundary loop shorter than PMAX filled (the holes and slots in the surface; the sheet's long open borders, under
# the deck and round the loops, left open), the new faces triangulated (beauty), oriented like their neighbours (never an
# original face turned) and given the material of the face across their edge. Placed where the exploded new piece is
# (that one hidden), name <src>_umplut. Usage: blender -b <f.blend> --python ref_umplut.py -- <out.blend> <src> <x_offset>
import bpy, bmesh, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SRC, DXO = a[0], a[1], float(a[2])
WELD, PMAX = float(os.environ.get("UMP_SUDURA", "0.05")), float(os.environ.get("UMP_PERIMETRU", "4000"))
e_ = bpy.data.objects["expl_" + SRC]; o = e_.copy(); o.data = e_.data.copy(); o.name = SRC.split()[-1] + "_umplut"
col = bpy.data.collections.get("PS_UMPLUT") or bpy.data.collections.new("PS_UMPLUT")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for x in list(col.objects): bpy.data.objects.remove(x)
col.objects.link(o); o.location.x += DXO
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
def loops():
    seen, out = set(), []
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st, comp = [e], []; seen.add(e)
        while st:
            x = st.pop(); comp.append(x)
            for v in x.verts:
                for f in v.link_edges:
                    if f.is_boundary and f not in seen: seen.add(f); st.append(f)
        out.append(comp)
    return out
L0 = loops(); small = [c for c in L0 if sum(e.calc_length() for e in c) < PMAX]
old = set(bm.faces); res = bmesh.ops.holes_fill(bm, edges=[e for c in small for e in c], sides=0); new = list(res["faces"])
tri = bmesh.ops.triangulate(bm, faces=new, quad_method="BEAUTY", ngon_method="BEAUTY"); new = tri["faces"]
newset = set(new)
for f in new:                                                          # orientation and material from the original neighbour
    for e in f.edges:
        nb = [g for g in e.link_faces if g is not f and g not in newset]
        if not nb: continue
        g = nb[0]; f.material_index = g.material_index
        v0, v1 = e.verts; i_f = list(f.verts).index(v0); i_g = list(g.verts).index(v0)
        same = f.verts[(i_f + 1) % len(f.verts)] is v1 and g.verts[(i_g + 1) % len(g.verts)] is v1
        if same: f.normal_flip()
        break
for f in new: f.smooth = True
L1 = sorted([sum(e.calc_length() for e in c) for c in loops()], reverse=True); bm.to_mesh(o.data); bm.free()
print("UMPLUT %s: %d gauri dupa sudura, %d umplute (perimetru < %.0f m) cu %d fete noi; raman deschise %d margini mari (%s m)" % (
    o.name, len(L0), len(small), PMAX, len(new), len(L1), ", ".join("%.0f" % p for p in L1[:5])))
en = bpy.data.objects.get("expl_piesa_comp_169_C")
if en: en.hide_set(True); en.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

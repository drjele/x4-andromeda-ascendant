# The exploded reference body split like the new pieces (asked: separate expl_R002 169_C into PS and arms too): a copy cut by
# the plane y = YC (exact cut, faces split), the front part = <name>_PS, the rear part split by side = <name>_brat_S (x < middle)
# and <name>_brat_D; same place, same materials; the whole original hidden (kept). Usage: blender -b <f.blend> --python
# ref_separa.py -- <out.blend> [object] [yc]
import bpy, bmesh, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; NAME = a[1] if len(a) > 1 else "expl_R002 169_C"; YC = float(a[2]) if len(a) > 2 else -60.0
src = bpy.data.objects[NAME]; xs_ = [v.co.x for v in src.data.vertices]; xm = (min(xs_) + max(xs_)) / 2   # its middle (local x)
col = bpy.data.collections.get("REF_SEPARATA") or bpy.data.collections.new("REF_SEPARATA")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def part(suffix, keep):
    o = src.copy(); o.data = src.data.copy(); o.name = NAME + suffix; col.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, YC, 0), plane_no=(0, 1, 0))
    gone = [f for f in bm.faces if not keep(f.calc_center_median())]; bmesh.ops.delete(bm, geom=gone, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    n = len(bm.faces); bm.to_mesh(o.data); bm.free(); print("PARTE %s: %d fete" % (o.name, n))
part("_PS", lambda c: c.y >= YC)
part("_brat_S", lambda c: c.y < YC and c.x < xm)
part("_brat_D", lambda c: c.y < YC and c.x >= xm)
src.hide_set(True); src.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

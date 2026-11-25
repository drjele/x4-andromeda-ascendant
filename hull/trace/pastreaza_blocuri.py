# Board reduced to the named blocks: every object outside their collection trees removed, collections left empty removed,
# and of the labels only the listed ones kept (kept collection trees are never unlinked, so nested pieces cannot be orphaned).
# Usage: blender -b <in.blend> --python pastreaza_blocuri.py -- <out.blend> <collection to keep>,... <label object to keep>,...
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; OUT, KEEP, LAB = a[0], set(a[1].split(",")), set(a[2].split(","))
lip = [n for n in KEEP | LAB if n not in bpy.data.collections and n not in bpy.data.objects]
if lip: sys.exit("LIPSESC %s" % lip)
tree = set()
def walk(c):
    tree.add(c.name)
    for ch in c.children: walk(ch)
for n in KEEP: walk(bpy.data.collections[n])
keep_obs = {o for n in KEEP for o in bpy.data.collections[n].all_objects} | {bpy.data.objects[n] for n in LAB}
inainte = len(bpy.data.objects)
for o in list(bpy.data.objects):
    if o not in keep_obs: bpy.data.objects.remove(o)
for c in sorted(bpy.data.collections, key=lambda c: -len(c.children_recursive)):
    if c.name not in tree and not c.all_objects: bpy.data.collections.remove(c)
for _ in range(3): bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
for n in sorted(KEEP): print("PASTRAT", n, len(bpy.data.collections[n].all_objects))
print("OBIECTE %d -> %d" % (inainte, len(bpy.data.objects)), "colectii", sorted(c.name for c in bpy.data.collections))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SALVAT", OUT)

# The complete new ship beside the reference (x + DX): the regenerated parts (red nacelles, front arms) plus every other
# reference A piece copied as it is (linked copy, same mesh data, moved by DX). Left out: the reference pieces the new
# parts replace - the front arms (022_S, 019_D), the plates now inside the arm (085, 098) and the red ribs inside the
# nacelle (the small rib pieces of piese_medii found within 4 m of the new surfaces, decided on the _S side and taken on
# both sides, symmetry). The reference collections stay untouched.
# Usage: blender -b <arm.blend> --python assemble_new.py -- <replaced.json> <out.blend> <dx>
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]; RJ, OUT, DX = a[0], a[1], float(a[2]); sc = bpy.context.scene
res = json.load(open(RJ)); key = lambda n: n.split()[-1]
ribs = {key(n)[:-2] for f, n, c, nf in res if f > 0.7 and c == "piese_medii" and nf <= 200 and key(n).endswith("_S")}
replaced = {"022_S", "019_D", "085_S", "085_D", "098_S", "098_D"} | {r + s for r in ribs for s in ("_S", "_D")}
col = bpy.data.collections.new("NAVA_NOUA"); sc.collection.children.link(col)
kept, left = 0, []
for cn in ("piese_mari", "piese_medii", "marunte"):
    for o in bpy.data.collections[cn].all_objects:
        if o.type != "MESH": continue
        if key(o.name) in replaced: left.append(o.name); continue
        c = o.copy(); col.objects.link(c); c.location.x += DX; c.name = "nou_" + o.name; c.hide_set(False); c.hide_render = False; kept += 1
for n in ("nacela_rosie_S", "nacela_rosie_D", "brat_fata_S", "brat_fata_D"):
    o = bpy.data.objects[n]
    for u in list(o.users_collection): u.objects.unlink(o)
    col.objects.link(o)
for c in sc.collection.children:                                            # the file opens on the new ship only
    if c.name != "NAVA_NOUA": bpy.context.view_layer.layer_collection.children[c.name].exclude = True
print("NAVA NOUA: %d piese copiate din A + 4 piese noi (nacele, brate); lasate deoparte (inlocuite): %d: %s" % (kept, len(left), " ".join(sorted(key(n) for n in left))))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

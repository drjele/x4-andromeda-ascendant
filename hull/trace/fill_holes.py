# Close the small holes left in the parts' surfaces (e.g. two at the top junction of the arms, which the red wings
# showed through): every border loop of at most `sides` edges gets capped; long borders (the fillets' open skirts,
# the deck's edge) are left alone.
# Usage: blender -b --python fill_holes.py [-- sides]
import bpy, bmesh, sys
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
SIDES = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 40
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; log = []
for o in sc.objects:
    if o.type != "MESH" or o.name.startswith("source"): continue
    bm = bmesh.new(); bm.from_mesh(o.data); before = len(bm.faces)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=SIDES)
    if len(bm.faces) > before:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:]); bm.to_mesh(o.data); o.data.update(); log.append("%s +%d" % (o.name, len(bm.faces) - before))
    bm.free()
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("HOLES", "; ".join(log) or "none")

# Lift the body's top decorations onto the raised rear deck (C22): the deck grew over them in pass 6 and buried
# the shoulders, the dome, the stern eyes and the crescent. Each point rises by the deck's height above the body at
# its x/y, relaxed over the mesh so a decoration crossing the deck's edge bends instead of tearing.
# Usage: blender -b --python deck_lift.py
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
LIFT = ["dorsal_shoulder", "rear_shoulder", "dorsal_dome", "stern_eyes", "stern_eyes_inner", "dorsal_crescent", "stern_window"]
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
def tree(names):
    b = bmesh.new()
    for n in names:
        o = sc.objects[n]; k = len(b.verts); b.from_mesh(o.data); b.verts.ensure_lookup_table()
        for v in b.verts[k:]: v.co = o.matrix_world @ v.co
    return BVHTree.FromBMesh(b)
body, deck = tree(["corp"]), tree(["corp", "rear_deck"]); down = Vector((0, 0, -1)); done = []
def top(t, p):
    h = t.ray_cast(Vector((p.x, p.y, 3000)), down); return h[0].z if h[0] is not None else None
for name in LIFT:
    o = sc.objects.get(name)
    if o is None: continue
    M = o.matrix_world; W = [M @ v.co for v in o.data.vertices]; dz = []
    for p in W:
        zb, zd = top(body, p), top(deck, p); dz.append(max(0.0, zd - zb) if zb is not None and zd is not None else 0.0)
    nb = [[] for _ in W]
    for e in o.data.edges: a, b = e.vertices; nb[a].append(b); nb[b].append(a)
    for _ in range(12): dz = [0.5 * d + 0.5 * (sum(dz[j] for j in n) / len(n)) if n else d for d, n in zip(dz, nb)]
    Mi = M.inverted()
    for v, p, d in zip(o.data.vertices, W, dz): v.co = Mi @ (p + Vector((0, 0, d)))
    o.data.update(); done.append(f"{name} +{max(dz):.0f}m")
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("LIFTED", done)

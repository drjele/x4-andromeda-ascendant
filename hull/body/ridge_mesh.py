import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body"
R = json.load(open(f"{D}/ridges.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in R]: bpy.data.objects.remove(o)
bb = bmesh.new(); bb.from_mesh(sc.objects["corp"].data); tree = BVHTree.FromBMesh(bb)
SINK = 2.0
for name, p in R.items():
    if name.startswith("_"): continue
    pts = []
    y = p["y_front"]
    while True:
        hit, n, _, _ = tree.ray_cast(Vector((0, y, -3000)), Vector((0, 0, 1)), 6000)
        if hit is None or n.y < -0.6: break
        pts.append((hit, n)); y -= 4
    z = pts[-1][0].z
    while z < p["z_end"]:
        hit, n, _, _ = tree.ray_cast(Vector((0, -3000, z)), Vector((0, 1, 0)), 6000)
        if hit: pts.append((hit, n))
        z += 3
    # smooth the path and normals a little
    sm = []
    for i in range(len(pts)):
        win = pts[max(0, i - 3): i + 4]
        sm.append((sum((q for q, _ in win), Vector()) / len(win), sum((m for _, m in win), Vector()).normalized()))
    L = [0.0]
    for a, b in zip(sm, sm[1:]): L.append(L[-1] + (b[0] - a[0]).length)
    bm = bmesh.new(); secs = []
    for i, (pt, n) in enumerate(sm):
        tan = (sm[min(i + 1, len(sm) - 1)][0] - sm[max(i - 1, 0)][0]).normalized()
        side = tan.cross(n).normalized()
        k = min(1.0, L[i] / p["taper"]); k = k * k * (3 - 2 * k)
        h = p["height"] * k; w = p["half"] * (0.3 + 0.7 * k)
        secs.append([bm.verts.new(pt - side * w - n * SINK), bm.verts.new(pt + n * max(h, 0.2)), bm.verts.new(pt + side * w - n * SINK)])
    for a, b in zip(secs, secs[1:]):
        for j in range(3): bm.faces.new((a[j], b[j], b[(j + 1) % 3], a[(j + 1) % 3]))
    bm.faces.new(secs[0]); bm.faces.new(list(reversed(secs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me)
    sc.collection.objects.link(bpy.data.objects.new(name, me))
bpy.data.libraries.write(f"{D}/body_v2.blend", {sc}, fake_user=True)
print("RIDGES ok")

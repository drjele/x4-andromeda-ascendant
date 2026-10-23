# Hangar decks inside the Y of each link: thin level plates stacked in the tunnel between the two branches,
# running from the body fillet to the wing's underside, open toward the bow.
import bpy, bmesh, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/links/h_params.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name in ("hangar_r", "hangar_l")]: bpy.data.objects.remove(o)
b = bmesh.new()
for n in ("corp", "link_r"): b.from_mesh(sc.objects[n].data)
T = BVHTree.FromBMesh(b)
bm = bmesh.new(); t = P["thick"] / 2
for z in P["levels"]:
    ys = np.arange(P["y"][0], P["y"][1] + 0.1, P["step"]); spans = []
    for y in ys:
        a, an = T.ray_cast(Vector((238, y, z)), Vector((-1, 0, 0)), 250)[:2]; c, cn = T.ray_cast(Vector((238, y, z)), Vector((1, 0, 0)), 300)[:2]
        # the hits must be the flank and the wing's underside facing the tunnel, else the row lies inside
        # the closed stern of the Y and gets no deck
        spans.append((a.x - P["inset"][0], c.x + P["inset"][1]) if a is not None and c is not None and an.x > 0 and cn.x < 0 and cn.z < 0.3 and c.x - a.x > 8 else None)
    # the front corners round off so each deck reads as a lip, not a cut box
    rows = []
    for y, sp in zip(ys, spans):
        if sp is None: rows.append(None); continue
        k = np.clip((P["y"][1] - y) / P["round"], 0, 1); w = sp[1] - sp[0]; inset = (1 - np.sqrt(1 - (1 - k) ** 2)) * min(P["round"], w / 2)
        x0, x1 = sp[0], sp[1] - inset
        xs = np.linspace(x0, x1, 12)
        rows.append([(bm.verts.new((x, y, z + t)), bm.verts.new((x, y, z - t))) for x in xs])
    for r0, r1 in zip(rows, rows[1:]):
        if r0 is None or r1 is None: continue
        for i in range(11):
            bm.faces.new((r0[i][0], r0[i + 1][0], r1[i + 1][0], r1[i][0])); bm.faces.new((r0[i][1], r1[i][1], r1[i + 1][1], r0[i + 1][1]))
        bm.faces.new((r0[11][0], r0[11][1], r1[11][1], r1[11][0])); bm.faces.new((r0[0][0], r1[0][0], r1[0][1], r0[0][1]))
    if not any(rows): continue
    for r in (next(r for r in rows if r), next(r for r in reversed(rows) if r)):
        for i in range(11): bm.faces.new((r[i][0], r[i][1], r[i + 1][1], r[i + 1][0]))
# the back wall of the hangar: a dark plate across the tunnel where the Y closes, so no wing colour shows inside
yb = P["y"][0] + 1.0; cell = 2.0; G = {}
def inside(x, z):
    # a cell is in the tunnel when it sees a ceiling above, a floor below, the flank inboard and the wing outboard
    o = Vector((x, yb, z)); hits = [T.ray_cast(o, Vector(dv), 400)[:2] for dv in ((0, 0, 1), (0, 0, -1), (-1, 0, 0), (1, 0, 0))]
    return all(h[0] is not None for h in hits) and hits[0][1].z < 0 and hits[1][1].z > 0 and hits[2][1].x > 0 and hits[3][1].x < 0
for i, x in enumerate(np.arange(180, 460, cell)):
    for j, z in enumerate(np.arange(-140, 160, cell)):
        if inside(x, z): G[(i, j)] = (x, z)
V = {}
def vert(i, j):
    if (i, j) not in V: V[(i, j)] = bm.verts.new((180 + i * cell - cell / 2, yb, -140 + j * cell - cell / 2))
    return V[(i, j)]
for (i, j) in G: bm.faces.new((vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("hangar_r"); bm.to_mesh(me)
sc.collection.objects.link(bpy.data.objects.new("hangar_r", me))
ml = me.copy(); ml.name = "hangar_l"; ml.transform(Matrix.Scale(-1, 4, (1, 0, 0))); ml.flip_normals()
sc.collection.objects.link(bpy.data.objects.new("hangar_l", ml))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("HANGARS ok", len(me.polygons))

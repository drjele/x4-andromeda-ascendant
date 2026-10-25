# Hangar decks inside the Y of each link: level plates stacked in the tunnel between the two branches,
# running from the body fillet to the wing's underside, open toward the bow; optionally (h_params "slats") the slat
# battery at the back of the recess, thin horizontal blades with gaps between the decks.
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
SL = P.get("slats"); slats = [z for z in np.arange(SL["z"][0], SL["z"][1] + 0.1, SL["pitch"]) if min(abs(z - l) for l in P["levels"]) > SL["clear"]] if SL else []
for z in P["levels"] + slats:
    deck = z in P["levels"]; t = (P["thick"] if deck else SL["thick"]) / 2
    ys = np.arange(P["y"][0], (P["y"][1] if deck else SL["y"][1]) + 0.1, P["step"]); spans = []
    for y in ys:
        a, an = T.ray_cast(Vector((238, y, z)), Vector((-1, 0, 0)), 250)[:2]; c, cn = T.ray_cast(Vector((238, y, z)), Vector((1, 0, 0)), 300)[:2]
        # the hits must be the flank and the Y's outer wall facing into the tunnel, else the row lies inside
        # the closed stern of the Y and gets no deck
        if a is None or c is None or an.x <= 0 or cn.x >= -0.2 or c.x - a.x <= 8: spans.append(None); continue
        # the plate keeps only the stretch that lies in the cavity: ceiling above and floor (or the body) below its
        # faces, so it ends where the floor climbs to the ceiling at the back instead of poking out of the link
        xs_ = np.arange(a.x + 1, c.x - 0.5, 2.0); ok = []
        for x in xs_:
            up = T.ray_cast(Vector((x, y, z + t + 0.5)), Vector((0, 0, 1)), 300)[:2]; dn = T.ray_cast(Vector((x, y, z - t - 0.5)), Vector((0, 0, -1)), 300)[:2]
            ok.append(up[0] is not None and dn[0] is not None and up[1].z < 0.2 and dn[1].z > -0.2)
        best, run = (0, -1), None
        for i, k in enumerate(ok + [False]):
            if k and run is None: run = i
            if not k and run is not None:
                if i - 1 - run > best[1] - best[0]: best = (run, i - 1)
                run = None
        if best[1] - best[0] < 4: spans.append(None); continue
        x0 = a.x - P["inset"][0] if best[0] == 0 else xs_[best[0]]; x1 = c.x + P["inset"][1] if best[1] == len(xs_) - 1 else xs_[best[1]]
        spans.append((x0, x1))
    # the front corners round off so each deck reads as a lip, not a cut box
    rows = []
    for y, sp in zip(ys, spans):
        if sp is None: rows.append(None); continue
        k = np.clip((P["y"][1] - y) / P["round"], 0, 1); w = sp[1] - sp[0]; inset = (1 - np.sqrt(1 - (1 - k) ** 2)) * min(P["round"], w / 2)
        x0, x1 = sp[0], sp[1] - inset
        xs = np.linspace(x0, x1, 12)
        rows.append([(bm.verts.new((x, y, z + t)), bm.verts.new((x, y, z - t))) for x in xs])
    rows = [r if r and ((i and rows[i - 1]) or (i + 1 < len(rows) and rows[i + 1])) else None for i, r in enumerate(rows)]   # a lone row has no deck to cap
    rows = [r if r and ((i and rows[i - 1]) or (i + 1 < len(rows) and rows[i + 1])) else None for i, r in enumerate(rows)]   # a lone row has no deck to cap
    for r0, r1 in zip(rows, rows[1:]):
        if r0 is None or r1 is None: continue
        for i in range(11):
            bm.faces.new((r0[i][0], r0[i + 1][0], r1[i + 1][0], r1[i][0])); bm.faces.new((r0[i][1], r1[i][1], r1[i + 1][1], r0[i + 1][1]))
        bm.faces.new((r0[11][0], r0[11][1], r1[11][1], r1[11][0])); bm.faces.new((r0[0][0], r1[0][0], r1[0][1], r0[0][1]))
    if not any(rows): continue
    for r in (next(r for r in rows if r), next(r for r in reversed(rows) if r)):
        for i in range(11): bm.faces.new((r[i][0], r[i][1], r[i + 1][1], r[i + 1][0]))
# the back wall of the hangar (off by default: the two branches of the Y close in a V by themselves)
yb = P["y"][0] + 1.0; cell = 2.0; G = {}
def inside(x, z):
    # a cell is in the tunnel when it sees a ceiling above, a floor below, the flank inboard and the wing outboard
    o = Vector((x, yb, z)); hits = [T.ray_cast(o, Vector(dv), 400)[:2] for dv in ((0, 0, 1), (0, 0, -1), (-1, 0, 0), (1, 0, 0))]
    return all(h[0] is not None for h in hits) and hits[0][1].z < 0 and hits[1][1].z > 0 and hits[2][1].x > 0 and hits[3][1].x < 0
for i, x in enumerate(np.arange(180, 460, cell) if P.get("wall", True) else []):
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

import bpy, bmesh, json
import numpy as np
from mathutils import Vector
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/vtop"
d = np.load(f"{D}/vplate.npz"); xs, ys, m, mid, half, dist = d["xs"], d["ys"], d["mask"], d["mid"], d["half"], d["dist"]; top, under, RIM = d["top"], d["under"], float(d["rim"])
bpy.ops.wm.open_mainfile(filepath="/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/body/body_v2.blend")
sc = bpy.data.scenes["seg"]
for o in [o for o in sc.objects if o.name == "v_plate"]: bpy.data.objects.remove(o)
bm = bmesh.new(); T = {}; B = {}
# the rim is every cell with an outside cell among its eight neighbours: there the top and bottom sheets
# share one vertex, so the shell closes without any extra wall
inner = m.copy()
for di in (-1, 0, 1):
    for dj in (-1, 0, 1): inner &= np.roll(np.roll(m, di, 0), dj, 1)
for i in range(len(ys)):
    for j in range(len(xs)):
        if not m[i, j]: continue
        if not inner[i, j]: T[(i, j)] = B[(i, j)] = bm.verts.new((xs[j], ys[i], mid[i, j])); T[(i, j)].tag = True; continue
        T[(i, j)] = bm.verts.new((xs[j], ys[i], mid[i, j] + half[i, j]))
        B[(i, j)] = bm.verts.new((xs[j], ys[i], mid[i, j] - half[i, j]))
def face(vs):
    # at the rim a quad may repeat the shared vertex: it closes as a triangle
    u = [v for k, v in enumerate(vs) if v not in vs[:k]]
    if len(u) >= 3 and bm.faces.get(u) is None: bm.faces.new(u)
for i in range(len(ys) - 1):
    for j in range(len(xs) - 1):
        q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
        if not all(x in T for x in q): continue
        face([T[x] for x in q]); face([B[x] for x in q][::-1])
# rim band: 8 rings in from the outline
ring = {v for v in bm.verts if v.tag}; band = set(ring); front = set(ring); depth = {v: 0 for v in ring}
for k in range(1, 9):
    front = {o for v in front for e in v.link_edges for o in e.verts} - band; band |= front; depth.update((v, k) for v in front)
# the outline is a staircase of grid cells that no relaxation can undo; each ring is set onto a level line of
# the smooth distance field instead (ring k at k cells in from the rim), which is where it sits away from the steps
step = float(xs[1] - xs[0])
def at(x, y, g=dist):
    i, j = np.clip((y - ys[0]) / step, 0, len(ys) - 1.001), np.clip((x - xs[0]) / step, 0, len(xs) - 1.001); i0, j0 = int(i), int(j); fi, fj = i - i0, j - j0
    return (g[i0, j0] * (1 - fi) * (1 - fj) + g[i0, j0 + 1] * (1 - fi) * fj + g[i0 + 1, j0] * fi * (1 - fj) + g[i0 + 1, j0 + 1] * fi * fj)
bm.normal_update(); d0 = float(np.median([at(v.co.x, v.co.y) for v in ring]))
for _ in range(6):
    for v, k in depth.items():
        x, y = v.co.x, v.co.y; gx, gy = (at(x + 1, y) - at(x - 1, y)) / 2, (at(x, y + 1) - at(x, y - 1)) / 2; g = max(np.hypot(gx, gy), 1e-3)
        e = (at(x, y) - (d0 + k * step)) * (1 - k / 9); v.co.x -= e * gx / g; v.co.y -= e * gy / g
# the heights follow the moved positions: the same rounded rim profile as the field, now even along each ring
for v, k in depth.items():
    r = min(max((at(v.co.x, v.co.y) - step) / RIM, 0.0), 1.0); bt = at(v.co.x, v.co.y, under)
    v.co.z = bt if (k and v.link_faces and sum(f.normal.z for f in v.link_faces) < 0) else bt + (at(v.co.x, v.co.y, top) - bt) * np.sqrt(1 - (1 - r) ** 2)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new("v_plate"); bm.to_mesh(me)
for p in me.polygons: p.use_smooth = True
sc.collection.objects.link(bpy.data.objects.new("v_plate", me))
bpy.data.libraries.write(f"{D}/v_scene.blend", {sc}, fake_user=True)
print("VPLATE", len(me.polygons))

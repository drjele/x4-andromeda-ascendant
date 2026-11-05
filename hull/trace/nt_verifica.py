# Night checks on the board: (1) ASAMBLAT_NOU unchanged against a reference scene's hash file (write on first run, compare after); (2) NAVA_TERMINATA's copy = ASAMBLAT_NOU moved -4800 at rest and mid-animation; (3) per new piece: free / non-manifold edges, degenerate faces, flipped volume, S/D mirror.
# Usage: blender -b <scene> --python nt_verifica.py -- <out.json>
import bpy, sys, json, hashlib, numpy as np, bmesh
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; A = bpy.data.collections["ASAMBLAT_NOU"]; NT = bpy.data.collections["NAVA_TERMINATA"]; res = {}
def world(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh(); P = np.empty(3 * len(m.vertices)); m.vertices.foreach_get("co", P); e.to_mesh_clear(); P = P.reshape(-1, 3); M = np.array(o.matrix_world); return P @ M[:3, :3].T + M[:3, 3]
hs = {}
for o in sorted(A.objects, key=lambda q: q.name):
    if o.type == "MESH": v = np.empty(3 * len(o.data.vertices)); o.data.vertices.foreach_get("co", v); hs[o.name] = hashlib.md5(v.tobytes() + np.array(o.location).tobytes()).hexdigest()
res["hash"] = hs; wc = 0.0; bad = []
for f in (1, 30, 60, 100, 146):
    sc.frame_set(f)
    for o in A.objects:
        c = bpy.data.objects.get("nt_" + o.name[3:])
        if o.type != "MESH": continue
        if c is None: bad.append(o.name); continue
        d = float(np.abs(world(c) - world(o) - np.array((-4800, 0, 0))).max()); wc = max(wc, d)
res["copie_abatere_max"] = wc; res["copie_lipsa"] = bad; sc.frame_set(1); rows = {}
old = {"nt_" + o.name[3:] for o in A.objects}
for o in sorted(NT.objects, key=lambda q: q.name):
    if o.name in old or o.type != "MESH": continue
    bm = bmesh.new(); bm.from_mesh(o.data); r = dict(fete=len(bm.faces), libere=sum(1 for e in bm.edges if len(e.link_faces) == 1), neman=sum(1 for e in bm.edges if len(e.link_faces) > 2), degenerate=sum(1 for f in bm.faces if f.calc_area() < 1e-6), volum=round(bm.calc_volume(signed=True)), metoda=o.get("metoda", "")); bm.free(); rows[o.name] = r
    if o.name.endswith("_S"):
        D = bpy.data.objects[o.name[:-1] + "D"]; a, b = np.empty(3 * len(o.data.vertices)), np.empty(3 * len(D.data.vertices)); o.data.vertices.foreach_get("co", a); D.data.vertices.foreach_get("co", b); r["mirror"] = float(np.abs(a.reshape(-1, 3) * [-1, 1, 1] - b.reshape(-1, 3)).max())
res["piese"] = rows; json.dump(res, open(OUT, "w"), indent=0)
g = [r for n, r in rows.items() if r["metoda"] == "ghidaje"]; print("VER copie max %.5f lipsa %s; piese %d (din ghidaje %d); ghidaje: libere %d neman %d degen %d volum<0 %d; mirror max %.5f" % (wc, bad, len(rows), len(g), sum(r["libere"] for r in g), sum(r["neman"] for r in g), sum(r["degenerate"] for r in g), sum(r["volum"] < 0 for r in g), max([r.get("mirror", 0) for r in rows.values()])))

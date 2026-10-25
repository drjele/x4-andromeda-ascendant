# Even out the ripples on every part's surface (the waves left by the voxel/SDF generators and the per-slice fits):
# Taubin smoothing (a shrink step then an inflate step, so the volume and the overall shape stay), borders pinned,
# the number of passes per group from smooth_all.json (the arms barely touched: the user called them nearly right).
# Usage: blender -b --python smooth_all.py
import bpy, json
import numpy as np
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/body/parts.json")); S = json.load(open(f"{D}/trace/smooth_all.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]; log = []
for o in sc.objects:
    if o.type != "MESH" or o.name.startswith("source"): continue
    label = P.get(o.name, ["?"])[0]; n = S["passes"].get(label, S["passes"].get(label[0], S["passes"]["default"]))
    if n <= 0: continue
    me = o.data; v = np.array([x.co for x in me.vertices]); e = np.array([x.vertices for x in me.edges])
    if not len(e): continue
    # border vertices: edges used by a single face
    cnt = {}
    for p in me.polygons:
        for k in p.edge_keys: cnt[k] = cnt.get(k, 0) + 1
    pin = np.zeros(len(v), bool)
    for (a, b), c in cnt.items():
        if c == 1: pin[a] = pin[b] = True
    deg = np.bincount(e.ravel(), minlength=len(v)).astype(float); free = (deg > 0) & ~pin
    def lap(x):
        s = np.zeros_like(x); np.add.at(s, e[:, 0], x[e[:, 1]]); np.add.at(s, e[:, 1], x[e[:, 0]])
        return np.where(deg[:, None] > 0, s / np.maximum(deg, 1)[:, None] - x, 0)
    v0 = v.copy()
    for _ in range(n):
        for f in (S["lambda"], S["mu"]): v[free] += f * lap(v)[free]
    # the open borders: Taubin along the border loop only (neighbours that are border vertices too)
    be = np.array([k for k, c in cnt.items() if c == 1])
    if len(be):
        bdeg = np.bincount(be.ravel(), minlength=len(v)).astype(float); bf = bdeg == 2
        for _ in range(S.get("border", 0)):
            for f in (S["lambda"], S["mu"]):
                s2 = np.zeros_like(v); np.add.at(s2, be[:, 0], v[be[:, 1]]); np.add.at(s2, be[:, 1], v[be[:, 0]])
                v[bf] += f * (s2[bf] / 2 - v[bf])
    for x, p in zip(me.vertices, v): x.co = p.tolist()
    me.update(); log.append("%s %d %.1f" % (o.name, n, np.abs(v - v0).max()))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("SMOOTH", "; ".join(log))

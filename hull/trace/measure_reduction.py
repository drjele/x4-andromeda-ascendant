# How far a reduced ship lies from its full-detail original: the body collections of both files (same placement),
# points sampled on each surface and their distance to the other surface (BVH nearest), both ways, in metres; the
# percentiles and the worst places (grid cells with the largest 99th percentile) printed per variant.
# Usage: blender -b <reduced.blend> --python measure_reduction.py -- <original.blend> <out.json>
import bpy, sys, json, random
from mathutils.bvhtree import BVHTree
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; ORIG, OUT = a; random.seed(0)
def objs(prefix, scene_objs): return [o for o in scene_objs if o.type == "MESH" and any(c.name.startswith(prefix) for c in o.users_collection)]
red = {k: objs(k, bpy.context.scene.objects) for k in ("A_Binkley_corp", "B_morenostefanuto_corp")}
with bpy.data.libraries.load(ORIG) as (src, dst): dst.collections = [n for n in src.collections if n in red]
ORIGC = {c.name.split(".0")[0] if c.name not in red else c.name: c for c in dst.collections}   # the original's collections, loaded under suffixed names
def tree(obs):
    vs, fs, off = [], [], 0
    for o in obs:
        m = o.matrix_world; vs += [m @ v.co for v in o.data.vertices]; fs += [tuple(i + off for i in p.vertices) for p in o.data.polygons]; off += len(o.data.vertices)
    return BVHTree.FromPolygons(vs, fs), vs, fs
def sample(vs, fs, n=60000):
    import math
    areas = []; tot = 0
    for f in fs:
        if len(f) < 3: areas.append(0); continue
        a_ = (vs[f[1]] - vs[f[0]]).cross(vs[f[2]] - vs[f[0]]).length / 2; tot += a_; areas.append(a_)
    pts = random.choices(range(len(fs)), weights=areas, k=n); out = []
    for i in pts:
        f = fs[i]; r1, r2 = random.random(), random.random(); s = math.sqrt(r1); out.append(vs[f[0]] * (1 - s) + vs[f[1]] * (s * (1 - r2)) + vs[f[2]] * (s * r2))
    return out
def pct(d, p): d = sorted(d); return round(d[min(len(d) - 1, int(len(d) * p / 100))], 2)
res = {}
for key, robs in red.items():
    oc = next((c for c in dst.collections if c is not None and c.name.startswith(key)), None)
    oobs = [o for o in oc.all_objects if o.type == "MESH"] if oc else []
    if not oobs: print("no originals for", key); continue
    tr, vr, fr = tree(robs); to, vo, fo = tree(oobs)
    d_ro = [(p - tr.find_nearest(p)[0]).length for p in sample(vo, fo)]     # original surface -> reduced (lost shape)
    d_or = [(p - to.find_nearest(p)[0]).length for p in sample(vr, fr)]     # reduced surface -> original (added error)
    res[key] = {"original_spre_redus_m": {p: pct(d_ro, p) for p in (50, 90, 99, 99.9)}, "redus_spre_original_m": {p: pct(d_or, p) for p in (50, 90, 99, 99.9)},
                "triunghiuri_redus": sum(len(p.vertices) - 2 for o in robs for p in o.data.polygons), "triunghiuri_original": sum(len(p.vertices) - 2 for o in oobs for p in o.data.polygons)}
    print(key, json.dumps(res[key]))
json.dump(res, open(OUT, "w"), indent=1)

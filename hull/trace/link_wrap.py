# The links' lower skirt hugged onto the body: below the body's middle, link vertices within `reach` of the skin are
# drawn onto it (the nearer, the more), so the skirt that wraps under the hull follows its curve and its edges end on
# the skin instead of standing off it as a flat panel with a gap.
# Usage: blender -b --python link_wrap.py
import bpy, bmesh, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; K = json.load(open(f"{D}/trace/link_wrap.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
o = sc.objects["corp"]; b = bmesh.new(); b.from_mesh(o.data); b.transform(o.matrix_world); B = BVHTree.FromBMesh(b); log = []
for name in ("link_r", "link_l"):
    o = sc.objects[name]; M = o.matrix_world; Mi = M.inverted(); n = 0; mx = 0.0
    for v in o.data.vertices:
        p = M @ v.co
        if p.z > K["z_max"]: continue
        loc, nn, _, _ = B.find_nearest(p); d = (p - loc).dot(nn)
        if d <= K["sink"] or d > K["reach"]: continue
        u = 1 - (d - K["sink"]) / (K["reach"] - K["sink"]); w = u * u * (3 - 2 * u); w *= min(1.0, (K["z_max"] - p.z) / K["z_fade"])
        dp = -nn * (d - K["sink"]) * w; v.co = Mi @ (p + dp); n += 1; mx = max(mx, dp.length)
    o.data.update(); log.append("%s %d moved, up to %.0f m" % (name, n, mx))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True); print("LINK WRAP", "; ".join(log))

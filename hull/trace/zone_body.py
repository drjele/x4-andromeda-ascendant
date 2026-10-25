# The body fitted to the confirmed zones, as one smooth correction (no slice-by-slice waves): per y, the body group's
# half width scaled toward the CORP zones' half width (bottom view) and its top raised/lowered toward the CORP zones'
# top (profile); both corrections smoothed hard along y (sigma), clamped, faded out at the ends.
# Usage: blender -b --python zone_body.py -- <targets.npz>
import bpy, sys, json, numpy as np
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; Z = np.load(sys.argv[sys.argv.index("--") + 1]); P = json.load(open(f"{D}/body/parts.json"))
K = json.load(open(f"{D}/trace/zone_body.json"))
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
def world(o): M = np.array(o.matrix_world); return np.array([x.co for x in o.data.vertices]) @ M[:3, :3].T + M[:3, 3]
def put(o, v):
    Mi = np.array(o.matrix_world.inverted()); loc = v @ Mi[:3, :3].T + Mi[:3, 3]; o.data.vertices.foreach_set("co", loc.ravel()); o.data.update()
gy = Z["gy"]; tw = Z["half_w"]; tz = Z["top_z"]
v = world(sc.objects["corp"]); idx = np.clip(np.round((v[:, 1] - gy[0]) / (gy[1] - gy[0])).astype(int), 0, len(gy) - 1)
cw = np.full(len(gy), np.nan); cz = np.full(len(gy), np.nan)
for k in np.unique(idx): s = v[idx == k]; cw[k] = np.abs(s[:, 0]).max(); cz[k] = s[:, 2].max()
def smooth(a, sig):
    a = np.where(np.isnan(a), 0, a); w = np.where(a != 0, 1.0, 0.0); r = int(3 * sig); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2)
    return np.convolve(a, k, "same") / np.maximum(np.convolve(w, k, "same"), 1e-6)
s = np.where(np.isnan(tw) | np.isnan(cw), np.nan, np.clip(tw / cw, *K["w_clamp"])) - 1
dz = np.where(np.isnan(tz) | np.isnan(cz), np.nan, np.clip(tz - cz, *K["z_clamp"]))
s = smooth(s, K["sigma"] / (gy[1] - gy[0])); dz = smooth(dz, K["sigma"] / (gy[1] - gy[0]))
ys = gy[~np.isnan(cw)]; fade = np.clip(np.minimum(gy - ys.min(), ys.max() - gy) / K["fade"], 0, 1); s *= fade; dz *= fade
zmid = np.nanmedian(cz) - 120
for o in sc.objects:
    if o.type != "MESH" or not P.get(o.name, ["?"])[0].startswith("C"): continue
    w = world(o); w[:, 0] *= 1 + np.interp(w[:, 1], gy, s)
    lift = np.clip((w[:, 2] - zmid) / 120, 0, 1); w[:, 2] += np.interp(w[:, 1], gy, dz) * lift   # the top moves, the belly stays
    put(o, w)
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)
print("ZONE BODY width x%.2f..%.2f, top %+.0f..%+.0f m" % (1 + s.min(), 1 + s.max(), dz.min(), dz.max()))

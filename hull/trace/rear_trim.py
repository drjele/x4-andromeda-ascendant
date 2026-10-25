# Narrow the stern to the user's bottom outline (rear body, region 8) and bring the raised rear deck flush with the
# body sides (it stood 11-14 m proud, the "fishtail" lip in plan): every body-group part is scaled in x per slice,
# the deck by its own factor; the scale fades out toward mid-body and keeps the stern tip.
# Usage: blender -b --python rear_trim.py -- <hull.npz>
import bpy, sys, json, numpy as np
H = np.load(sys.argv[sys.argv.index("--") + 1]); D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
P = json.load(open(f"{D}/body/parts.json")); VOX = 5.0; gx = np.arange(-1100, 1100 + VOX / 2, VOX); gy = np.arange(-1500, 1500 + VOX / 2, VOX)
Y0, Y1, TIP = -760.0, -400.0, -780.0
bpy.ops.wm.open_mainfile(filepath=f"{D}/vtop/v_scene.blend"); sc = bpy.data.scenes["seg"]
def world(o): M = np.array(o.matrix_world); v = np.array([x.co for x in o.data.vertices]); return v @ M[:3, :3].T + M[:3, 3]
def half_width(v):
    out = np.full(len(gy), np.nan); i = np.clip(np.round((v[:, 1] - gy[0]) / VOX).astype(int), 0, len(gy) - 1)
    for k in np.unique(i): out[k] = np.percentile(np.abs(v[i == k, 0]), 99)
    return out
def smooth(a, s=3):
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(a, 3 * s, mode="edge"), k, "valid")
B = H["body_bottom"]; tgt = np.array([(gx[r].max() - gx[r].min()) / 2 if r.any() else np.nan for r in B.T])
corp = half_width(world(sc.objects["corp"])); deck = half_width(world(sc.objects["rear_deck"]))
fade = np.clip(np.minimum((gy - TIP) / 40, (Y1 - gy) / 60), 0, 1) * (gy <= Y1)
s_body = np.where(np.isnan(tgt) | np.isnan(corp), 1, np.clip(tgt / corp, 0.85, 1.03)); s_body = smooth(1 + (s_body - 1) * fade)
s_deck = np.where(np.isnan(deck), s_body, np.clip((corp * s_body + 3) / deck, 0.85, 1.0)); s_deck = smooth(np.where(gy <= Y1 + 60, s_deck, 1) * 1.0)
s_deck = 1 + (s_deck - 1) * np.clip((Y1 + 60 - gy) / 60, 0, 1)
done = []
for o in sc.objects:
    if o.type != "MESH" or not P.get(o.name, ["?"])[0].startswith("C"): continue
    s = s_deck if o.name == "rear_deck" else s_body; v = world(o)
    v[:, 0] *= np.interp(v[:, 1], gy, s)   # continuous along y, so no step at the slice boundaries
    Mi = np.array(o.matrix_world.inverted()); loc = v @ Mi[:3, :3].T + Mi[:3, 3]
    for x, p in zip(o.data.vertices, loc): x.co = p.tolist()
    o.data.update(); done.append(o.name)
r = (gy >= Y0) & (gy <= Y1)
print("TRIM body x%.2f..%.2f, deck x%.2f..%.2f, %d parts" % (s_body[r].min(), s_body[r].max(), s_deck[r].min(), s_deck[r].max(), len(done)))
bpy.data.libraries.write(f"{D}/vtop/v_scene.blend", {sc}, fake_user=True)

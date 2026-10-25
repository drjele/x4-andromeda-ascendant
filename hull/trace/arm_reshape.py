# Reshape the arms toward ref 01 (the user's read of the overlay, 2026-10-25): the rear loops stretched aft (every
# point behind rear_y moves back in proportion to its distance from it), the whole path scaled in height away from
# the body, and the front tips splayed outward and lengthened, the front arc's middle drawn slightly inward; then (V14) the turn into the front arc moved aft, the upper branch
# rising into shoulders at the bridge, the loop's lower rear part curling up, the loop a little wider, the front tips
# lower and the strap thicker where it passes the lower wings. The pods at the tips and the U arch's legs (which end
# on the arms' rear loops) get the same transform so they stay attached; the pod joint box grows with them.
# Writes a_params.json and g_params.json in place from the originals given.
# Usage: python arm_reshape.py <a_params_orig.json> <g_params_orig.json>
import sys, json, numpy as np
T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; K = json.load(open(f"{T}/trace/arm_reshape.json"))
A = json.load(open(sys.argv[1])); G = json.load(open(sys.argv[2]))
def bump(y, lo, hi):
    v = np.clip((y - lo) / (hi - lo), 0, 1); return np.sin(np.pi * v) ** 2
def move(p):
    p = np.array(p, float); x, y, z = p.T.copy(); y0, z0 = p[:, 1].copy(), p[:, 2].copy()
    j = K.get("junction")                                                 # the turn into the front arc moved aft
    if j: y = y - j["aft"] * bump(y0, *j["y"])
    r = K["rear"]; y = np.where(y < r["y"], r["y"] + (y - r["y"]) * r["k"], y)
    f = K["front"]; u = np.clip((p[:, 1] - f["y"][0]) / (f["y"][1] - f["y"][0]), 0, 1); u = u * u * (3 - 2 * u)
    x = x + np.sign(x) * f["splay"] * u; y = y + f["longer"] * u
    mi = K.get("mid")                                                     # the arc's middle drawn inward (a smooth bump)
    if mi: v = np.clip((p[:, 1] - mi["y"][0]) / (mi["y"][1] - mi["y"][0]), 0, 1); x = x - np.sign(x) * mi["inward"] * np.sin(np.pi * v) ** 2
    z = z * K["height"]
    sh = K.get("shoulder")                                                # the upper branch rising at the bridge
    if sh: z = z + sh["up"] * bump(y0, *sh["y"]) * np.clip((z0 - sh["z"][0]) / (sh["z"][1] - sh["z"][0]), 0, 1)
    lc = K.get("loop_curl")                                               # the loop's lower rear part curving up
    if lc: s_ = np.clip((lc["y"] - y0) / lc["over"], 0, 1); z = z + lc["up"] * s_ * s_ * (3 - 2 * s_) * np.clip((lc["z_top"] - z0) / lc["z_span"], 0, 1)
    lo = K.get("loop_out")                                                # the rear loop slightly wider at mid length
    if lo: x = x + np.sign(x) * lo["out"] * bump(y0, *lo["y"])
    td = K.get("tip_down")                                                # the front tips lower
    if td: s_ = np.clip((y0 - td["y"][0]) / (td["y"][1] - td["y"][0]), 0, 1); z = z - td["down"] * s_ * s_ * (3 - 2 * s_)
    return np.round(np.stack([x, y, z], 1)).astype(int).tolist()
for m in ("arm", "pod"): A["members"][m]["path"] = move(A["members"][m]["path"])
th = K.get("thick")
if th:
    sys.path.insert(0, f"{T}/arms"); from a_frame import member
    C, f, *_ = member(A["members"]["arm"], 10)
    sel = (np.abs(C[:, 0]) > th["x_min"]) & (C[:, 1] > th["y"][0]) & (C[:, 1] < th["y"][1]) & (C[:, 2] < th["z_max"])
    f0, f1 = f[sel].min(), f[sel].max(); r = th["fade"]
    for row in A["members"]["arm"]["sections"]:
        u = np.clip(min(row[0] - (f0 - r), (f1 + r) - row[0]) / r, 0, 1); k = 1 + (th["scale"] - 1) * u * u * (3 - 2 * u)
        row[1] = round(row[1] * k, 1); row[2] = round(row[2] * k, 1)
    print("thicker f %.3f..%.3f" % (f0, f1))
b = A["joints"]["arm_pod"]["box"]; f = K["front"]
b["x"] = [b["x"][0], b["x"][1] + f["splay"]]; b["y"] = [b["y"][0], b["y"][1] + f["longer"]]; b["z"] = [round(b["z"][0] * K["height"]), round(b["z"][1] * K["height"])]
for m in ("leg_l", "leg_r"): G["members"][m]["path"] = move(G["members"][m]["path"])
json.dump(A, open(f"{T}/arms/a_params.json", "w")); json.dump(G, open(f"{T}/uarch/g_params.json", "w"))
y = np.array(A["members"]["arm"]["path"])[:, 1]; print("ARM RESHAPE rear end y %.0f, front tip y %.0f" % (y.min(), y.max()))

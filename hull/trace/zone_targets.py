# Targets read from the confirmed zones for the body and the lower wings: per y the CORP half width (bottom view) and
# top z (profile); the AI zone's front/back y per x (bottom view) for the link outline.
# Usage: python zone_targets.py <out_dir> <l_params.json>
import sys, json, numpy as np
OD, LP = sys.argv[1:3]; T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
src = open(f"{T}/trace/fit_zones.py").read(); src = src[:src.index("GROUPS = {")]; sys.argv = ["x", "/dev/null", OD]; exec(src)
B = sample("bottom", bmask(["CORP fata", "CORP spate"])); S = sample("side", side_mask(["CORP", "CORP spate", "CORP etaj", "CORP bot"]))
gy = g[1]; half_w = np.array([np.abs(g[0][B[:, j]]).max() if B[:, j].any() else np.nan for j in range(len(gy))])
top_z = np.array([g[2][S[i]].max() if S[i].any() else np.nan for i in range(len(gy))])
np.savez(f"{OD}/body_targets.npz", gy=gy, half_w=half_w, top_z=top_z)
AI = sample("bottom", bmask(["AI"])); L = json.load(open(LP))
def edge(line, use_max):
    out = []
    for x, y in line:
        i = np.argmin(abs(g[0] - x)); ys = g[1][AI[i]]
        out.append([x, int(round(0.7 * (ys.max() if use_max else ys.min()) + 0.3 * y))] if len(ys) > 3 else [x, y])
    return out
L["front"] = edge(L["front"], True); L["back"] = edge(L["back"], False)
json.dump(L, open(LP, "w"), indent=1); print("TARGETS body rows %d, link front %s, back %s" % ((~np.isnan(half_w)).sum(), L["front"], L["back"]))

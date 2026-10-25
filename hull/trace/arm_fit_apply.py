# The arm fitted to the zones put into the generators: the fitted path, the strap sizes kept within +-15 % of the
# previous ones (the footprint seen from below merges straps that lie side by side), the tip pods and the U arch's
# legs moved with the arm points near them so they stay attached.
# Usage: python arm_fit_apply.py <a_params_old> <a_params_fitted> <g_params_old>
import sys, json, numpy as np
T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; A0, A1, G0 = (json.load(open(p)) for p in sys.argv[1:4])
p0 = np.array(A0["members"]["arm"]["path"], float); p1 = np.array(A1["members"]["arm"]["path"], float); dv = p1 - p0
def carry(pts, sigma=120.0):
    pts = np.array(pts, float); out = pts.copy()
    for i, q in enumerate(pts):
        for side in (1, -1):                                                 # the arm and its mirror (left arm: x negated)
            ref = p0 * [side, 1, 1]; d = np.hypot(*(ref - q).T); w = np.exp(-0.5 * (d / sigma) ** 2)
            if w.sum() > 1e-3 and d.min() < 3 * sigma: out[i] += (w[:, None] * dv * [side, 1, 1]).sum(0) / max(w.sum(), 1e-9) * min(1.0, w.max() * 3)
    return np.round(out).astype(int).tolist()
A = json.loads(json.dumps(A0)); A["members"]["arm"]["path"] = p1.round().astype(int).tolist()
for r0, r1 in zip(A["members"]["arm"]["sections"], A1["members"]["arm"]["sections"]):
    r0[1] = round(float(np.clip(r1[1], r0[1] * 0.85, r0[1] * 1.15)), 1); r0[2] = round(float(np.clip(r1[2], r0[2] * 0.85, r0[2] * 1.15)), 1)
A["members"]["pod"]["path"] = carry(A0["members"]["pod"]["path"])
G = json.loads(json.dumps(G0))
for m in ("leg_l", "leg_r"): G["members"][m]["path"] = carry(G0["members"][m]["path"])
json.dump(A, open(f"{T}/arms/a_params.json", "w")); json.dump(G, open(f"{T}/uarch/g_params.json", "w"))
print("APPLIED path max move %.0f m, mean %.0f m" % (np.hypot(*dv.T).max(), np.hypot(*dv.T).mean()))

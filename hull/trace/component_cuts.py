# Each component cut out of every confirmed view and laid on the multi-view drawing (multiview.py layout): the zones
# named for the component (per view, from the confirmed zone maps) filled in the view's colour with their outline, the
# whole ship's lines faint underneath, the views that do not show the component left empty; a view where the part is
# only known together with others (the arms in the side view) is hatched and noted. One sheet per component.
# Symmetric views (top, bottom, back, front) keep one half and mirror it; the asymmetry removed is printed.
# Usage: python component_cuts.py <components.json> <layout.json> <vederi.json> <out_dir>
#   components.json: {"BS": {"top": {"zone": path, "names": path, "take": [names]}, "side": {"faces": path, "take": [...],
#                    "shared": true}, "bottom": {"npz": path, "take": [...]}, ...}, ...}
import sys, json, os, numpy as np, cv2
CJ, LJ, VJ, OD = sys.argv[1:5]; COMP = json.load(open(CJ)); LAY = json.load(open(LJ)); VIEWS = json.load(open(VJ)); os.makedirs(OD, exist_ok=True)
Wc, Hc = LAY["size"]; AFF = {k: np.array(v, float) for k, v in LAY["aff"].items()}
COL = {"top": (0, 220, 255), "bottom": (120, 255, 120), "side": (255, 140, 255), "back": (255, 200, 0), "front": (90, 160, 255)}
NAME = {"top": "SUS", "bottom": "JOS", "side": "PROFIL", "back": "SPATE", "front": "FATA"}
def lines_of(path):
    d = json.load(open(path)); out = []
    if isinstance(d, list): return [np.array(c, float) for l in d for c in l["curves"]]
    for k, v in d.items():
        if isinstance(v, dict): out.append(np.array(v["points"], float))
        else: out += [np.array(c, float) for c in v]
    return out
def to_canvas(key, pts): A = AFF[key]; return pts @ A[:, :2].T + A[:, 2]
base = np.full((Hc, Wc, 3), 18, np.uint8)
for key, v in VIEWS.items():
    for c in lines_of(v["lines"]): cv2.polylines(base, [np.round(to_canvas(key, c)).astype(np.int32)], False, (85, 85, 85), 2, cv2.LINE_AA)
    A = AFF[key]; ox, oy = A[0, 2], A[1, 2]
def view_mask(key, spec):
    # the component's pixels in the view's own sheet frame
    if "zone" in spec:
        z = np.load(spec["zone"]); nm = json.load(open(spec["names"])); ids = [int(k) for k, t in nm.items() if t in spec["take"]]
        return np.isin(z, ids)
    if "npz" in spec:
        z = np.load(spec["npz"]); m = None
        for t in spec["take"]: m = z[t] if m is None else (m | z[t])
        return m
    if "faces" in spec:
        F = json.load(open(spec["faces"])); H, W = spec.get("size", [860, 3260]); m = np.zeros((H, W), np.uint8)
        for t in spec["take"]:
            for f in F[t]:
                cv2.fillPoly(m, [np.round(np.array(f["outer"])).astype(np.int32)], 1)
                for h in f.get("holes", []): cv2.fillPoly(m, [np.round(np.array(h)).astype(np.int32)], 0)
        return m > 0
SYM = ("top", "bottom", "back", "front"); ASYM = []
for comp, views in COMP.items():
    img = base.copy(); notes = []
    for key, spec in views.items():
        m = view_mask(key, spec)
        if m is None or not m.any(): continue
        if key in SYM:                                                     # symmetry: one half kept, mirrored over the view's centreline
            ax = VIEWS[key]["axis"]; vert = key in ("back", "front"); n = m.shape[1] if vert else m.shape[0]; i = np.arange(n)
            src = np.clip(np.where(i <= ax, i, np.round(2 * ax - i).astype(int)), 0, n - 1)
            mm = m[:, src] if vert else m[src]; asym = (m ^ mm).sum() / max(m.sum(), 1); m = mm; ASYM.append("%s %s %.1f%%" % (comp, NAME[key], 100 * asym))
        warped = cv2.warpAffine(m.astype(np.uint8), AFF[key], (Wc, Hc), flags=cv2.INTER_NEAREST) > 0
        col = np.array(COL[key])
        if spec.get("shared"):                                             # known only together with other parts: hatched
            hatch = ((np.add.outer(np.arange(Hc), np.arange(Wc)) // 10) % 3 == 0)
            img[warped & hatch] = col; notes.append("%s: %s (hasurat = impreuna cu alte piese)" % (NAME[key], ", ".join(spec["take"])))
        else: img[warped] = (img[warped] * 0.3 + col * 0.7).astype(np.uint8)
        cs, _ = cv2.findContours(warped.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(img, cs, -1, (255, 255, 255), 2, cv2.LINE_AA)
    for key in VIEWS:
        A = AFF[key]; p = to_canvas(key, np.array([[0, 0]], float))[0]
    cv2.putText(img, comp, (60, 90), 0, 3.0, (255, 255, 255), 6, cv2.LINE_AA)
    for j, n in enumerate(notes): cv2.putText(img, n, (60, Hc - 60 - 50 * j), 0, 1.2, (235, 235, 235), 2, cv2.LINE_AA)
    cv2.imwrite(f"{OD}/{comp}.png", cv2.resize(img, None, fx=0.5, fy=0.5)); print(comp, ", ".join(k for k in views))
print("ASIMETRIE corectata:", "; ".join(ASYM))

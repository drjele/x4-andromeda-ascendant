# Draw the cross-sections from section.py to scale: the original as a grey outline, our parts in their colours.
# Usage: python section_draw.py <sections.json> <out_dir> <name>:<lo1,hi1,lo2,hi2>[:px_per_m[:part,part]] ...
# (a part list isolates the surfaces of interest; the original is always drawn in grey)
import json, sys, numpy as np, cv2
D = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"
S = json.load(open(sys.argv[1])); OUT = sys.argv[2]; P = json.load(open(f"{D}/body/parts.json"))
for spec in sys.argv[3:]:
    f = spec.split(":"); name = f[0]; lo1, hi1, lo2, hi2 = map(float, f[1].split(",")); k = float(f[2]) if len(f) > 2 else 2.0; only = set(f[3].split(",")) if len(f) > 3 else None
    W, H = int((hi1 - lo1) * k) + 80, int((hi2 - lo2) * k) + 80; img = np.full((H, W, 3), 245, np.uint8)
    px = lambda u, v: (int(40 + (u - lo1) * k), int(H - 40 - (v - lo2) * k))
    sec = S[name]; lab = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}[sec["axis"]]
    for g in np.arange(np.ceil(lo1 / 50) * 50, hi1 + 1, 50): cv2.line(img, px(g, lo2), px(g, hi2), (225, 225, 225), 1)
    for g in np.arange(np.ceil(lo2 / 50) * 50, hi2 + 1, 50): cv2.line(img, px(lo1, g), px(hi1, g), (225, 225, 225), 1)
    order = [n for n in sorted(sec["points"], key=lambda n: n != "source") if only is None or n == "source" or n in only]
    for on in order:
        pts = np.array(sec["points"][on]); rgb = (150, 150, 150) if on == "source" else tuple(int(c * 255) for c in P.get(on, ["", (0.8, 0.6, 0.3)])[1][::-1])
        for u, v in pts:
            if lo1 <= u <= hi1 and lo2 <= v <= hi2: cv2.circle(img, px(u, v), 1 if on == "source" else 2, rgb, -1)
    cv2.putText(img, f"{name}: {sec['axis']} = {sec['value']:.0f}   ({lab[0]} across, {lab[1]} up, 50 m grid)", (10, 24), 0, 0.6, (30, 30, 30), 1)
    for i, on in enumerate([n for n in order if len(sec["points"][n]) > 3][:12]):
        rgb = (150, 150, 150) if on == "source" else tuple(int(c * 255) for c in P.get(on, ["", (0.8, 0.6, 0.3)])[1][::-1])
        cv2.rectangle(img, (W - 230, 14 + 18 * i), (W - 216, 28 + 18 * i), rgb, -1); cv2.putText(img, "original (grannyte)" if on == "source" else f"{P.get(on, ['?'])[0]} {on}", (W - 210, 27 + 18 * i), 0, 0.45, (30, 30, 30), 1)
    cv2.imwrite(f"{OUT}/sec_{name}.png", img)
print("drawn")

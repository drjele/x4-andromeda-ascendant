# A reference model written in the common frame with its objects kept apart: the same normalisation to the average
# proportions and the same alignment as ref_compare.py (transformari.json, model "a" or "b").
# Usage: python write_aligned.py <in_world.obj> <transformari.json> <a|b> <out.obj>
import sys, json, numpy as np
IN, TJ, WH, OUT = sys.argv[1:5]; T = {k: np.array(v) for k, v in json.load(open(TJ)).items()}
lo, hi = (T["la"], T["ha"]) if WH == "a" else (T["lb"], T["hb"]); R, t = (np.eye(3), np.zeros(3)) if WH == "a" else (T["R"], T["t"])
with open(IN) as f, open(OUT, "w") as g:
    for l in f:
        if l.startswith("v "):
            p = np.array(l.split()[1:4], float); q = ((p - (lo + hi) / 2) * (T["Em"] / (hi - lo))) @ R.T + t; g.write("v %.3f %.3f %.3f\n" % tuple(q))
        else: g.write(l)
print("WROTE", OUT)

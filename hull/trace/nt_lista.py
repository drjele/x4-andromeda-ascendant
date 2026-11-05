# The list of pieces still to build: every reference object minus those the validated ship has (agreed list by number) and the ones the user took out. One line per component: id name.
import numpy as np, sys, re, json
Z = np.load(sys.argv[1]); names = [str(n) for n in Z["names"]]
EXIST = set("019 022 169 012 001 098 085 086 087 055 099 103 096 104 028 034 029 030 031 040 043 049 051 052 053 054 056 057 058 060 063 064 065 066 067 069 070 072 073 074 075 076 077 078 079 080 081 082 083 084".split())
OUT = {"117": "scos de user (103_118 vechi)", "118": "scos de user (103_118 vechi)"}; SK = {}; rows = {}
def bb(n):
    v = Z[n.replace(" ", "_") + "__v"]; return v.min(0), v.max(0)
for n in names:
    if n.startswith("Circle"): continue                                      # the blades, validated
    if n.startswith(("Plane", "Cube")): rows[n.replace(".", "")] = {"C": n}; continue
    m = re.match(r"R\d+ (marunte_\w+?|\d+)_([SDC])$", n)
    if not m: print("NEPOTRIVIT", n); continue
    num, side = m.groups()
    if num in EXIST: continue
    if num in OUT: SK[n] = OUT[num]; continue
    rows.setdefault(num, {})[side] = n
fin = {}; dup = []
for k, r in rows.items():
    if "marunte" in k: continue
    fin[k] = r.get("S") or r.get("C") or r.get("D")
for k, n in list(fin.items()):                                               # a D-only number whose mirror sits on an S-only number's place = the same piece named differently
    if n.endswith("_D"):
        a0, a1 = bb(n); a0, a1 = a0 * [-1, 1, 1], a1 * [-1, 1, 1]; a0, a1 = np.minimum(a0, a1), np.maximum(a0, a1)
        for k2, n2 in fin.items():
            if k2 == k or not n2 or not n2.endswith("_S"): continue
            b0, b1 = bb(n2); I = np.minimum(a1, b1) - np.maximum(a0, b0)
            if (I > 0).all():
                iou = I.prod() / ((a1 - a0).prod() + (b1 - b0).prod() - I.prod())
                if iou > 0.25: dup.append((n, n2, round(float(iou), 2))); fin[k] = None; break
fin = {k: n for k, n in fin.items() if n}
for k, n in sorted(fin.items(), key=lambda t: -len(Z[t[1].replace(" ", "_") + "__f"])): print(k, n.replace(" ", "_"))
json.dump(dict(scoase=SK, duplicate=dup), open(sys.argv[2], "w"), ensure_ascii=False, indent=0); print("#", len(fin), "dup", len(dup), "scoase", len(SK), file=sys.stderr)

# Guides for the hood's inner chambers (asked: the hood hollow like the original): the original's layout in the new
# trapezoid hood - outer walls T m thick (parallel to the faces, so the slanted ones stay 45 deg), a lengthwise middle wall
# WM m on x = 0, a cross wall WC m at y YC, so 4 chambers; the front ones open to the front (the mouth, as the original),
# the back ones closed. Guides: each chamber's floor outline (one plane, z = base + T) and its sections at the hood ribs'
# stations (planes y = const). Usage: python ghid_capac_camere.py <ghid_capac _asamblat.npz> <out.npz>
# env T=2 WM=4 WC=4 YC=155 DZ=0 (WC=0: no cross wall - one long chamber a side)
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
T, WM, WC, YC, DZ = e("T", "2"), e("WM", "4"), e("WC", "4"), e("YC", "155"), e("DZ", "0")
B = G["contur_capac_baza"]; ZC = float(B[0, 2]); SP = G["spinare_capac_mijloc"]; YB, YF = B[:, 1].min(), B[:, 1].max()
o = np.argsort(SP[:, 1]); hgt = lambda y: np.interp(y, SP[o, 1], SP[o, 2]) - ZC
R = B[(B[:, 0] > 0) & (B[:, 1] > YB + 15) & (B[:, 1] < YF - 15)]; b, a = np.polyfit(R[:, 1], R[:, 0], 1); xb = lambda y: a + b * y
S2 = np.sqrt(2)
def inner(y):                                          # the chamber's section at y (right side): floor z, inner wall foot / top x, top z
    h = hgt(y); w = xb(y); zf, zt = ZC + T, ZC + h - T
    if zt <= zf + 0.5: return None
    xf = w - (zf - ZC) - T * S2; xt = w - (zt - ZC) - T * S2                       # the 45 deg wall moved in by T (perpendicular)
    x0 = WM / 2; return (x0, xf, xt, zf, zt) if xt > x0 + 1 else None
out = {}; k = 0
# floor outlines: right chambers (back: y from the back wall to the cross wall; front: cross wall to the open front)
yb0 = YB + T * S2 + T; ys_back = np.arange(yb0, YC - WC / 2 + 0.01, 1.0); ys_front = np.arange(YC + WC / 2, YF + 0.01, 1.0)
zones = (("spate", ys_back), ("fata", ys_front)) if WC > 0 else (("lunga", np.arange(yb0, YF + 0.01, 1.0)),)   # WC=0: no cross wall
for nm, ys in zones:
    rows = [(y, inner(y)) for y in ys]; rows = [(y, q) for y, q in rows if q is not None]
    if not rows: continue
    yy = np.array([r[0] for r in rows]); xo = np.array([r[1][1] for r in rows]); x0 = rows[0][1][0]
    P = np.vstack([np.c_[np.full(len(yy), x0), yy], np.c_[xo[::-1], yy[::-1]]]); P = np.vstack([P, P[:1]])
    zf = rows[0][1][3]
    for sd, sg in (("D", 1), ("S", -1)): out["contur_camera_%s_%s" % (nm, sd)] = np.c_[P[:, 0] * sg, P[:, 1], np.full(len(P), zf)]
ribs = sorted(set(round(float(G[q][0, 1]), 1) for q in G.files if q.startswith("sectiune_capac")))
for y in ribs:
    q = inner(y)
    if q is None or (WC > 0 and abs(y - YC) < WC / 2): continue
    x0, xf, xt, zf, zt = q; P = np.array([[x0, zf], [xf, zf], [xt, zt], [x0, zt], [x0, zf]])
    for sd, sg in (("D", 1), ("S", -1)): out["sectiune_camera_%02d_%s" % (k, sd)] = np.c_[P[:, 0] * sg, np.full(len(P), y), P[:, 1]]
    k += 1
for kk in out: out[kk] = out[kk] + [0, 0, DZ]
hb, hf = hgt(YB + 20), hgt(YF - 20)
print("CAMERE CAPAC: pereti %.0f m, perete mijloc %.0f m (x 0), perete transversal %.0f m (y %.0f; 0 = fara); camerele (fata deschise spre fata); podeaua z %.0f; inaltimea camerei ~%.1f m in spate -> ~%.1f m in fata; %d sectiuni la nervuri" % (
    T, WM, WC, YC, ZC + T, hb - 2 * T, hf - 2 * T, k))
np.savez(OUT, **out)

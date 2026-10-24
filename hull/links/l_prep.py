# Side link fields: the top is a smooth polynomial surface fitted to the measured source (robust, so the
# eye and small fittings drop out), the underside follows it at a fitted thickness; the rim rounds both.
import json, numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt, zoom
d = np.load("lfield.npz"); xs, ys, top, bot, bx = d["xs"], d["ys"], d["top"], d["bot"], d["body_x"]
P = json.load(open("l_params.json"))
X, Y = np.meshgrid(xs, ys)
fy = np.interp(xs, *zip(*P["front"])); by = np.interp(xs, *zip(*P["back"]))
inner = np.interp(ys, ys[np.isfinite(bx)], bx[np.isfinite(bx)]) - P["inset"]
# the outline as a soft field whose half level sits on the front and back lines between cells, so no grid
# staircase ever reaches the rims; the smoothing rounds the corners between the line segments
sx = xs[1] - xs[0]
edge = np.minimum(np.minimum(fy[None] - Y, Y - by[None]), np.minimum(X - inner[:, None], P["x_max"] - X))
mf = gaussian_filter(np.clip(edge / sx + 0.5, 0, 1), P["outline_smooth"]); m = mf > 0.5
def basis(x, y, deg):
    u, v = (x - 400) / 300, (y + 250) / 250
    return np.stack([u ** i * v ** j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)
def robust(x, y, z, deg):
    ok = np.ones(len(z), bool)
    for _ in range(6):
        c = np.linalg.lstsq(basis(x[ok], y[ok], deg), z[ok], rcond=None)[0]
        res = z - basis(x, y, deg) @ c; s = 1.4826 * np.median(np.abs(res[ok])); ok = np.abs(res) < 2.0 * s + 2
    return c
fit = m & np.isfinite(top) & (top > -330) & (top < 150) & (X > inner[:, None] + 40)
ct = robust(X[fit], Y[fit], top[fit], P["deg_top"]); TP = basis(X, Y, P["deg_top"]) @ ct
th = top - bot; ft = fit & np.isfinite(th) & (th > P["thick_min"]) & (th < P["thick_max"] + 20)
ch = robust(X[ft], Y[ft], th[ft], P["deg_thick"]); TH = np.clip(basis(X, Y, P["deg_thick"]) @ ch, P["thick_min"], P["thick_max"])
# fillets that follow the body: the top may climb the flank as a cove, the underside drops onto it, except
# along the hangar slot where the underside lifts away from the body as in the source
lb = np.load("lbody.npz"); from scipy.interpolate import RegularGridInterpolator
BW = RegularGridInterpolator((lb["ys"], lb["zs"]), lb["bw"], bounds_error=False, fill_value=0.0)
def gap(z): return X - BW(np.stack([Y, np.clip(z, lb["zs"][0], lb["zs"][-1])], -1))
F = P["fillet"]
gb = np.clip(gap(TP) / P["thin_reach"], 0, 1)
_a, _b, _k = TH, P["thin_root"] + gb * 120, 25.0
_h = np.clip(0.5 + 0.5 * (_b - _a) / _k, 0, 1); BT = TP - (_b * (1 - _h) + _a * _h - _k * _h * (1 - _h))   # soft minimum, no crease   # thinner where it meets the body, so the hangar slot opens under it
for _ in range(3):                                   # the flank moves with the height, so settle it
    u = 1 - np.clip(gap(TPf if "TPf" in dir() else TP) / F["top_reach"], 0, 1); TPf = TP + F["top"] * (1 - np.sqrt(1 - u * u))   # a cove: tangent to the wing and to the flank
hy = np.clip(np.minimum((Y - F["slot"][0]) / F["slot_ramp"], (F["slot"][1] - Y) / F["slot_ramp"]), 0, 1); hy = hy * hy * (3 - 2 * hy)
for _ in range(3):
    g = np.clip(gap(BTf if "BTf" in dir() else BT) / F["bottom"], 0, 1)
    BTf = BT - F["bottom"] * (1 - g) ** 2 * (1 - hy)
    gs = np.clip(gap(BT) / F["slot_width"], 0, 1); BTf = BTf + F["slot_lift"] * hy * (1 - gs) ** 2
BTf = np.minimum(BTf, TPf - P["thick_min"] * 0.6)
BTf = np.maximum(BTf, TPf - P["thick_max"] - F["bottom"])
TO = P.get("thin_out")
if TO:
    # thinner toward the outer edge as well, so the wing meets the arm strap with a thin edge instead of a collar
    go = np.clip((P["x_max"] - X) / TO["reach"], 0, 1); _b = TO["to"] + go * 120; _a = TPf - BTf
    _h = np.clip(0.5 + 0.5 * (_b - _a) / _k, 0, 1); BTf = TPf - (_b * (1 - _h) + _a * _h - _k * _h * (1 - _h))
TP, TH = TPf, TPf - BTf
# inboard of where each face enters the body it is held under the body's upper surface (the flank recedes
# above the widest point) and over its lower surface (the stern belly is shallow), so the inner end stays
# hidden; a column left too thin by that is inside the body anyway and is dropped
ZT = np.full(X.shape, np.inf); ZB = np.full(X.shape, -np.inf)
for i in range(len(ys)):
    bwr = lb["bw"][int(round(np.interp(ys[i], lb["ys"], np.arange(len(lb["ys"])))))]
    for j in range(len(xs)):
        hit = np.where(bwr >= xs[j])[0]
        if len(hit): ZT[i, j] = lb["zs"][hit[-1]]; ZB[i, j] = lb["zs"][hit[0]]
meet = np.where((TPf <= ZT) & np.isfinite(ZT), X, -np.inf).max(1, keepdims=True)
meet_b = np.where((BTf >= ZB) & np.isfinite(ZB), X, -np.inf).max(1, keepdims=True)
TPf = np.where(X <= meet, np.minimum(TPf, ZT - P["bury"]), TPf)
BTf = np.where(X <= meet_b, np.maximum(BTf, ZB + P["bury"]), BTf)
thin = (X <= np.minimum(meet, meet_b)) & (TPf - BTf < P["thick_min"] * 0.6); m = m & ~thin
BTf = np.minimum(BTf, TPf - P["thick_min"] * 0.6)
TP, TH = TPf, TPf - BTf
# the inner end stops just inside the body at both its heights, square, so the body hides it
cut = np.minimum(BW(np.stack([Y, np.clip(TP, lb["zs"][0], lb["zs"][-1])], -1)), BW(np.stack([Y, np.clip(BTf, lb["zs"][0], lb["zs"][-1])], -1))) - P["bury"]
m = m & (X >= cut); mcut = np.minimum(mf, np.clip((X - cut) / sx + 0.5, 0, 1) * ~thin)
print("top rms", np.sqrt(np.nanmean((top[fit] - TP[fit]) ** 2)).round(1), "thick range", TH[m].min().round(), TH[m].max().round())
k = 2
X2 = np.linspace(xs[0], xs[-1], k * len(xs)); Y2 = np.linspace(ys[0], ys[-1], k * len(ys))
tp2 = zoom(TP, k, order=3); th2 = zoom(TH, k, order=3)                 # cubic, so the rims carry no kink per base cell
def fine_sdist(field, up=8):
    # signed distance to the 0.5 contour of a smooth field, measured on a grid finer than the output so the
    # rounded rims carry no staircase ripple
    f = zoom(field, up, order=3) > 0.5; st = up // k                # cubic: the contour is a curve, not a polyline
    e = gaussian_filter(distance_transform_edt(f) - distance_transform_edt(~f), 1.5)   # the pixel staircase of the distance would ripple a slanted rim
    return e[::st, ::st] * (xs[1] - xs[0]) / up
sd = fine_sdist(mf)
# the plate is kept as fields, not a mesh: a mid surface and a half thickness, the in-plane distance to the
# outline that rounds the rim (it ignores the inner end, so the root stays full), and the in-plane distance
# to the plate alone that bounds it, so the piece ends square at the inner end inside the body
sdm = fine_sdist(mcut); m2 = sdm > 0
np.savez("lplate.npz", xs=X2, ys=Y2, mask=m2, mid=tp2 - th2 / 2, hf=th2 / 2, sd=sd, sdm=sdm, rim=P["rim"])
print("cells", m2.sum())

# the lower branch of the Y: the hangar deck, nearly level, from the body flank out into the wing's underside
Dk = P["deck"]
dy = np.clip(np.minimum((Y - Dk["y"][0]) / Dk["ramp_back"], (Dk["y"][1] - Y) / Dk["ramp"]), 0, 1)
# the lower branch slopes: low on the body flank, rising outboard to the fork, so the Y reads from ahead
dtop = Dk["top"] + Dk["wave"] * np.sin((Y - Dk["y"][0]) / (Dk["y"][1] - Dk["y"][0]) * np.pi) + Dk["rise"] * np.clip((X - Dk["x_in"]) / (Dk["x_out"] - Dk["x_in"]), 0, 1)
dcut = BW(np.stack([Y, np.full_like(Y, (Dk["top"] + Dk["bottom"]) / 2)], -1)) - P["bury"] - 25
# the deck ends where its top passes under the wing's underside, found between columns so the edge of the
# fork is a smooth curve and not the grid's staircase
xin = np.full(len(ys), np.inf); g = BTf - (dtop - 4)
for i in range(len(ys)):
    row = np.where(m[i] & (g[i] < 0) & (X[i] > dcut[i]))[0]
    if len(row) and row[0] > 0:
        j = row[0]; xin[i] = X[i, j - 1] + (X[i, j] - X[i, j - 1]) * g[i, j - 1] / (g[i, j - 1] - g[i, j])
xin = np.maximum(np.where(np.isfinite(xin), xin, 0), Dk["x_out"])
md = np.clip(dy * 4, 0, 1) * np.clip((X - dcut) / sx + 0.5, 0, 1) * np.clip((xin[:, None] + Dk["into_wing"] - X) / sx + 0.5, 0, 1)
# toward the stern the lower branch rises into the wing, so the Y closes behind the hangars
c = np.clip((Dk["close"][0] - Y) / (Dk["close"][0] - Dk["close"][1]), 0, 1); c = c * c * (3 - 2 * c)
dtop = dtop + c * np.maximum(BTf + Dk["into_wing"] - dtop, 0)
thk = (Dk["top"] - Dk["bottom"]) * (0.35 + 0.65 * dy) + c * np.maximum(BTf + Dk["into_wing"] - dtop, 0)
sdd = fine_sdist(gaussian_filter(md, 2.0)); md2 = sdd > 0
dmid = zoom(dtop - thk / 2, k, order=3); dhalf = zoom(thk / 2, k, order=3)
np.savez("ldeck.npz", xs=X2, ys=Y2, mask=md2, mid=dmid, hf=dhalf, sd=sdd, sdm=sdd, rim=Dk.get("rim", 12))
print("deck cells", md2.sum())

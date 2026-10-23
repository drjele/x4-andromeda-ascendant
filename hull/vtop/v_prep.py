# Plate fields for the V on the full width (mirrored first, so the centreline is interior), smoothed.
import json, numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt, binary_closing, binary_opening, label, zoom
d = np.load("vfield.npz"); xs, ys, top, bot = d["xs"], d["ys"], d["top"], d["bot"]
P = json.load(open("v_params.json"))
# rays exactly on the seam can slip through: take the x=0 column from its neighbour
top[:, 0] = np.where(np.isfinite(top[:, 0]), top[:, 0], top[:, 1]); bot[:, 0] = np.where(np.isfinite(bot[:, 0]), bot[:, 0], bot[:, 1])
mir = lambda a: np.hstack([a[:, :0:-1], a]); X = np.r_[-xs[:0:-1], xs]
top, bot = mir(top), mir(bot)
xlim = np.interp(ys, [c[0] for c in P["x_cut"]], [c[1] for c in P["x_cut"]])
m = np.isfinite(top) & (ys[:, None] >= P["y_min"]) & (np.abs(X)[None, :] < xlim[:, None])
m = binary_closing(m, iterations=3); m = binary_opening(m, iterations=2)
lab, n = label(m); m = lab == np.bincount(lab.ravel())[1:].argmax() + 1
def fill(a): v = np.nanmedian(a); return np.where(np.isfinite(a), a, v)
# keep the detail of the upper surface, smooth only the underside
tp = gaussian_filter(fill(top), P["top_smooth"]); bt = gaussian_filter(fill(np.where(top - bot > 4, bot, np.nan)), P["bot_smooth"])
# a flat underside: the plane that best fits the measured underside, kept under the top
Yg, Xg = np.meshgrid(ys, X, indexing="ij"); sel = m & np.isfinite(bot) & (top - bot > 4)
A = np.c_[Xg[sel] * 0, Yg[sel], np.ones(sel.sum())]; coef = np.linalg.lstsq(A[:, 1:], bot[sel], rcond=None)[0]
bt = coef[0] * Yg + coef[1]
bt = np.minimum(bt, gaussian_filter(tp, 3) - P["min_thick"])
print("underside plane z = %.3f * y + %.1f" % tuple(coef))
BT = bt; TPf = tp
k = 2
m2 = zoom(gaussian_filter(m.astype(float), 2.0), k, order=1) > 0.5
X2 = np.linspace(X[0], X[-1], m2.shape[1]); Y2 = np.linspace(ys[0], ys[-1], m2.shape[0])
tp2 = zoom(TPf, k, order=1); bt2 = zoom(BT, k, order=1)
dist = gaussian_filter(distance_transform_edt(m2) * (X2[1] - X2[0]), 1.5)
r = np.clip((dist - (X2[1] - X2[0])) / P["rim"], 0, 1)
# the underside stays exactly flat; only the top rounds down onto it at the rim
from scipy.ndimage import binary_erosion
r[m2 & ~binary_erosion(m2)] = 0.0   # the outermost cells close the plate exactly
top2 = bt2 + (tp2 - bt2) * np.sqrt(1 - (1 - r) ** 2)
np.savez("vplate.npz", xs=X2, ys=Y2, mask=m2, mid=(top2 + bt2) / 2, half=(top2 - bt2) / 2)
# the keel: flat in the middle (a deck for mounts), sloping evenly out to every edge of the plate
K = json.load(open("vdeco.json"))["v_keel"]
dk = gaussian_filter(distance_transform_edt(m2) * (X2[1] - X2[0]), 2.0) - K["inset"]
t = np.clip(dk / K["ramp"], 0, 1); keel = K["depth"] * t * t * (3 - 2 * t)
np.savez("vkeel.npz", xs=X2, ys=Y2, mask=m2 & (dk > 0), depth=keel, under=bt2)
print("plate cells", m2.sum())

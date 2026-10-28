# The piece's edge made one smooth rounded rim all round (asked: the outline looked like stairs - behind the nose the
# original's two flat lips with the closing wall between them read as steps): on the last D m inside the smoothed plan
# outline the top and the bottom curve towards each other as quarter ellipses and meet on the outline at their middle
# height, like the nose's edge. The distance to the outline from the smooth outline itself (fine raster, not the footprint's
# cells), the faces at the band's inner side taken from the nearest inside cell and smoothed along the edge. Writes the
# terrain with both faces replaced. Usage: python margine_rotunda.py <teren.npz> <out.npz> [d]
import sys, numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt, gaussian_filter
T = dict(np.load(sys.argv[1])); OUT = sys.argv[2]; D = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
top, bot = T["top"].astype(float), T["bot"].astype(float); x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"]); ny, nx = top.shape
ol = T["outline"][:, :2]; S = 4; m = np.zeros((ny * S, nx * S), np.uint8); cv2.fillPoly(m, [np.round((ol - [x0, y0]) / C * S).astype(np.int32)], 1)
d = (edt(m) * C / S)[S // 2::S, S // 2::S][:ny, :nx]                  # distance inside the smooth outline (m)
inner = d >= D; _, (pi, pj) = edt(~inner, return_indices=True)
def band(F):                                                            # the face at the band's inner side, smoothed along the edge
    E = F[pi, pj]; w = gaussian_filter((~inner).astype(float), 2.0 / C); Es = gaussian_filter(np.where(~inner, E, 0), 2.0 / C) / np.maximum(w, 1e-6)
    return np.where(~inner & (w > 0.05), Es, E)
tD, bD = band(top), band(bot); zm = (tD + bD) / 2
t = np.clip(d / D, 0, 1); q = np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1))  # quarter ellipse: 0 on the outline, 1 at the band's inner side
top2 = np.where(inner, top, zm + (tD - zm) * q); bot2 = np.where(inner, bot, zm - (zm - bD) * q)
k = gaussian_filter((np.abs(d - D) < 2.0).astype(float), 1.0 / C)       # the band's inner seam softened
top2 = top2 * (1 - k) + gaussian_filter(top2, 1.5 / C) * k; bot2 = bot2 * (1 - k) + gaussian_filter(bot2, 1.5 / C) * k
T["top"], T["bot"] = top2.astype(np.float32), bot2.astype(np.float32); T["foot"] = m[S // 2::S, S // 2::S][:ny, :nx].astype(bool)
np.savez(OUT, **T)
print("MARGINE rotunda: banda %.0f m in interiorul conturului neted; pe contur grosimea 0, la mijlocul inaltimii (z %.0f..%.0f)" % (D, zm[(d > 0) & (d < 1)].min(), zm[(d > 0) & (d < 1)].max()))

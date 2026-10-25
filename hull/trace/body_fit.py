# Fit V4's body onto the user's body outlines, slice by slice along the length: the half width from the top/bottom
# footprint, the bottom and top heights from the profile; where a view hides the body (the lower wing in profile, the
# arms below) the correction is blended across from the slices on either side, so V4's own shape carries through.
# The section shape stays V4's; every body-group part follows the same map so the decorations stay on the body.
# Usage: python body_fit.py <drawings_dir> <body_V.npz> <out.npz> [--width-only]   (keep V4's heights)
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter1d
D, SRC, OUT = sys.argv[1:4]; H = np.load(f"{D}/hull.npz"); B = np.load(SRC); VOX = 5.0
gx = np.arange(-1100, 1100 + VOX / 2, VOX); gy = np.arange(-1500, 1500 + VOX / 2, VOX); gz = np.arange(-500, 500 + VOX / 2, VOX)
F, S = H["body_xy"], H["body_side"]
def edges(body, sil, coords, near=16):
    # per slice the body's two extremes, each kept only if no other drawn part lies within `near` cells beyond it:
    # there the edge is a junction (a wing on the body) or hidden (an arm in front), not the body's own outline
    lo = np.full(body.shape[0], np.nan); hi = lo.copy()
    for i, row in enumerate(body):
        if row.sum() < 3: continue
        idx = np.nonzero(row)[0]; a, b = idx[0], idx[-1]
        if not sil[i, max(a - near, 0):a].any(): lo[i] = coords[a]
        if not sil[i, b + 1:b + 1 + near].any(): hi[i] = coords[b]
    return lo, hi
def half_width(body, sil):
    lo, hi = edges(body.T, sil.T, gx); return np.nanmax(np.stack([-lo, hi]), 0)   # symmetric ship: either side will do
with np.errstate(all="ignore"):
    hw_t = np.nanmean(np.stack([half_width(H["body_top"], H["others_top"]), half_width(H["body_bottom"], H["others_bottom"])]), 0)
    zl_t, zh_t = edges(S, H["others_side"], gz)
body = B["corp"]
def binned(v, f):
    out = np.full(len(gy), np.nan); idx = np.clip(np.round((v[:, 1] - gy[0]) / VOX).astype(int), 0, len(gy) - 1)
    for i in np.unique(idx): out[i] = f(v[idx == i])
    return out
hw_c = binned(body, lambda p: np.percentile(np.abs(p[:, 0]), 99)); zl_c = binned(body, lambda p: np.percentile(p[:, 2], 1)); zh_c = binned(body, lambda p: np.percentile(p[:, 2], 99))
# length: the body's ends from the footprint and the profile together
known = F.any(0) | S.any(1); y0_t, y1_t = gy[known][[0, -1]]; ok_c = ~np.isnan(hw_c); y0_c, y1_c = gy[ok_c][[0, -1]]
def y_map(y): return y0_t + (y - y0_c) * (y1_t - y0_t) / (y1_c - y0_c)
def y_unmap(y): return y0_c + (y - y0_t) * (y1_c - y0_c) / (y1_t - y0_t)
src_i = np.clip(np.round((y_unmap(gy) - gy[0]) / VOX).astype(int), 0, len(gy) - 1)   # V4 slice under each target slice
def blend(delta, inside):
    # fill the hidden slices by straight interpolation of the correction, then smooth it so the surface stays organic
    d = delta.copy(); good = ~np.isnan(d) & inside
    if good.sum() < 2: return np.zeros_like(d)
    d = np.interp(gy, gy[good], d[good]); a, b = gy[good][[0, -1]]
    fade = np.clip(1 - np.maximum(a - gy, gy - b) / 120, 0, 1)   # beyond the measured slices the correction dies out over 120 m
    return gaussian_filter1d(d * fade, 4)
inside = (gy >= y0_t) & (gy <= y1_t)
with np.errstate(all="ignore"):
    q = hw_t / hw_c[src_i]; q[(q < 0.75) | (q > 1.3)] = np.nan   # far off V4 is an arm's or wing's edge read as the body's: not a measurement
    sx = blend(q - 1, inside) + 1
sx = np.clip(np.nan_to_num(sx, nan=1.0), 0.6, 1.6)
ends = np.clip(np.minimum(gy - y0_t, y1_t - gy) / 120, 0, 1); sx = 1 + (sx - 1) * ends   # V4's own width at both tips, never a blow-up past them
dl = blend(zl_t - zl_c[src_i], inside); dh = blend(zh_t - zh_c[src_i], inside)
if "--width-only" in sys.argv: dl[:] = 0; dh[:] = 0
def apply(v):
    # every correction read continuously along y (interpolated between the 5 m slices): read per slice it left a
    # tiny step at each slice boundary, visible as stripes on the skin
    y2 = y_map(v[:, 1]); ys = y_unmap(y2)
    lo = np.interp(ys, gy[~np.isnan(zl_c)], zl_c[~np.isnan(zl_c)]); hi = np.interp(ys, gy[~np.isnan(zh_c)], zh_c[~np.isnan(zh_c)])
    t = (v[:, 2] - lo) / np.maximum(hi - lo, 1e-3)   # height fraction inside the slice; decorations above/below extrapolate
    d_lo, d_hi = np.interp(y2, gy, dl), np.interp(y2, gy, dh); z2 = lo + d_lo + t * ((hi + d_hi) - (lo + d_lo))
    return np.stack([v[:, 0] * np.interp(y2, gy, sx), y2, z2], 1).astype(np.float32)
out = {k: apply(B[k]) for k in B.files}
np.savez_compressed(OUT, **out)
print("BODY FIT length %.0f -> %.0f m, y %.0f..%.0f -> %.0f..%.0f" % (y1_c - y0_c, y1_t - y0_t, y0_c, y1_c, y0_t, y1_t))
print("width scale %.2f..%.2f, bottom shift %.1f..%.1f m, top shift %.1f..%.1f m" % (sx[inside].min(), sx[inside].max(), dl[inside].min(), dl[inside].max(), dh[inside].min(), dh[inside].max()))

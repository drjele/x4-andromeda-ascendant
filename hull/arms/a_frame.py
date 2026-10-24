# Shared arm geometry: the Catmull-Rom path with its section frame (w outboard-level, u up), the rounded
# strap ring (flat top and bottom, round corners) and a cast from the path onto a built surface.
import math
import numpy as np

def catmull(pts, n):
    p = np.array(pts, float); p = np.vstack([p[:1], p, p[-1:]]); out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1:i + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2]); return np.array(out)
def member(m, n=10):
    # sections are [f, width, height, round]; round is the corner radius as a fraction of the half height
    C = catmull(m["path"], n)
    if m.get("smooth"):
        # the control polygon leaves short bends; a Gaussian along the dense samples makes the curvature flow
        sg = m["smooth"] / np.linalg.norm(np.diff(C, axis=0), axis=1).mean(); r = int(3 * sg)
        k = np.exp(-0.5 * (np.arange(-r, r + 1) / sg) ** 2); k /= k.sum()
        C = np.stack([np.convolve(np.pad(C[:, c], r, mode="edge"), k, "valid") for c in range(3)], 1)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))]; f = s / s[-1]
    S = np.array([list(r) + [m.get("round", 1.0)] * (4 - len(r)) for r in m["sections"]], float)
    return C, f, np.interp(f, S[:, 0], S[:, 1]), np.interp(f, S[:, 0], S[:, 2]), np.interp(f, S[:, 0], S[:, 3])
def frame(C, i, oriented=False):
    t = C[min(i + 1, len(C) - 1)] - C[max(i - 1, 0)]; t /= np.linalg.norm(t)
    w = np.cross(t, [0, 0, 1.0]); w = w / np.linalg.norm(w) if np.linalg.norm(w) > 1e-3 else np.array([1.0, 0, 0]); u = np.cross(w, t)
    if oriented:
        w = w if w[0] >= 0 else -w; u = u if u[2] >= 0 else -u
    return t, w, u
def ring(W, H, rnd, K=48):
    r = max(0.5, min(rnd * H / 2, W / 2, H / 2)); m = K // 4; out = []
    for q, (sx, sz) in enumerate([(1, 1), (-1, 1), (-1, -1), (1, -1)]):
        for a in np.linspace(q * math.pi / 2, (q + 1) * math.pi / 2, m):
            out.append((sx * (W / 2 - r) + r * math.cos(a), sz * (H / 2 - r) + r * math.sin(a)))
    return out
def cast(T, c, d, reach=600):
    from mathutils import Vector
    hit, nrm, _, _ = T.ray_cast(Vector(c), Vector(d).normalized(), reach)
    return (np.array(hit), np.array(nrm)) if hit is not None else (None, None)
def rrect(X, Y, x, y, r):
    # signed distance inside a rounded rectangle (positive inside)
    cx, cy = (x[0] + x[1]) / 2, (y[0] + y[1]) / 2; hx, hy = np.maximum((x[1] - x[0]) / 2 - r, 0.1), np.maximum((y[1] - y[0]) / 2 - r, 0.1)
    qx, qy = np.abs(X - cx) - hx, np.abs(Y - cy) - hy
    return r - (np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0))
def housing(X, Y, N, keys_axis=None):
    L = N["lift"] * np.sin(np.clip(rrect(X, Y, N["x"], N["y"], N["rim"] * 1.6) / N["rim"], 0, 1) * np.pi / 2)
    S = N["slot"]; us = np.clip(rrect(X, Y, S["x"], S["y"], S["rim"] * 1.5) / S["rim"], 0, 1); m = us * us * (3 - 2 * us)
    L = L - S["depth"] * m
    if keys_axis is not None: L = L + N["keys"]["h"] * (0.5 + 0.5 * np.cos(2 * np.pi * keys_axis / N["keys"]["pitch"])) ** 1.5 * m
    return np.where(L > 0.02, L, -0.6)                                 # outside the rim the sheet dives under the skin
def grid_mesh(bm, G, ny, nx, keep=None):
    # faces with no lifted corner stay out, so the rim is the clean crossing of the sheet through the skin
    for i in range(ny):
        for j in range(nx):
            q = [G.get((i, j)), G.get((i, j + 1)), G.get((i + 1, j + 1)), G.get((i + 1, j))]
            if None in q or (keep is not None and not (keep[i, j] or keep[i, j + 1] or keep[i + 1, j + 1] or keep[i + 1, j])): continue
            bm.faces.new(q)

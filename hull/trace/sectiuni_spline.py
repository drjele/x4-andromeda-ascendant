# Step 1 of the hybrid rebuild of PS (169_C) - silhouette + plane sections (memory feedback_metoda_ghidaje): the reference
# only as geometry. At each station y (every STEP m) the reference points of a +-1 m slice on an x-z raster (0.5 m), the
# right half (x >= 0) mirrored (never averaged); every x column filled between its highest and lowest point (the reference
# is a sheet); cut to the confirmed top silhouette (ghid_drept2.npz: outer B, inner U - where they reach); then the
# rolling ball: closing of radius RC (fills holes, slots, gaps) and opening of radius RO (cuts ribs and small steps);
# inner holes filled. Each outer contour fitted by one periodic smoothing spline (tolerance TOL), made exactly symmetric
# (the right half mirrored; a contour across the middle crosses it as one curve). Per variant (RC, RO): distance of the
# reference points to the contours, the largest turn per 1 m; a sheet of representative stations; all stations saved.
# Usage: python sectiuni_spline.py <esantion_punte.npz> <ghid_drept2.npz> <out_dir> <rc/ro,...> [step] [y0] [y1]
import sys, os, numpy as np, cv2
from scipy.interpolate import splprep, splev
from scipy.ndimage import binary_fill_holes
from scipy.spatial import cKDTree
D = np.load(sys.argv[1]); G = np.load(sys.argv[2]); OUTD = sys.argv[3]; VAR = [tuple(float(x) for x in v.split("/")) for v in sys.argv[4].split(",")]
STEP = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0; YA = float(sys.argv[6]) if len(sys.argv) > 6 else 474.0; YB = float(sys.argv[7]) if len(sys.argv) > 7 else -500.0
CEN, PX, TOL, Z0, Z1, XM = -4.68, 0.5, float(os.environ.get("SEC_TOL", "0.5")), 150.0, 420.0, 300.0
os.makedirs(OUTD, exist_ok=True)
P = D["ps"].copy(); P[:, 0] -= CEN; P = P[(P[:, 1] < YA + 2) & (P[:, 1] > YB - 2) & (P[:, 2] > Z0) & (P[:, 2] < Z1) & (np.abs(P[:, 0]) < XM)]
order = np.argsort(P[:, 1]); P = P[order]; Ys = P[:, 1]
def side(Q):                                                           # the right half of a mirrored guide line: x(y) where it exists
    R = Q[Q[:, 0] >= 0]; return R
Bo, Bi = side(G["B"]), side(G["B_int"]); YU = float(Bi[:, 1].max())   # the top of the U between the arms
def x_at(R, y):                                                        # the guide's x at height y (the run that reaches y), or None
    i = np.nonzero(np.diff(np.sign(R[:, 1] - y)))[0]
    if not len(i): return None
    j = i[0]; t = (y - R[j, 1]) / (R[j + 1, 1] - R[j, 1]); return float(R[j, 0] + t * (R[j + 1, 0] - R[j, 0]))
NX, NZ = int(2 * XM / PX), int((Z1 - Z0) / PX)
def section(y0, rc, ro):
    S = P[(Ys > y0 - 1) & (Ys < y0 + 1)]; S = S[S[:, 0] >= 0]
    if len(S) < 20: return [], S
    m = np.zeros((NZ, NX), np.uint8); ix = ((S[:, 0] + XM) / PX).astype(int); iz = ((S[:, 2] - Z0) / PX).astype(int)
    for c in np.unique(ix):                                            # column fill (the reference is a sheet)
        zz = iz[ix == c]; m[zz.min():zz.max() + 1, c] = 1
    m = np.maximum(m, m[:, ::-1])                                      # the right half mirrored
    if y0 > YU:                                                        # in front of the U the deck is one body: each row filled
        for r in np.nonzero(m.any(1))[0]:                              # across (the big hole under the 086 lid)
            c = np.nonzero(m[r])[0]; m[r, c.min():c.max() + 1] = 1
    xs = (np.arange(NX) + 0.5) * PX - XM; keep = np.ones(NX, bool)
    xo, xi = x_at(Bo, y0), x_at(Bi, y0)
    if xo is not None: keep &= np.abs(xs) <= xo                         # cut to the confirmed silhouette
    if xi is not None: keep &= np.abs(xs) >= xi
    m[:, ~keep] = 0
    k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(r / PX) + 1,) * 2)
    if rc > 0: m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k(rc))
    m = binary_fill_holes(m).astype(np.uint8); m[:, ~keep] = 0
    if ro > 0: m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k(ro))
    out = []
    for c in cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]:
        if cv2.contourArea(c) < 40: continue
        Q = np.stack([(c[:, 0, 0] + 0.5) * PX - XM, (c[:, 0, 1] + 0.5) * PX + Z0], 1)
        if Q[:, 0].max() < 0: continue                                 # left blobs come from the mirror of the right ones
        Qd = Q[np.r_[True, np.linalg.norm(np.diff(Q, axis=0), axis=1) > 1e-6]]
        tck, _ = splprep(Qd.T, s=len(Qd) * TOL ** 2, per=1, k=3); F = np.array(splev(np.linspace(0, 1, max(len(Qd), 60), endpoint=False), tck)).T
        if Q[:, 0].min() < 0:                                          # across the middle: right half + its mirror (one curve)
            pos = F[:, 0] > 0; up = np.nonzero(pos & ~np.roll(pos, 1))[0]
            if len(up):
                F = np.roll(F, -up[0], axis=0); n_ = int(np.argmin(F[:, 0] > 0)) or len(F); R = F[:n_]   # the x > 0 arc, in order
                F = np.vstack([[[0, R[0, 1]]], R, [[0, R[-1, 1]]], (R * [-1, 1])[::-1]])
            out.append(F)
        else: out += [F, F * [-1, 1]]
    return out, S
def stats(C, S):
    if not C or not len(S): return np.nan, np.nan, np.nan
    T = np.vstack(C); d = cKDTree(T).query(S[:, [0, 2]])[0]
    tr = 0.0
    for F in C:
        Fc = np.vstack([F, F[:1]]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Fc, axis=0), axis=1))]; u = np.arange(0, s[-1], 1.0)
        if len(u) < 4: continue
        Q = np.stack([np.interp(u, s, Fc[:, i]) for i in range(2)], 1); t = np.diff(Q, axis=0); t /= np.maximum(np.linalg.norm(t, axis=1), 1e-9)[:, None]
        tr = max(tr, np.degrees(np.arccos(np.clip(np.sum(t[1:] * t[:-1], 1), -1, 1))).max())
    return d.mean(), np.percentile(d, 95), tr
REP = [440, 380, 300, 200, 100, 20, -40, -120, -250, -400]
for rc, ro in VAR:
    tag = "rc%g_ro%g" % (rc, ro); ys = np.arange(YA - 1, YB, -STEP); allc = {}; st = []
    for y0 in ys:
        C, S = section(y0, rc, ro); allc[round(float(y0), 1)] = C; st.append(stats(C, S))
    st = np.array(st, float); ok = ~np.isnan(st[:, 0])
    pts, sy, start = [], [], []                                        # flat (readable by Blender's older numpy): all points,
    for k_, v in allc.items():                                         # and per contour its station and first point
        for F in v: start.append(sum(len(p) for p in pts)); sy.append(k_); pts.append(np.asarray(F, float))
    np.savez(os.path.join(OUTD, "sectiuni_%s.npz" % tag), ys=ys, pts=np.vstack(pts), sy=np.array(sy), start=np.array(start + [sum(len(p) for p in pts)]))
    print("VARIANTA %s: %d statii; abatere referinta fata de contur medie %.2f / 95%% %.2f m (median pe statii); intoarcere max %.1f grade la 1 m (95%% statii %.1f)" % (
        tag, ok.sum(), np.median(st[ok, 0]), np.median(st[ok, 1]), np.nanmax(st[:, 2]), np.nanpercentile(st[:, 2], 95)))
    W, H, cw, ch, sc = 1500, 1000, 300, 200, 0.5; im = np.full((ch * 2 * 5 // 5 * 1 + ch, cw * 5, 3), 255, np.uint8); im = np.full((ch * 2, cw * 5, 3), 255, np.uint8)
    for k, y0 in enumerate(REP):
        ox, oy = (k % 5) * cw, (k // 5) * ch; C, S = section(y0, rc, ro); f = lambda Q: np.stack([ox + cw / 2 + Q[:, 0] * sc * 0.9, oy + ch - 20 - (Q[:, 1] - 230) * sc * 1.2], 1).astype(np.int32)
        for p in f(np.r_[S[:, [0, 2]], S[:, [0, 2]] * [-1, 1]]):
            if 0 <= p[0] < im.shape[1] and 0 <= p[1] < im.shape[0]: im[p[1], p[0]] = (170, 170, 170)
        for F in C: cv2.polylines(im, [f(F)], True, (0, 0, 0), 1)
        cv2.putText(im, "y %d" % y0, (ox + 5, oy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 200), 1); cv2.rectangle(im, (ox, oy), (ox + cw - 1, oy + ch - 1), (220, 220, 220), 1)
    cv2.imwrite(os.path.join(OUTD, "sectiuni_%s.png" % tag), im)
print("SALVAT in", OUTD)

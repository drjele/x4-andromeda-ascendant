# Guides for the blends between the PS and arm pieces (asked: better blending between all of them, pieces kept separate;
# chosen "mixt": arm ends widen as a funnel tangent onto the PS, the edges of 103 / hood / nacelle get a rounded fillet).
# Per joint, on the right (D) half, mirrored about the ship axis: the contact line (where the secondary piece crosses the
# primary's surface - triangle by triangle where the signed distance changes sign; for a piece that only touches, its
# rim nearest the primary), then on each piece the line where the blend starts = iso-line of the distance to the contact
# line at the band width, only on the part left outside the other piece. Pieces exported in world coordinates (npz
# <name>__v/__f); guides written centred on the ship (x + 1700).
# v2: one contact line per joint (the longest loop), smoothed; the start lines = the contact line walked over each surface.
# Usage: [IMB_SIGMA=8] python imbinari_ghidaje.py <pieces.npz> <out.npz> [secondary:primary:band_sec:band_prim ...]
import sys, numpy as np, igl
from scipy.spatial import cKDTree
a = sys.argv[1:]; D = np.load(a[0]); OUT = a[1]; XAX = -1700.0
JOINTS = [s.split(":") for s in a[2:]] or [s.split(":") for s in (
    "brat_spate_D:PS:60:15", "brat_fata_D:PS+103_D:60:15", "103_D:PS:8:8", "103_D:brat_spate_D:8:8", "103_D:brat_fata_D:8:8",
    "capac_086:PS:8:8", "nacela_rosie_D:PS:8:8")]

def piece(n, box=None):                               # "A+B" = the pieces together (an arm closing on PS and 103)
    vs_, fs_, o_ = [], [], 0
    for m in n.split("+"):
        vs_.append(D[m + "__v"].astype(np.float64)); fs_.append(D[m + "__f"].astype(np.int64) + o_); o_ += len(vs_[-1])
    v, f = np.vstack(vs_), np.vstack(fs_)
    if box is not None:
        keep = np.all((v[f] > box[0]) & (v[f] < box[1]), axis=(1, 2)); f = f[keep]
    return v, f

def sdist(p, v, f):                                    # + inside (winding number: arms are open at their ends)
    return -igl.signed_distance(p, v, f, sign_type=igl.SIGNED_DISTANCE_TYPE_FAST_WINDING_NUMBER)[0]

def iso(v, f, s, lvl=0.0):                             # iso-line of a vertex field as chained polylines
    s = s - lvl; segs = []
    for t in f[(np.sign(s[f]) != np.sign(s[f[:, :1]])).any(1)]:
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            a_, b_ = t[i], t[j]
            if (s[a_] < 0) != (s[b_] < 0): u = s[a_] / (s[a_] - s[b_]); pts.append((min(a_, b_), max(a_, b_), v[a_] + u * (v[b_] - v[a_])))
        if len(pts) == 2: segs.append(pts)
    nb, pos = {}, {}
    for (a1, b1, p1), (a2, b2, p2) in segs:
        k1, k2 = (a1, b1), (a2, b2); pos[k1], pos[k2] = p1, p2; nb.setdefault(k1, []).append(k2); nb.setdefault(k2, []).append(k1)
    seen, lines = set(), []
    for k0 in nb:
        if k0 in seen: continue
        line = [k0]; seen.add(k0)
        for direction in (0, 1):
            cur = line[-1] if direction == 0 else line[0]
            while True:
                nxt = [k for k in nb[cur] if k not in seen]
                if not nxt: break
                cur = nxt[0]; seen.add(cur)
                if direction == 0: line.append(cur)
                else: line.insert(0, cur)
        P = np.array([pos[k] for k in line])
        if len(P) > 1: lines.append(P)
    return lines

def length(P): return np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
def resample(P, step=1.0):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]; t = np.arange(0, d[-1], step)
    return np.c_[[np.interp(t, d, P[:, i]) for i in range(3)]].T if len(t) > 1 else P
def smooth(P, sig=3):
    if len(P) < 7: return P
    k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); k /= k.sum()
    Q = np.c_[[np.convolve(np.pad(P[:, i], 3 * sig, mode="edge"), k, "valid") for i in range(3)]].T
    Q[0], Q[-1] = P[0], P[-1]; return Q

SIG = float(__import__("os").environ.get("IMB_SIGMA", "8"))            # smoothing of the guide lines, metres
def smooth_c(P, sig, closed):                         # gaussian along the line (wrap-around when closed)
    n = len(P); r = int(3 * sig)
    if n < 2 * r + 3: return P
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); k /= k.sum()
    Q = np.c_[[np.convolve(np.pad(P[:, i], r, mode="wrap" if closed else "edge"), k, "valid") for i in range(3)]].T
    if not closed: Q[0], Q[-1] = P[0], P[-1]
    return Q
def turn(P, closed):                                  # max turn of the line, degrees per metre (over 2 m)
    T = np.diff(np.r_[P, P[:2]] if closed else P, axis=0); L = np.linalg.norm(T, axis=1); T = T / L[:, None]
    c = np.clip((T[:-1] * T[1:]).sum(1), -1, 1); return float(np.degrees(np.arccos(c)).max() / max(np.median(L), 1e-6))
def band(C, mine, other, d, closed, steps=6):         # the contact line walked d metres over my surface, away from the other piece
    v, f = mine; vo, fo = other; t = np.gradient(C, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; P = C.copy()
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
    for _ in range(steps):
        _, I, P = igl.point_mesh_squared_distance(P, v, f); n = fn[I]; w = np.cross(n, t); w /= np.linalg.norm(w, axis=1)[:, None] + 1e-12
        h = 1.0; sp = sdist(P + h * w, vo, fo); sm = sdist(P - h * w, vo, fo); w *= np.where(sp < sm, 1, -1)[:, None]
        w = smooth_c(w, SIG, closed); w /= np.linalg.norm(w, axis=1)[:, None]; P = P + (d / steps) * w
    _, _, P = igl.point_mesh_squared_distance(P, v, f); return smooth_c(P, SIG, closed)

out = {}
for sec, pri, bs, bp in JOINTS:
    bs, bp = float(bs), float(bp); key = sec.replace("_D", "") + "__" + pri.replace("_D", "").replace("+", "_")
    vs, fs = piece(sec); vp, fp = piece(pri)
    box = (np.maximum(vs.min(0), vp.min(0)) - 80, np.minimum(vs.max(0), vp.max(0)) + 80)
    vs, fs = piece(sec, box); vp, fp = piece(pri, box)
    if not len(fs) or not len(fp): print("IMBINARE %-26s departe" % key); continue
    s_sec = np.full(len(vs), -1e3); us = np.unique(fs); s_sec[us] = sdist(vs[us], *piece(pri))
    s_pri = np.full(len(vp), -1e3); up = np.unique(fp); s_pri[up] = sdist(vp[up], *piece(sec))
    contact = [L for L in iso(vs, fs, s_sec) if length(L) > 15]; kind = "trece prin"
    if not contact:                                    # touches only: the secondary's nearest rim (free edges near the primary)
        dmin = -s_sec.max(); kind = "atinge (gol min %.1f m)" % dmin
        contact = [L for L in iso(vs, fs, s_sec, lvl=-(dmin + 2.0)) if length(L) > 15]
    full_s, full_p = piece(sec), piece(pri)
    if sec.startswith("brat_"):                        # funnel: the arm's ring on the PS, ordered round the arm's axis, closed
        E = np.sort(np.r_[fs[:, [0, 1]], fs[:, [1, 2]], fs[:, [2, 0]]], axis=1); E, cnt = np.unique(E, axis=0, return_counts=True)
        rim = E[cnt == 1]; rim = rim[np.abs(s_sec[rim]).max(1) < 3] if s_sec.max() < 2 else rim[:0]   # open mouth on the PS surface (not one deep inside)
        pts = np.vstack([resample(L, 0.5) for L in contact] + [vs[rim].mean(1)] if len(rim) else [resample(L, 0.5) for L in contact])
        c0 = pts.mean(0); dv = np.linalg.norm(vs - c0, axis=1); ring = vs[(dv > 40) & (dv < 140) & (s_sec < -1)]
        ax = ring.mean(0) - c0; ax /= np.linalg.norm(ax)
        if len(rim):                                     # arm that only touches: its mouth, ordered round the arm's axis
            e1 = np.cross(ax, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1); q = pts - c0
            ang = np.arctan2(q @ e2, q @ e1); idx = np.digitize(ang, np.linspace(-np.pi, np.pi, 361)) - 1; C = np.full((360, 3), np.nan)
            for b_ in range(360):
                if (idx == b_).any(): C[b_] = pts[idx == b_].mean(0)
            ok = ~np.isnan(C[:, 0]); th = np.arange(360); C = np.c_[[np.interp(th, th[ok], C[ok, i], period=360) for i in range(3)]].T
        else:                                            # arm passing through: the crossing pieces joined into one ring
            frags = [L for L in iso(vs, fs, s_sec) if length(L) > 5]
            frags = [L for L in frags if np.linalg.norm(L[0] - L[-1]) > 5] or frags          # open pieces to join; a lone loop stays
            C = max(frags, key=length); rest = [L for L in frags if L is not C]; gaps = []
            while rest:                                    # nearest end first, reversed when needed
                dd = [(min(np.linalg.norm(C[-1] - L[0]), np.linalg.norm(C[-1] - L[-1])), i) for i, L in enumerate(rest)]
                g, i = min(dd); L = rest.pop(i)
                if g > 120: break
                gaps.append(round(g)); C = np.r_[C, L if np.linalg.norm(C[-1] - L[0]) <= np.linalg.norm(C[-1] - L[-1]) else L[::-1]]
            gaps.append(round(np.linalg.norm(C[-1] - C[0]))); print("   %s: %d bucati legate, goluri %s m" % (key, len(gaps), gaps))
        C = smooth_c(resample(np.r_[C, C[:1]], 1.0)[:-1], SIG, True); closed = True
        o = c0 + bs * ax; sec_l = iso(full_s[0], full_s[1], (full_s[0] - o) @ ax)       # flat section of the arm bs metres back
        S_ = min(sec_l, key=lambda L: np.linalg.norm(L.mean(0) - o)); S_ = smooth_c(resample(S_, 1.0), 3, True)
        lines = {"contact": C, "sec": S_, "pri": band(C, full_p, full_s, bp, True)}; kind = "palnie"
    else:
        C = max(contact, key=length); closed = np.linalg.norm(C[0] - C[-1]) < 5
        C = smooth_c(resample(C, 1.0), SIG, closed)
        lines = {"contact": C, "sec": band(C, full_s, full_p, bs, closed), "pri": band(C, full_p, full_s, bp, closed)}
    msg = []
    for role, P in lines.items():
        P = P.copy(); P[:, 0] -= XAX; out["%s_%s_D" % (role, key)] = P; Q = P.copy(); Q[:, 0] *= -1
        if sec.endswith("_D") or pri.endswith("_D"): out["%s_%s_S" % (role, key)] = Q
        msg.append("%s %.0f m, %.2f grd/m" % (role, length(P), turn(P, closed)))
    print("IMBINARE %-24s %-10s %-7s patrundere max %5.1f m | %s" % (key, kind, "inchis" if closed else "deschis", max(s_sec.max(), 0), " | ".join(msg)))
np.savez(OUT, **out); print("SALVAT", OUT, len(out), "linii")

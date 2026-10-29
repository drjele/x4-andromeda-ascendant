# Guides for the "ear" grown out of the PS instead of the separate 103 (asked: like the series ship - the ears carry on the
# head's curve and thin towards their outer edge, hugging the side like the red nacelles on the front arms; whole length of
# 103; section = the PS's side carried on and thinned; outer outline = 103's spine as confirmed). From the confirmed 103 piece
# (its 4 corners per section: inner top edge on the PS, small outer side top/bottom, inner bottom edge): the outer edge =
# the middle of the small side; each section = a top and a bottom Hermite curve from the inner edge (leaving along the PS's
# own surface there - its section's tangent, or level where there is no PS) to the outer edge, which is a rounded blade
# MARGINE m thick. Writes contur_margine (outer edge), contur_prindere_sus/_jos (attach lines) and sectiune_NN (closed).
# UR_PLAN=1 the outer edge in one (best-fit) plane; UR_CONT=1 each section carries on the PS's own section curve: same point,
# direction and curvature (read over +-10 m, capped so it cannot loop), quintic to the edge (level, straight there).
# Usage: python ureche_ghidaje.py <103_D.npz> <pieces.npz> <out.npz> ; env UR_MARGINE=4 UR_PAS=40
import sys, os, numpy as np, trimesh
R = np.load(sys.argv[1])["v"].astype(float).reshape(-1, 4, 3); D = np.load(sys.argv[2]); OUT = sys.argv[3]
MG, PAS = float(os.environ.get("UR_MARGINE", "4")), float(os.environ.get("UR_PAS", "40"))
ps = trimesh.Trimesh(D["PS__v"] + [1700, 0, 0], D["PS__f"], process=False)
edge = (R[:, 1] + R[:, 2]) / 2
def tangent(p, up):                                    # direction of the PS's section surface leaving the attach point outwards
    s = ps.section(plane_origin=[0, p[1], 0], plane_normal=[0, 1, 0])
    if s is None: return None
    best = None
    for e in s.discrete:
        e = e[:, [0, 2]]; d = np.linalg.norm(e - p[[0, 2]], axis=1); i = np.argmin(d)
        if d[i] < 4 and (best is None or d[i] < best[0]): best = (d[i], e, i)
    if best is None: return None
    _, e, i = best; a, b = e[max(i - 3, 0)], e[min(i + 3, len(e) - 1)]; t = b - a; t /= np.linalg.norm(t)
    if t[0] < 0: t = -t                                 # outwards (+x on the right half)
    return np.array([t[0], 0, t[1]])
def hermite(p0, t0, p1, t1, n=24):
    L = np.linalg.norm(p1 - p0); s = np.linspace(0, 1, n)[:, None]
    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    return h00 * p0 + h10 * L * 0.6 * t0 + h01 * p1 + h11 * L * 0.6 * t1
PLAN = os.environ.get("UR_PLAN")                       # the outer edge (spine) in ONE plane: best-fit plane z = a x + b y + c
if PLAN:
    A_ = np.c_[edge[:, 0], edge[:, 1], np.ones(len(edge))]; cf = np.linalg.lstsq(A_, edge[:, 2], rcond=None)[0]
    dz = A_ @ cf - edge[:, 2]; edge = edge.copy(); edge[:, 2] = A_ @ cf
    print("SPINARE intr-un plan: z = %.4f x + %.4f y + %.1f (inclinat %.1f grd), mutata max %.1f m" % (cf[0], cf[1], cf[2], np.degrees(np.arctan(np.hypot(cf[0], cf[1]))), np.abs(dz).max()))
CONT, W = os.environ.get("UR_CONT"), float(os.environ.get("UR_W", "30"))   # sections carry on the PS's own top / bottom curve
def ps_profile(y, x0, top):                            # PS section at y: its top (or bottom) z over x in [x0 - W, x0]
    s = ps.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if s is None: return None
    P = np.vstack(list(s.discrete)); P = P[(P[:, 0] > x0 - W) & (P[:, 0] <= x0 + 0.5)]
    if len(P) < 6: return None
    xs = np.arange(x0 - W, x0 + 0.01, 1.0); zz = []
    for x in xs:
        q = P[np.abs(P[:, 0] - x) < 1.0]
        if not len(q): return None
        zz.append(q[:, 2].max() if top else q[:, 2].min())
    return xs, np.array(zz)
def cont_curve(p_att, e_pt, top, n=24):                # quadratic fitted on the PS's last W m, carried out, landed on the edge
    pr = ps_profile(p_att[1], p_att[0], top)
    if pr is None: return None
    xs, zz = pr; u = xs - xs[-1]; c2, c1, c0 = np.polyfit(u, zz, 2); ue = e_pt[0] - xs[-1]
    if ue <= 1: return None
    uu = np.linspace(0, ue, n); z = c0 + c1 * uu + c2 * uu ** 2; dl = e_pt[2] - z[-1]; z = z + dl * (uu / ue) ** 2
    return np.c_[xs[-1] + uu, np.full(n, p_att[1]), z]
def sec_local(p, arc=10.0):                            # the PS section through p: tangent (outwards) and mean curvature over +-arc m
    s = ps.section(plane_origin=[0, p[1], 0], plane_normal=[0, 1, 0])
    if s is None: return None
    best = None
    for e in s.discrete:
        e = e[:, [0, 2]]; d = np.linalg.norm(e - p[[0, 2]], axis=1); i = np.argmin(d)
        if d[i] < 4 and (best is None or d[i] < best[0]): best = (d[i], e, i)
    if best is None: return None
    _, e, i = best; dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(e, axis=0), axis=1))]; u = np.arange(dd[0], dd[-1], 0.5)
    e = np.c_[np.interp(u, dd, e[:, 0]), np.interp(u, dd, e[:, 1])]; i = np.argmin(np.abs(u - dd[i])); k = int(arc / 0.5)
    a, b = e[max(i - k, 0)], e[min(i + k, len(e) - 1)]; t = b - a; t /= np.linalg.norm(t)
    t1 = e[min(i + 2, len(e) - 1)] - e[i]; t0 = e[i] - e[max(i - 2, 0)]
    ta, tb = e[i] - e[max(i - k, 0)], e[min(i + k, len(e) - 1)] - e[i]; ta /= np.linalg.norm(ta); tb /= np.linalg.norm(tb)
    kap = np.arctan2(ta[0] * tb[1] - ta[1] * tb[0], ta @ tb) / (2 * arc * 0.5 + 1e-9)   # signed turn per metre
    if t[0] < 0: t, kap = -t, kap                     # outwards; the turn's sense is kept (seen from the front)
    return t, kap
def cont_g2(p_att, e_pt, n=24):                        # quintic: PS's point, direction and curvature -> edge, level, straight
    loc = sec_local(p_att)
    if loc is None: return None
    t0, k0 = loc; p0, p1 = p_att[[0, 2]], e_pt[[0, 2]]; L = np.linalg.norm(p1 - p0)
    k0 = np.clip(k0, -0.8 / L, 0.8 / L)               # capped: the curve may not loop
    n0 = np.array([-t0[1], t0[0]]); d0, dd0 = L * t0, L * L * k0 * n0; d1, dd1 = np.array([L, 0.0]), np.zeros(2)
    s_ = np.linspace(0, 1, n)[:, None]
    h = [1 - 10*s_**3 + 15*s_**4 - 6*s_**5, s_ - 6*s_**3 + 8*s_**4 - 3*s_**5, 0.5*s_**2 - 1.5*s_**3 + 1.5*s_**4 - 0.5*s_**5,
         10*s_**3 - 15*s_**4 + 6*s_**5, -4*s_**3 + 7*s_**4 - 3*s_**5, 0.5*s_**3 - s_**4 + 0.5*s_**5]
    q = h[0] * p0 + h[1] * d0 + h[2] * dd0 + h[3] * p1 + h[4] * d1 + h[5] * dd1
    return np.c_[q[:, 0], np.full(n, p_att[1]), q[:, 1]]
out = {"contur_margine": edge, "contur_prindere_sus": R[:, 0], "contur_prindere_jos": R[:, 3]}
d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(edge, axis=0), axis=1))]; picks = [np.argmin(np.abs(d - x)) for x in np.arange(0, d[-1], PAS)] + [len(R) - 1]
for k, i in enumerate(picks):
    top, bot, e = R[i, 0], R[i, 3], edge[i]; out_dir = np.array([1.0, 0, 0])
    ts = tangent(top, True); tb = tangent(bot, False)
    ts = ts if ts is not None else out_dir; tb = tb if tb is not None else out_dir
    et, eb = e + [0, 0, MG / 2], e - [0, 0, MG / 2]
    up = hermite(top, ts, et, out_dir); dn = hermite(bot, tb, eb, out_dir)
    if CONT:
        cu, cd = cont_g2(top, et), cont_g2(bot, eb)
        if cu is not None: up = cu
        if cd is not None: dn = cd
    tip = et + (MG / 2) * np.c_[np.sin(np.linspace(0, np.pi, 9)), np.zeros(9), np.cos(np.linspace(0, np.pi, 9))] - [0, 0, MG / 2]
    tip = e + np.c_[(MG / 2) * np.sin(np.linspace(0, np.pi, 9)), np.zeros(9), (MG / 2) * np.cos(np.linspace(0, np.pi, 9))]
    out["sectiune_%02d" % k] = np.vstack([up, tip[1:-1], dn[::-1]])
print("URECHE: margine %.0f m (y %.0f..%.0f), %d sectiuni la %.0f m, margine %.0f m grosime" % (d[-1], edge[:, 1].min(), edge[:, 1].max(), len(picks), PAS, MG))
for k, i in enumerate(picks[::3]): print("   y %5.0f: prindere sus z %.0f (x %.0f), jos z %.0f, margine x %.0f z %.0f" % (R[i, 0, 1], R[i, 0, 2], R[i, 0, 0], R[i, 3, 2], edge[i, 0], edge[i, 2]))
S = {k.replace("contur_", "contur_") + "_S": v * [-1, 1, 1] for k, v in out.items()}
np.savez(OUT, **{k + "_D": v for k, v in out.items()}, **S)

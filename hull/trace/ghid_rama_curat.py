# The rim's outline guides to the guide-line standard (asked: each outline in one plane, the inner and the inner-bottom
# always in the same plane as each other, all 3 smooth and straight - the standard of guide lines). Built only from
# straight lines and circle arcs, tangent where they meet, right half mirrored, each line at one height:
#   side: straight line x = A + B y (fitted to the current outline, y SY0..SY1); head: an arc tangent to the side at y YQ
#   through the tip, the two arcs (right / mirror) rounded at the tip by RT; back: straight line y = YB, corner rounded RC;
#   U recess: a circle on the axis through the current recess point (radius RU), joined to the back line by a fillet RF.
# The inner outline: the same lines RW m in, the same arc centres (radii -RW for the head, +RW for the recess), its own
# corner / tip rounds (RCI / RTI); the inner-bottom = the inner outline H m lower (one above the other). Sections every
# PAS m: straight from the outer point to the nearest inner point (vertical plane), the ghid_rama.py profile. Usage: python ghid_rama_curat.py <ghid_rama.npz (current)> <out.npz>
# env SY0=0 SY1=300 YQ=330 RT=8 RC=10 RF=8 RU=30 RCI=5 RTI=4 PAS=40 YT_PLUS=0 (head aimed further forward) EXTRA_OFF=0 (+ an outline that far inside the inner one) H_RAMA=m (height at the inner edge)
import sys, os, numpy as np
G = np.load(sys.argv[1]); OUT = sys.argv[2]; e = lambda k, d: float(os.environ.get(k, d))
SY0, SY1, YQ, RT, RC, RF, RU, RCI, RTI, PAS = (e(k, d) for k, d in (("SY0", "0"), ("SY1", "300"), ("YQ", "330"), ("RT", "8"), ("RC", "10"),
                                                                ("RF", "8"), ("RU", "30"), ("RCI", "5"), ("RTI", "4"), ("PAS", "40")))
E = G["contur_rama_exterior"]; ZP = float(E[0, 2]); H = ZP - float(G["contur_rama_interior_jos"][0, 2])
if os.environ.get("H_RAMA"): H = float(os.environ["H_RAMA"])   # the rim's height at its inner edge
Ii = G["contur_rama_interior"][:, :2]; RW = float(np.median([np.min(np.linalg.norm(Ii - p, axis=1)) for p in E[::10, :2]]))
R_ = E[(E[:, 0] > 0) & (E[:, 1] > SY0) & (E[:, 1] < SY1), :2]; B, A = np.polyfit(R_[:, 1], R_[:, 0], 1)
YT = float(E[:, 1].max()) + e("YT_PLUS", "0"); YB = float(E[:, 1].min()); back = E[(np.abs(E[:, 0]) < 1.5) & (E[:, 1] < 100), 1]; YU0 = float(back.max())
def arc(c, r, a0, a1, step=0.5):
    n = max(int(abs(a1 - a0) * r / step), int(abs(a1 - a0) / np.radians(3)) + 2); t = np.linspace(a0, a1, n); return np.c_[c[0] + r * np.cos(t), c[1] + r * np.sin(t)]
def seg(p, q, step=0.5): n = max(int(np.linalg.norm(q - p) / step), 2); return np.linspace(p, q, n)
def fillet_ll(p0, d0, p1, d1, r):                     # fillet between line p0 + t d0 and p1 + s d1 (unit dirs, travel order)
    nrm0 = np.array([-d0[1], d0[0]]); nrm1 = np.array([-d1[1], d1[0]]); cr = d0[0] * d1[1] - d0[1] * d1[0]; sg = 1 if cr > 0 else -1
    # centre: offset both lines by r towards the turn and intersect
    a0 = p0 + sg * r * nrm0; a1 = p1 + sg * r * nrm1; M = np.c_[d0, -d1]; t, s = np.linalg.solve(M, a1 - a0); c = a0 + t * d0
    t0 = c - sg * r * nrm0; t1 = c - sg * r * nrm1; return c, t0, t1, sg
def build(off, rc, rt):
    s_ = np.hypot(1, B); dL = np.array([B, 1.0]) / s_; nout = np.array([1.0, -B]) / s_          # side direction (up), outward normal
    Aoff = A - off * s_
    Q = np.array([A + B * YQ, YQ]); T = np.array([0.0, YT]); v = T - Q; Rh = -(v @ v) / (2 * (nout @ v)); Ch = Q - Rh * nout   # head arc
    Rh_o = Rh - off; Qo = Ch + Rh_o * nout                                                    # concentric
    xh, yh = Ch; rt_c = (0.0, yh + np.sqrt((Rh_o - rt) ** 2 - xh ** 2)); Ct = np.array(rt_c)       # tip round: on the axis, inside the arc
    u = (Ct - Ch) / np.linalg.norm(Ct - Ch); Pt = Ch + Rh_o * u                                    # tangency tip round / head arc
    tip = arc(Ct, rt, np.pi / 2, np.arctan2(Pt[1] - Ct[1], Pt[0] - Ct[0]))
    head = arc(Ch, Rh_o, np.arctan2(Pt[1] - yh, Pt[0] - xh), np.arctan2(Qo[1] - yh, Qo[0] - xh))
    ybb = YB + off; Pc = np.array([Aoff + B * ybb, ybb])                                          # side / back corner
    c, t0, t1, _ = fillet_ll(Qo, -dL, Pc, np.array([-1.0, 0.0]), rc)
    side = seg(Qo, t0); corner = arc(c, rc, np.arctan2(t0[1] - c[1], t0[0] - c[0]), np.arctan2(t1[1] - c[1], t1[0] - c[0]))
    # U recess: circle centre (0, yuc), radius ru (+off), the boundary reaching (0, YU0 + off); fillet RF (+off) to the back line
    ru = RU + off; yuc = YU0 - RU; rf = RF                                                # fillet inside the shape (a convex corner)
    cy = ybb + rf; dx2 = (ru + rf) ** 2 - (cy - yuc) ** 2
    if dx2 <= 0: raise SystemExit("recess too shallow for these radii")
    Cf = np.array([np.sqrt(dx2), cy]); tb = np.array([Cf[0], ybb]); Cu = np.array([0.0, yuc]); tu = Cu + ru * (Cf - Cu) / (ru + rf)
    backl = seg(t1, tb); fil = arc(Cf, rf, -np.pi / 2, np.arctan2(tu[1] - cy, tu[0] - Cf[0]))
    rec = arc(Cu, ru, np.arctan2(tu[1] - yuc, tu[0]), np.pi / 2)
    half = np.vstack([tip, head[1:], side[1:], corner[1:], backl[1:], fil[1:], rec[1:]])
    full = np.vstack([half, (half[::-1] * [-1, 1])[1:-1]])
    return full, dict(Rh=Rh_o, Ch=Ch, ru=ru, yuc=yuc, tip=YT if off == 0 else Ct[1] + rt)
ext, ie = build(0.0, RC, RT); inn, ii_ = build(RW, RCI, RTI)
def check(p):                                          # the standard: no kinks (max turn between 0.5 m steps), no self-crossing
    d = np.diff(np.vstack([p, p[:1]]), axis=0); ang = np.degrees(np.abs(np.angle(np.exp(1j * (np.arctan2(d[1:, 1], d[1:, 0]) - np.arctan2(d[:-1, 1], d[:-1, 0]))))))
    return ang.max()
EX = e("EXTRA_OFF", "0")                               # an extra outline EXTRA_OFF m inside the inner one (same lines / centres)
if EX > 0: extra, _ = build(RW + EX, RCI, RTI)
out = {"contur_rama_exterior": np.c_[ext, np.full(len(ext), ZP)], "contur_rama_interior": np.c_[inn, np.full(len(inn), ZP)],
       "contur_rama_interior_jos": np.c_[inn, np.full(len(inn), ZP - H)]}
if EX > 0: out["contur_offset_extra"] = np.c_[extra, np.full(len(extra), ZP)]
cc = np.vstack([ext, ext[:1]]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cc, axis=0), axis=1))]; k = 0
for t in np.arange(0, d[-1] / 2 + 0.1, PAS):
    i = np.searchsorted(d, t); p = np.array([np.interp(t, d, cc[:, 0]), np.interp(t, d, cc[:, 1])])
    if p[0] < -0.1: continue
    q_ = inn[np.argmin(np.linalg.norm(inn - p, axis=1))]                          # straight to the nearest inner point (shortest,
    s = np.linspace(0, 1, 25); bot = np.c_[p + np.outer(s, q_ - p), ZP - H * np.sqrt(np.clip(1 - (1 - s) ** 2, 0, 1))]   # one vertical plane)
    top = np.c_[p + np.outer(s[::-1], q_ - p), np.full(25, ZP)]; sec = np.vstack([bot, top])
    out["sectiune_rama_%02d_D" % k] = sec
    if p[0] > 0.1: out["sectiune_rama_%02d_S" % k] = sec * [-1, 1, 1]
    k += 1
print("VARF exterior la y %.1f" % ext[:, 1].max())
print("CONTUR RAMA (linii + arce): latura x = %.1f %+.3f y; cap arc R %.0f (pana la y %.0f), varf rotunjit R %.0f; spate drept y %.1f, colt R %.0f; U arc R %.0f (punct y %.1f), racord R %.0f" % (
    A, B, ie["Rh"], YT, RT, YB, RC, RU, YU0, RF))
print("   interior la %.1f m: aceleasi linii / centre (cap R %.0f, U R %.0f), colt R %.0f, varf R %.0f; interior_jos = interiorul la z %.1f (acelasi x, y)" % (RW, ii_["Rh"], ii_["ru"], RCI, RTI, ZP - H))
print("   planuri: exterior z %.1f, interior z %.1f, interior_jos z %.1f (fiecare o singura inaltime); cea mai mare frangere intre pasi de 0,5 m: ext %.2f grd, int %.2f grd; %d sectiuni" % (
    ZP, ZP, ZP - H, check(ext), check(inn), k))
dv = [np.min(np.linalg.norm(ext - q, axis=1)) for q in E[::3, :2]]; print("   fata de conturul de dinainte: medie %.1f m, max %.1f m" % (np.mean(dv), np.max(dv)))
np.savez(OUT, **out)

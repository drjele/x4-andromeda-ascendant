# Guides read off the PS and the rear arms as they are (asked: the ears put aside, PS and arms adjusted a little first - guides
# on them to point at): PS - its outline seen from above (drawn in a plane just over the deck), its profile on the axis (top /
# bottom), its real sections every PAS m; arms - outline seen from above, centre line, sections every PAS_B m (both sides).
# Ship coordinates (x from the axis). Usage: python ghidaje_piese.py <pieces.npz> <out.npz> ; env GP_PAS=40 GP_PAS_B=60 GP_Y_B=-1000
import sys, os, numpy as np, trimesh
D = np.load(sys.argv[1]); OUT = sys.argv[2]; MX = -1700.0
PAS, PB, YB = float(os.environ.get("GP_PAS", "40")), float(os.environ.get("GP_PAS_B", "60")), float(os.environ.get("GP_Y_B", "-1000"))
def T(n): return trimesh.Trimesh(D[n + "__v"] - [MX, 0, 0], D[n + "__f"], process=False)
ps = T("PS"); out = {}
def loops(m, y): s = m.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]); return [] if s is None else [e for e in s.discrete]
y0, y1 = ps.vertices[:, 1].min() + 1, ps.vertices[:, 1].max() - 1; ZT = ps.vertices[:, 2].max() + 4
ys = np.arange(y1, y0, -2.0); R, L, TOP, BOT = [], [], [], []
for y in ys:
    P = np.vstack(loops(ps, y)) if loops(ps, y) else None
    if P is None: continue
    R.append((P[:, 0].max(), y)); L.append((P[:, 0].min(), y)); ax = P[np.abs(P[:, 0]) < 1.5]
    if len(ax): TOP.append((y, ax[:, 2].max())); BOT.append((y, ax[:, 2].min()))
R, L = np.array(R), np.array(L)
out["contur_PS_sus"] = np.vstack([np.c_[R[:, 0], R[:, 1], np.full(len(R), ZT)], np.c_[L[::-1, 0], L[::-1, 1], np.full(len(L), ZT)], [[R[0, 0], R[0, 1], ZT]]])
TOP, BOT = np.array(TOP), np.array(BOT)
out["contur_PS_profil_sus"] = np.c_[np.zeros(len(TOP)), TOP[:, 0], TOP[:, 1]]; out["contur_PS_profil_jos"] = np.c_[np.zeros(len(BOT)), BOT[:, 0], BOT[:, 1]]
k = 0
for y in np.arange(np.floor(y1 / PAS) * PAS, y0, -PAS):
    for e in loops(ps, y): out["sectiune_PS_%02d_%d" % (k, len(out) % 97)] = e
    k += 1
for side in ("D", "S"):
    br = T("brat_spate_" + side); yb0 = br.vertices[:, 1].max() - 2; C, Ro, Ri = [], [], []
    for y in np.arange(yb0, YB, -4.0):
        ls = [e for e in loops(br, y) if len(e) > 8]
        if not ls: continue
        e = max(ls, key=lambda q: len(q)); C.append(e.mean(0)); xo = e[:, 0].max() if side == "D" else e[:, 0].min(); xi = e[:, 0].min() if side == "D" else e[:, 0].max()
        Ro.append((xo, y)); Ri.append((xi, y))
    C, Ro, Ri = np.array(C), np.array(Ro), np.array(Ri)
    out["contur_brat_%s_centru" % side] = C; zb = br.vertices[:, 2].max() + 4
    out["contur_brat_%s_sus_ext" % side] = np.c_[Ro[:, 0], Ro[:, 1], np.full(len(Ro), zb)]; out["contur_brat_%s_sus_int" % side] = np.c_[Ri[:, 0], Ri[:, 1], np.full(len(Ri), zb)]
    for j, y in enumerate(np.arange(np.floor(yb0 / PB) * PB, YB, -PB)):
        ls = [e for e in loops(br, y) if len(e) > 8]
        if ls: out["sectiune_brat_%s_%02d" % (side, j)] = max(ls, key=lambda q: len(q))
print("GHIDAJE PIESE: PS y %.0f..%.0f (%d sectiuni la %.0f m), contur de sus la z %.0f, profil pe axa; brate pana la y %.0f (sectiuni la %.0f m); %d linii" % (
    y1, y0, k, PAS, ZT, YB, PB, len(out)))
np.savez(OUT, **out)

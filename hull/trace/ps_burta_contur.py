# Outlines for the conical belly V (asked: slightly conical, following the body's contour like the reference): the body's
# outline seen from above (the V with the round nose) cut at the back by y = 0, offset inward by MARGINE (the reference
# plate keeps ~90 m from the body's edge) for the top, by MARGINE + CON for the bottom (the cone), with rounded steps in
# between for the lower edge; offsets from a distance field at 0.5 m, contours smoothed. Writes loops (x, y) + z.
# Usage: python ps_burta_contur.py <corp.npz> <out.npz>
import sys, os, numpy as np, cv2
B = np.load(sys.argv[1]); OUT = sys.argv[2]; env = lambda k, d: float(os.environ.get(k, d))
MG, CON, ZB, ZJ, RR = env("BV_MARGINE", "92"), env("BV_CON", "10"), env("CORP_BURTA", "256"), env("BV_JOS", "236"), env("BV_RAZA", "6")
ys, E = B["ys"], B["edge"]; px = 0.5; x0, y0 = -250.0, -210.0; Wd, Hd = int(500 / px), int(700 / px)
img = np.zeros((Hd, Wd), np.uint8)
if os.environ.get("BV_FORMA", "v") == "v":                              # the reference plate's own V: straight sides from
    YT, WR, RT = env("BV_VARF_Y", "276"), env("BV_LAT", "94"), env("BV_VARF_R", "25")   # (WR, 0) tangent to a round tip
    cy = YT - RT; Pp, Cc = np.array([WR, 0.0]), np.array([0.0, cy]); d_ = np.linalg.norm(Cc - Pp); be = np.arcsin(RT / d_); u0 = (Cc - Pp) / d_
    tx, ty = max([Pp + np.array([[np.cos(b), -np.sin(b)], [np.sin(b), np.cos(b)]]) @ u0 * np.sqrt(d_ ** 2 - RT ** 2) for b in (be, -be)], key=lambda p: p[0])
    yy = np.r_[np.arange(-200, 0, 2.0), np.arange(0, YT, 0.5)]
    ee = np.where(yy <= ty, WR + (tx - WR) * np.clip(yy, 0, None) / ty, np.sqrt(np.clip(RT ** 2 - (yy - cy) ** 2, 0, None))); MG = 0.0
else:                                                                   # or the body's outline, set in by MARGINE
    Er = float(np.interp(0.0, ys, E)); yy = np.r_[np.arange(-200, 0, 2.0), ys[ys >= 0]]; ee = np.r_[np.full(100, Er), E[ys >= 0]]
poly = np.array([(e, y) for y, e in zip(yy, ee)] + [(-e, y) for y, e in zip(yy[::-1], ee[::-1])])   # runs on past the back, cut at y = 0
cv2.fillPoly(img, [np.round((poly - [x0, y0]) / px).astype(np.int32)], 1)
dist = cv2.distanceTransform(img, cv2.DIST_L2, 5) * px
def loop(d):
    rear = d - MG                                                       # the back edge: straight, set in by the cone only
    m = (dist > max(d, 0.6)).astype(np.uint8); cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=cv2.contourArea)[:, 0].astype(float)
    P = c * px + [x0, y0]; k = np.exp(-0.5 * (np.arange(-12, 13) / 4.0) ** 2); k /= k.sum()
    P = np.stack([np.convolve(np.r_[P[-12:, i], P[:, i], P[:12, i]], k, "valid") for i in range(2)], 1)
    P = P[P[:, 1] > rear - 40]; P[:, 1] = np.maximum(P[:, 1], rear)
    if np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) < 0: P = P[::-1]
    i0 = int(np.argmax(P[:, 1])); P = np.roll(P, -i0, 0)                # start at the tip
    s_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1))]; u = np.linspace(0, s_[-1], 400, endpoint=False)
    return np.stack([np.interp(u, s_, np.r_[P[:, i], P[0, i]]) for i in range(2)], 1)
L, Z = [loop(MG)], [ZB + 1]
if os.environ.get("BV_JOS_SCALA"):                                      # asked: the bottom smaller and toward the back - the bottom
    SC_, AN_ = env("BV_JOS_SCALA", "0.55"), env("BV_JOS_ANCORA", "0.15")  # loop = the top loop shrunk toward a point AN_ of the length
    T0 = L[0].copy()
    if os.environ.get("BV_VARF_NOU_Y"):                                 # the tip further back and sharper: the front part pulled back
        ya, yt, yn, ka = env("BV_VARF_DE_LA", "250"), T0[:, 1].max(), env("BV_VARF_NOU_Y", "410"), env("BV_ASCUTIT", "0.35")
        u = np.clip((T0[:, 1] - ya) / (yt - ya), 0, 1); T0[:, 1] = np.where(T0[:, 1] > ya, ya + u * (yn - ya), T0[:, 1]); T0[:, 0] *= 1 - ka * u ** 1.5
        L[0] = T0
    anc = np.array([0.0, T0[:, 1].min() + AN_ * np.ptp(T0[:, 1])])  # from the back; the wall between them: straight cone
    for t in np.linspace(0, 1, 12)[1:]:                                 # + a rounded lower edge (last steps)
        sc_ = 1 - (1 - SC_) * t; L.append(anc + (T0 - anc) * sc_); Z.append(ZB + 1 - (ZB + 1 - ZJ - RR) * t)
    for t in np.linspace(0, np.pi / 2, 6)[1:]:
        sc_ = SC_ * (1 - 0.08 * (1 - np.cos(t))); L.append(anc + (T0 - anc) * sc_); Z.append(ZJ + RR - RR * np.sin(t))
    np.savez(OUT, loops=np.array(L), z=np.array(Z)); print("CONTUR BURTA: sus %.0f x %.0f m, jos %.0f x %.0f m, ancorat la %.0f%% din lungime de la spate" % (np.ptp(T0[:, 0]), np.ptp(T0[:, 1]), np.ptp(L[-1][:, 0]), np.ptp(L[-1][:, 1]), 100 * AN_)); sys.exit(0)
for t in np.linspace(0, 1, 10)[1:]:                                    # the cone + rounded lower edge
    L.append(loop(MG + CON * t)); Z.append(ZB + 1 - (ZB + 1 - ZJ - RR) * t if t < 1 else ZJ + RR)
for t in np.linspace(0, np.pi / 2, 6)[1:]: L.append(loop(MG + CON + RR * (1 - np.cos(t)))); Z.append(ZJ + RR - RR * np.sin(t))
np.savez(OUT, loops=np.array(L), z=np.array(Z))
print("CONTUR BURTA: varf y %.0f, lata %.0f m sus, %.0f m jos, spate la y %.0f / %.0f, z %.0f -> %.0f" % (L[0][:, 1].max(), np.ptp(L[0][:, 0]), np.ptp(L[-1][:, 0]), L[0][:, 1].min(), L[-1][:, 1].min(), Z[0], Z[-1]))

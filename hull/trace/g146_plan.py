# nt_146 plan rails, clean: outer contour nose -> arm tip and inner contour V apex -> arm tip, from the reference silhouette (S half read on x > 0, mirrored), straight lines + tangent arcs.
import numpy as np, cv2, json, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, g1_arce as g
O = "/home/adrian/Documents/Andromeda/2026-11-05-nt146/"; c = np.load(O + "sil.npy"); c = c * [-1, 1]; h = c[c[:, 0] >= 0]
# walk the closed contour from the nose
c = np.vstack([c, c[:1]]); i0 = np.argmax(c[:, 1]); c = np.roll(c[:-1], -i0, axis=0)
if c[120, 0] < 0: c = c[::-1]
it = np.argmin(c[:, 1] + 1e3 * (c[:, 0] < 0)); 
iap = np.argmax(np.where((np.abs(c[:, 0]) < 3) & (c[:, 1] < 200), c[:, 1], -9e9)); print("nose", c[0], "lowest tip", c[it], "apex", c[iap], "n", len(c), it, iap)
t = c[it - 400:it + 300]; print("x-max pt", c[np.argmax(c[:iap, 0])])
fig, a = plt.subplots(figsize=(9, 9)); a.plot(c[it - 450:it + 350, 0], c[it - 450:it + 350, 1], "k.-", ms=1, lw=.5); a.set_aspect("equal"); a.grid(alpha=.4); a.minorticks_on(); a.grid(which="minor", alpha=.15); fig.savefig(O + "a3_varf.png", dpi=90)
np.savez(O + "sil_walk.npz", c=c, it=it, iap=iap)
# rails: fork at the arm tip left out (separate question), both rails carried straight on to the oblique end plane of the reference tip. Inner rail by exact construction:
# apex arc tangent to the axis normal + straight V + fillet + the arm's chain; outer rail one chain of long pieces.
dE = c[:it]; dE = dE[:np.argmin(np.linalg.norm(dE - [484, -743], axis=1))]; dE = np.vstack([[0, 452.5], dE[dE[:, 0] >= 0]]); RE = g.fit(dE, tol=2.5, rmin=10, x0=[0, 452.5], th0=0.0, lmin=40.0)
dI = c[it:iap + 1][::-1]; dI = dI[:np.argmin(np.linalg.norm(dI - [484, -826], axis=1))]; dI = dI[dI[:, 0] >= 0]
vp = dI[(dI[:, 0] > 22) & (dI[:, 0] < 92)]; ml, ql = np.polyfit(vp[:, 0], vp[:, 1], 1); al = np.arctan(ml); Ra, Rc = 24.0, 22.0; print("V: panta %.1f grade, dev %.2f" % (np.degrees(al), np.abs(np.polyval([ml, ql], vp[:, 0]) - vp[:, 1]).max()))
Rt = g.fit(dI[dI[:, 1] < -140], tol=1.5, rmin=10, lmin=40.0); P0 = Rt["x0"]; t0 = Rt["th0"]                   # the arm's chain, then the corner as a fillet between its first tangent and the V line
dv = np.array([np.cos(al), np.sin(al)]); dt = np.array([np.cos(t0), np.sin(t0)]); A_ = np.array([[dv[0], -dt[0]], [dv[1], -dt[1]]]); vq = np.array([0.0, ql]); sol = np.linalg.solve(A_, P0 - vq); X = vq + sol[0] * dv
turn = t0 - al
while turn > np.pi: turn -= 2 * np.pi
while turn < -np.pi: turn += 2 * np.pi
Tl = Rc * np.tan(abs(turn) / 2); ext0 = np.linalg.norm(P0 - X) - Tl; print("colt la", X.round(1), "intoarcere %.1f, tangenta %.1f, drept pana la lant %.1f" % (np.degrees(turn), Tl, ext0))
x1 = Ra * np.sin(abs(al)); y0 = (ml * x1 + ql) + Ra * (1 - np.cos(al)); vlen = (np.linalg.norm(X - [x1, ml * x1 + ql])) - Tl
RI = dict(x0=np.array([0.0, y0]), th0=0.0, seg=[(Ra * abs(al), np.sign(al) / Ra), (vlen, 0.0), (Rc * abs(turn), np.sign(turn) / Rc)] + ([(ext0, 0.0)] if ext0 > .5 else []) + Rt["seg"], dev=0, devmax=0, tot=0); RI["tot"] = sum(q[0] for q in RI["seg"])
S_, _ = g.draw(RI, .5); dd = g.KD(S_).query(dI[dI[:, 1] > -815])[0]; RI["dev"], RI["devmax"] = float(dd.mean()), float(dd.max()); print("varf V y0 = %.1f (referinta -37.5)" % y0)
A, B = np.array([505.0, -768.0]), np.array([485.0, -827.5]); nE = np.array([B[1] - A[1], A[0] - B[0]]); nE /= np.linalg.norm(nE)
def to_end(R):
    S, _ = g.draw(R, .5); L, K = R["seg"][-1]; d = np.array([np.cos(R["th0"] + sum(l * k for l, k in R["seg"])), np.sin(R["th0"] + sum(l * k for l, k in R["seg"]))]); ex = (np.dot(A - S[-1], nE)) / np.dot(d, nE); R["seg"][-1] = (L + ex, K); R["tot"] += ex; return ex
print("extindere", round(to_end(RE), 1), round(to_end(RI), 1))
for n, R in (("EXT", RE), ("INT", RI)):
    print(n, "dev medie %.2f max %.2f m, lung %.0f, %d segmente" % (R["dev"], R["devmax"], R["tot"], len(R["seg"])))
    for L, k in R["seg"]: print("   %s L %.0f %s" % ("dreapta" if k == 0 else "arc", L, "" if k == 0 else "R %.0f" % (1 / abs(k))))
SE, _ = g.draw(RE, .5); SI, _ = g.draw(RI, .5); np.savez(O + "rails_plan.npz", E=SE, I=SI); json.dump({"E": RE["seg"], "I": RI["seg"]}, open(O + "rails_seg.json", "w"))
fig, ax = plt.subplots(1, 2, figsize=(17, 9))
for a, tit in zip(ax, ("toata", "zona V")):
    a.plot(c[:, 0], c[:, 1], color=".7", lw=2.5)
    for R in (RE, RI):
        e = 0; L = np.array([s[0] for s in R["seg"]]); K = np.array([s[1] for s in R["seg"]]); S, u = g.draw(R, .5); ed = np.cumsum(L)
        for i in range(len(L)): 
            m = (u >= (ed[i - 1] if i else 0)) & (u <= ed[i]); a.plot(S[m, 0], S[m, 1], "b" if K[i] == 0 else ("r" if i % 2 else "m"), lw=1.3)
        for q in ed[:-1]: j = np.argmin(abs(u - q)); a.plot(*S[j], "k|", ms=9)
    a.set_aspect("equal"); a.grid(alpha=.3); a.set_title(tit + ": albastru = dreapta, rosu/mov = arc, gri = referinta")
ax[1].set_xlim(-10, 260); ax[1].set_ylim(-320, 100); fig.tight_layout(); fig.savefig(O + "a4_plan_arce.png", dpi=85)

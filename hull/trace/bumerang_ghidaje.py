# The 103 band's guides for its final boomerang shape (asked: keep only the right part of its outline seen from above - the
# inner blade out - then guides at about the angle of the PS nose, their tip on that outline): the outline without the blade
# (its loop cut out between the two points where it leaves and rejoins the band), and a set of curves shaped like the PS
# nose's side (tip to shoulder) put with their tip on the band's front tip, offset OFF m inwards. Flat at Z. Writes them.
# Usage: python bumerang_ghidaje.py <teren_103.npz> <teren_ps.npz> <out.npz> <sheet.png> [z] [offsets m, comma]
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
T = np.load(sys.argv[1]); P = np.load(sys.argv[2]); OUT, SHEET = sys.argv[3], sys.argv[4]; Z = float(sys.argv[5]) if len(sys.argv) > 5 else 320.0
OFF = [float(t) for t in (sys.argv[6] if len(sys.argv) > 6 else "0,12,24").split(",")]
ol = T["outline"][:, :2]; po = P["outline"][:, :2]
a0 = 150 + np.argmin(np.linalg.norm(ol[150:350] - [158, -52], axis=1)); a1 = 450 + np.argmin(np.linalg.norm(ol[450:700] - [158, -52], axis=1))
right = np.vstack([ol[a1:], ol[:a0 + 1]])                                # the band: the blade's loop (a0..a1) cut out
tip = right[np.argmax(right[:, 1])]
r = po[(po[:, 0] >= 0) & (po[:, 1] > 230)]; r = r[np.argsort(-r[:, 1])]; side = r - r[0]   # PS nose's right side, from its tip
t = np.diff(side, axis=0); nrm = np.stack([-t[:, 1], t[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1)[:, None]; nrm = np.vstack([nrm, nrm[-1:]])
if nrm[len(nrm) // 2, 0] > 0: nrm = -nrm                                # pointing inwards (towards -x)
G = {"contur_dreapta": np.c_[right, np.full(len(right), Z)]}
for k, o in enumerate(OFF): G["bot_%d" % k] = np.c_[side + tip + nrm * o, np.full(len(side), Z)]
np.savez(OUT, **G)
ang = np.degrees(np.arctan2(r[-1, 0] - r[0, 0], r[0, 1] - r[-1, 1]))
fig, a = plt.subplots(figsize=(11, 15)); a.plot(po[:, 0], po[:, 1], "-", color="0.7", lw=1, label="PS v11"); a.plot(ol[:, 0], ol[:, 1], "-", color="0.85", lw=1, label="contur 103 intreg")
a.plot(right[:, 0], right[:, 1], "g-", lw=2.5, label="partea dreapta (pastrata)")
for k, o in enumerate(OFF): q = G["bot_%d" % k]; a.plot(q[:, 0], q[:, 1], "r-", lw=1.8, label="ghidaje cu unghiul botului PS" if k == 0 else None)
a.plot(*tip, "ko"); a.set_aspect("equal"); a.grid(alpha=.3); a.legend(); a.set_xlim(40, 260); a.set_ylim(-300, 300); a.set_title("103_D: partea dreapta + ghidajele botului (varf pe varful benzii)")
fig.tight_layout(); fig.savefig(SHEET, dpi=70)
print("BUMERANG: contur dreapta %d puncte (lama scoasa, indici %d..%d); varful benzii (%.0f, %.0f); %d ghidaje cu latura botului PS (%.1f grade, %.0f m), decalate %s m spre interior" % (
    len(right), a0, a1, *tip, len(OFF), ang, np.ptp(r[:, 1]), OFF))

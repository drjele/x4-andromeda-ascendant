# The rear arm tube with one constant section (asked: the arms as thick everywhere as between the guides; towards PS a
# slight funnel is fine): the tube (ps_tube.py: centre curve + radius per angle) kept, past y = Y0 its section ramped (over
# RAMP rings) into an ellipse W x H across x up in the tube's own frame (across = horizontal, square to the tube), the
# radius per angle measured in the tube's original angle frame, so ps_corp_mesh.py reads it unchanged.
# Usage: python tub_uniform.py <tub.npz> <out.npz> <W> <H> [y0] [ramp]
import sys, numpy as np
T = dict(np.load(sys.argv[1])); OUT, W, H = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
Y0 = float(sys.argv[5]) if len(sys.argv) > 5 else -480.0; RAMP = int(sys.argv[6]) if len(sys.argv) > 6 else 60
X, C, R = T["X"], T["C"], T["R"]; K, NA = R.shape
e1 = (X[:, 0] - C) / R[:, :1]; e2 = (X[:, NA // 4] - C) / R[:, NA // 4:NA // 4 + 1]
def g1(v, sg=6.0):
    n = int(3 * sg); kk = np.exp(-0.5 * (np.arange(-n, n + 1) / sg) ** 2); kk /= kk.sum(); return np.convolve(np.pad(v, n, mode="edge"), kk, "valid")
Cs = np.stack([g1(C[:, i]) for i in range(3)], 1); tg = np.gradient(Cs, axis=0); tg /= np.linalg.norm(tg, axis=1)[:, None]
sd = np.cross(tg, [0, 0, 1.0]); ns = np.linalg.norm(sd, axis=1)
for k in range(1, K):
    if ns[k] < 0.2: sd[k] = sd[k - 1]; ns[k] = 1.0
sd /= ns[:, None]
for k in range(1, K):
    if sd[k] @ sd[k - 1] < 0: sd[k] *= -1
up = np.cross(sd, tg); up /= np.linalg.norm(up, axis=1)[:, None]
ph = np.linspace(0, 2 * np.pi, NA, endpoint=False)
U = np.cos(ph)[None, :, None] * e1[:, None] + np.sin(ph)[None, :, None] * e2[:, None]          # the original angle directions
re = 1.0 / np.sqrt((np.einsum("kij,kj->ki", U, sd) / (W / 2)) ** 2 + (np.einsum("kij,kj->ki", U, up) / (H / 2)) ** 2)
k0 = int(np.nonzero(C[:, 1] < Y0)[0][0]); w = np.clip((np.arange(K) - k0) / RAMP, 0, 1); w = w * w * (3 - 2 * w)
Rn = (1 - w[:, None]) * R + w[:, None] * re; T["R"] = Rn; T["X"] = C[:, None] + Rn[..., None] * U
np.savez(OUT, **T)
print("TUB uniform: elipsa %.1f x %.1f m de la inelul %d (y %.0f), rampa %d inele; raza inainte %.1f..%.1f, dupa %.1f..%.1f" % (W, H, k0, C[k0, 1], RAMP, R[k0:].min(), R[k0:].max(), Rn[k0 + RAMP:].min(), Rn[k0 + RAMP:].max()))

# The top silhouettes continued along the reference outline to the arms' ends (asked: keep the guides on the reference
# and go on along its outline to the end of the arms): the confirmed outer line (B, to its end) then the reference's flat
# outline (ghid_plan2.py: from above, smooth, one half mirrored) from the nearest point on, round the loop's inside, up the
# loop's far branch to its tip; the confirmed inner line (U, to its end) then the outline the other way, down the arm's
# inside, round the loop's outside, up to the same tip - the two meet there. Each junction eased over EASE m (the offset
# between the line and the outline fades out). Writes B / B_int (right half mirrored, flat).
# Usage: python ghid_extins.py <ghid_drept3.npz> <g2_t1.npz> <out.npz> [png]
import sys, numpy as np, cv2
G = np.load(sys.argv[1]); P2 = np.load(sys.argv[2]); OUT = sys.argv[3]; PNG = sys.argv[4] if len(sys.argv) > 4 else None; EASE, SG = 300.0, 30.0
g = P2["contur"]; n = len(g); R = g[:n // 2 + 1]
if R[5, 0] < 0: R = np.vstack([g[:1], g[::-1][:n // 2]])                # tip ... outside ... loop ... inside ... U
s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(R, axis=0), axis=1))]
right = lambda Q: Q[Q[:, 0] >= 0]
Bo = right(G["B"]); Bo = Bo[np.argsort(-Bo[:, 1])]                      # tip -> end
Bi = right(G["B_int"]); Bi = Bi[np.argsort(-Bi[:, 1])]                  # U -> end
far = np.nonzero(R[:, 0] > 450)[0]; it = far[np.argmax(R[far, 1])]      # the far branch's tip (highest point out there)
io = int(np.argmin(np.linalg.norm(R[:it] - Bo[-1], axis=1)))            # outline point nearest the outer line's end (before the tip)
ii = it + int(np.argmin(np.linalg.norm(R[it:] - Bi[-1], axis=1)))       # and the inner line's end (after the tip)
def ease(run, start):                                                  # the outline run shifted to start at `start`, the shift fading
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(run, axis=0), axis=1))]; w = np.clip(1 - d / EASE, 0, 1); w = w * w * (3 - 2 * w)
    return run + np.outer(w, start - run[0])
def smooth_run(Q, keep):                                               # the outline part smoothed (gaussian with twicing, ends held);
    def gs(P):                                                         # the confirmed line before it untouched
        n_ = int(3 * SG); k = np.exp(-0.5 * (np.arange(-n_, n_ + 1) / SG) ** 2); k /= k.sum()
        Z_ = np.vstack([2 * P[:1] - P[n_:0:-1], P, 2 * P[-1:] - P[-2:-n_ - 2:-1]]); return np.stack([np.convolve(Z_[:, i], k, "valid") for i in range(2)], 1)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]; u = np.arange(0, d[-1], 1.0); Q = np.stack([np.interp(u, d, Q[:, i]) for i in range(2)], 1)
    S_ = 2 * gs(Q) - gs(gs(Q)); w = np.clip(np.arange(len(Q)) / 30.0, 0, 1)[:, None]; S_ = (1 - w) * Q + w * S_; S_[0] = keep; return S_
run = ease(R[io:ii + 1], Bo[-1]); run = ease(run[::-1], Bi[-1])[::-1]   # the loop part as ONE line round the tip (both ends eased),
run = smooth_run(run, Bo[-1]); run = smooth_run(run[::-1], Bi[-1])[::-1]  # smoothed whole, then split at the tip: no point there
far_ = np.nonzero(run[:, 0] > 450)[0]; kt = far_[np.argmax(run[far_, 1])]
outer = np.vstack([Bo, run[1:kt + 1]]); inner = np.vstack([Bi, run[kt:-1][::-1]])
full = lambda H: np.vstack([(H * [-1, 1])[::-1], H[1:]]) if H[0, 0] < 1 else np.vstack([(H * [-1, 1])[::-1], H])
np.savez(OUT, B=np.vstack([(outer * [-1, 1])[::-1], outer[1:]]), B_int=np.vstack([(inner * [-1, 1])[::-1], inner[1:]]), centru=G["centru"])
print("GHIDAJE prelungite: exterior %.0f m (silueta %.0f + contur %.0f, salt la imbinare %.1f m), interior %.0f m (silueta %.0f + contur %.0f, salt %.1f m); capatul bratului la (%.0f, %.0f)" % (
    np.sum(np.linalg.norm(np.diff(outer, axis=0), axis=1)), np.sum(np.linalg.norm(np.diff(Bo, axis=0), axis=1)), s[it] - s[io], np.linalg.norm(R[io] - Bo[-1]),
    np.sum(np.linalg.norm(np.diff(inner, axis=0), axis=1)), np.sum(np.linalg.norm(np.diff(Bi, axis=0), axis=1)), s[ii] - s[it], np.linalg.norm(R[ii] - Bi[-1]), *R[it]))
if PNG:
    sc = 0.5; im = np.full((int(1900 * sc) + 20, int(1300 * sc) + 20, 3), 255, np.uint8)
    f = lambda Q: np.stack([(Q[:, 0] + 650) * sc + 10, (500 - Q[:, 1]) * sc + 10], 1).astype(np.int32)
    cv2.polylines(im, [f(g)], True, (190, 190, 190), 1)
    cv2.polylines(im, [f(np.vstack([(outer * [-1, 1])[::-1], outer[1:]]))], False, (0, 0, 220), 2); cv2.polylines(im, [f(np.vstack([(inner * [-1, 1])[::-1], inner[1:]]))], False, (220, 80, 0), 2)
    cv2.imwrite(PNG, im)

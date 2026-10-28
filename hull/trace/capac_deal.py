# The 086 hood rebuilt as a hill over the hangars, and its flat front (asked: hangars a little closer and further back; the
# front plate flat with its outline following the hood's; the hood sloping all the way back like a hill, as far as the
# hangars allow - they must not come through): NT launch tubes (40 x 30 x 80 m) at pitch PITCH, their fronts at YF, floor ZF.
# Hood top z = ZF + H(y) * (1 - (|x| / W)^N)^(1/N): across, a rounded section; at the front straight walls close round the
# hangars (W = room + wall + 5, N 6), over LB m easing back to WB wide (flared beyond the walls, N 2.6);
# along, H(y) = HF * (1 - t^P), t = (YF - y) / LH - highest at the front, falling ever faster to the back, chosen so the
# room over the tubes (clearance + wall) stays under it. The room (tubes + clearance) hollowed out, open at the front; the
# front cut flat at YF. The front plate: YF .. YF + TF, outline = the hood's section at YF, the doors cut. Both as fields,
# surface at 0 (marching cubes). Writes hood / plate verts and faces, the tubes' boxes (ship coordinates, centred).
# Usage: python capac_deal.py <out.npz> [yf] [pitch]
import sys, numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
OUT = sys.argv[1]; YF = float(sys.argv[2]) if len(sys.argv) > 2 else 255.0; PITCH = float(sys.argv[3]) if len(sys.argv) > 3 else 42.0
NT, TW, TH, TL, ZF, CL, WT, TF = 3, 40.0, 30.0, 80.0, 316.0, 3.0, 4.0, 4.0
XR = (NT - 1) / 2 * PITCH + TW / 2 + CL; ZR = ZF + 1 + TH + CL               # the room: half width, top
N_, P_, FLARE = 2.6, 2.5, 22.0
WB = XR + WT + FLARE                                                    # base half width at the back (walls + flare)
import os
TILT = float(os.environ.get("CAPAC_TILT", "0"))                          # the tubes tilted down to the back: their back end TILT m lower
WF, NF, LB = XR + WT + float(os.environ.get("CAPAC_WF", "5")), float(os.environ.get("CAPAC_NF", "6")), 70.0   # at the front: straight walls
Wy = lambda y: (lambda v: (WF + (WB - WF) * v, NF + (N_ - NF) * v))((lambda c: c * c * (3 - 2 * c))(np.clip((YF - y) / LB, 0, 1)))
drop = lambda y: TILT * np.clip((YF - y) / TL, 0, None)                  # how far the (tilted) tubes sink at y
LH = float(os.environ.get("CAPAC_LH", "230")); yr_ = np.linspace(YF - TL - CL, YF, 200); w_, n_ = Wy(yr_)
need = np.maximum(ZR - drop(yr_) + WT - ZF, 0.5) / (1 - ((XR + WT) / w_) ** n_) ** (1 / n_)   # height to clear the room's corner
HF = float(np.max(need / (1 - ((YF - yr_) / LH) ** P_)))
C = 1.0; xs = np.arange(-WB - 8, WB + 8, C); ys = np.arange(YF - LH - 8, YF + TF + 8, C); zs = np.arange(ZF - 6, ZF + HF + 8, C)
X, Y = np.meshgrid(xs, ys, indexing="ij"); t = np.clip((YF - Y) / LH, 0, 1); H = HF * (1 - t ** P_); WW, NN = Wy(Y)
u = np.clip(np.abs(X) / WW, 0, 1); ztop = ZF + H * np.maximum(1 - u ** NN, 0) ** (1 / NN)
gy, gx = np.gradient(ztop, C); sl = np.sqrt(1 + gx ** 2 + gy ** 2)
sm = lambda a, b, k: (a + b + np.sqrt((a - b) ** 2 + k ** 2)) / 2
tx = (np.arange(NT) - (NT - 1) / 2) * PITCH
Fh = np.empty((len(xs), len(ys), len(zs)), np.float32); Ff = np.empty_like(Fh)
for k, z in enumerate(zs):
    hill = (z - ztop) / sl; f = sm(sm(sm(hill, (ZF - 5) - z, 2.0), Y - YF, 1.0), np.abs(X) - WW, 1.0)   # under the hill, above the base,
                                                                        # behind the front, within the section (no base slab beyond it)
    room = np.maximum.reduce([np.abs(X) - XR, (ZF - 1) - z + 0 * X, z - (ZR - drop(Y)), (YF - TL - CL) - Y, Y - (YF + 20)])
    Fh[:, :, k] = np.maximum(f, -room)
    uf = np.clip(np.abs(X) / WF, 0, 1); sec = z - (ZF + HF * np.maximum(1 - uf ** NF, 0) ** (1 / NF))   # the hood's outline at YF
    plate = sm(sm(sm(sec, (ZF - 5) - z, 2.0), np.maximum(YF - Y, Y - (YF + TF)), 1.0), np.abs(X) - WF, 1.0)
    door = np.full(X.shape, 1e3)
    for c in tx: door = np.minimum(door, np.maximum.reduce([np.abs(X - c) - TW / 2, (ZF + 1) - z + 0 * X, z - (ZF + 1 + TH) + 0 * X]))
    Ff[:, :, k] = np.maximum(plate, -door)
def mesh(F):
    F = gaussian_filter(F, 0.5); v, f, _, _ = marching_cubes(F, 0.0, spacing=(C, C, C)); return v + [xs[0], ys[0], zs[0]], f[:, ::-1]
vh, fh = mesh(Fh); vf, ff = mesh(Ff)
boxes = np.array([[c - TW / 2, c + TW / 2, YF - TL, YF, ZF + 1, ZF + 1 + TH, TILT] for c in tx])   # + the back end's drop
np.savez(OUT, vh=vh.astype(np.float32), fh=fh.astype(np.int32), vf=vf.astype(np.float32), ff=ff.astype(np.int32), tuburi=boxes)
print("CAPAC deal: tuburi inclinate %.0f m (%.0f grade); " % (TILT, np.degrees(np.arctan2(TILT, TL))) + "hangare la x %s (pas %.0f, %.0f m intre usi), fata la y %.0f, tuburi y %.0f..%.0f; camera +-%.0f, sus z %.0f; baza +-%.0f; inaltime in fata %.0f m (z %.0f), coboara la 0 la y %.0f; %d / %d fete; fata plana %.0f x %.0f m" % (
    tx.tolist(), PITCH, PITCH - TW, YF, YF - TL, YF, XR, ZR, WB, HF, ZF + HF, YF - LH, len(fh), len(ff), 2 * WF, HF))

# The PS's back made square and thicker towards the arms (asked: the back straighter / square, its thickness closer to the
# arms'): from y SP_Y1 to the back edge SP_YE the bottom drops smoothly by SP_DZ m (the rim follows it); from y SP_YP to the
# back the ribs turn square (superellipse exponent 2 -> SP_P) and their side bulge is held to SP_E m. Shared by the guide and
# the piece builders. env SP_Y1=-18 SP_YE=-53 SP_DZ=18 SP_YP=40 SP_P=5 SP_E=6 SP_ZE=0 (0..1: the back ribs' corner raised towards the top = an L) (SP_DZ=0: the base flat; SP_PATRAT=1: square ribs anyway)
import os, numpy as np
e = lambda k, d: float(os.environ.get(k, d))
Y1, YE, DZ, YP, PX, EM = e("SP_Y1", "-18"), e("SP_YE", "-53"), e("SP_DZ", "0"), e("SP_YP", "40"), e("SP_P", "5"), e("SP_E", "6")
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
def dz(y): return -DZ * ss((Y1 - np.asarray(y, float)) / (Y1 - YE)) if DZ > 0 else np.zeros_like(np.asarray(y, float))
PAT = os.environ.get("SP_PATRAT", "1" if DZ > 0 else "0") == "1"     # the square back on its own (the base stays flat)
def wb(y): return ss((YP - np.asarray(y, float)) / (YP - YE)) if PAT else np.zeros_like(np.asarray(y, float))
def rib(e_, ze, zb, zl, w, y, k1=16, k2=40):
    """C rib in its plane (u outwards, z): bottom (0, zb) -> bulge (e, ze) -> line end (-w, zl); squarer towards the back"""
    b = float(wb(y)); p = 2 + (PX - 2) * b; e_ = e_ * (1 - b) + min(e_, EM) * b
    ze = zb + (ze - 280.0) * (zl - zb) / (zl - 280.0) if zl != 280.0 else ze          # the bulge keeps its relative height
    ze = ze + e("SP_ZE", "0") * b * (zl - 2 - ze)                                     # towards an L: the corner raised near the top
    th = np.linspace(0, np.pi / 2, k1); ph = np.linspace(0, np.pi / 2, k2)[1:]; q = 2 / p
    A1 = np.c_[e_ * np.sin(th) ** q, ze - (ze - zb) * np.cos(th) ** q]
    A2 = np.c_[-w + (e_ + w) * np.cos(ph) ** q, ze + (zl - ze) * np.sin(ph) ** q]
    return np.vstack([A1, A2])

# R109 as one solid shark fin (asked: one piece, shark fin, sharp at the front and a little wider at the back, no hole in the
# middle, sitting on an_ureche_S where it meets an_PS): axis = the ear/PS junction line seen from above (x = K*y + B), s from SB
# (back) to SF (front). Footprint half-width WB/2*(1-u)^PW (u = 0 back .. 1 front: pointed front), the back corners rounded over UR.
# Side profile: apex HM m above the surface at u = UA, leading edge HM*((1-u)/(1-UA))^PL down to the front tip, trailing edge
# HM*(u/UA)^PT down to the back. Section: sides from the base edge to a sharp ridge, lateral = w*(1-q)^PS, every point stood on
# the surface under it (ray from above onto ear + PS + PS frame), the base edge SINK m into it, bottom 1 m under that. Ends = fans.
# Left half computed in ship coords, right = its mirror.
# env FORM=masina (asked: cleaner lines, rounder at the back, like half an arrowhead, like the shark fins on cars): footprint
# and side profile = smooth beta curves u^a (1-u)^b (widest / highest near the back, round back end, long taper to a sharp front),
# section = a rounded arch (lateral w*cos, height h*sin^SE) instead of a sharp ridge; stations packed towards both ends.
#        env WA=0.5 WBB=1.3 (footprint exponents) HA=0.3 HB=1.15 (profile exponents) SE=0.8
# Usage: blender -b <scene.blend> --python fin_rechin.py -- <out npz> [x0=1600]
#        env K=0.173 B=-140.1 SB=-17 SF=167 (as y of the ends) WB=30 PW=0.8 UR=0.05 HM=34 UA=0.2 PL=1.0 PT=0.6 PS=0.7 SINK=1
import bpy, sys, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; X0 = float(a[1]) if len(a) > 1 else 1600.0
E = lambda k, d: float(os.environ.get(k, d))
K, B, YB, YF, WB, PW, UR = E("K", .173), E("B", -140.1), E("SB", -17), E("SF", 167), E("WB", 30), E("PW", .8), E("UR", .05)
HM, UA, PL, PT, PSX, SINK = E("HM", 34), E("UA", .2), E("PL", 1.0), E("PT", .6), E("PS", .7), E("SINK", 1)
V, F = [], []
for n in ("an_ureche_S", "an_PS", "an_PS_rama"):
    o = bpy.data.objects[n]; b = len(V); V += [tuple(o.matrix_world @ v.co + Vector((X0, 0, 0))) for v in o.data.vertices]
    F += [[b + i for i in p.vertices] for p in o.data.polygons]
bvh = BVHTree.FromPolygons([Vector(p) for p in V], F)
def zs(x, y):
    h = bvh.ray_cast(Vector((x, y, 2000.0)), Vector((0, 0, -1)))
    if h[0] is None: raise SystemExit("ray miss %.1f %.1f" % (x, y))
    return h[0].z
d = np.array([K, 1.0]); d /= np.linalg.norm(d); nrm = np.array([d[1], -d[0]])
P0 = np.array([K * YB + B, YB]); P1 = np.array([K * YF + B, YF]); L = np.linalg.norm(P1 - P0)
NU, NQ, NB = 121, 12, 8
us = np.linspace(0, 1, NU)
CAR = os.environ.get("FORM") == "masina"
if CAR:
    NQ = 16; us = (1 - np.cos(np.pi * np.linspace(0, 1, NU))) / 2
    WA, WBB, HA, HB, SE = E("WA", .5), E("WBB", 1.3), E("HA", .3), E("HB", 1.15), E("SE", .8)
    beta = lambda u, a_, b_: u ** a_ * (1 - u) ** b_ / ((a_ / (a_ + b_)) ** a_ * (b_ / (a_ + b_)) ** b_)
def width(u):
    if CAR: return WB / 2 * beta(u, WA, WBB)
    w = WB / 2 * (1 - u) ** PW
    return w * np.sqrt(np.clip(1 - ((UR - u) / UR) ** 2, 0, 1)) if u < UR else w
def height(u):
    if CAR: return HM * beta(u, HA, HB)
    return HM * ((1 - u) / (1 - UA)) ** PL if u >= UA else HM * (u / UA) ** PT
qs = np.linspace(0, 1, NQ)
pts, rings = [], []
for i, u in enumerate(us):
    c = P0 + d * L * u
    if i == 0 or i == NU - 1:
        rings.append(len(pts)); pts.append([*c, zs(*c) - SINK]); continue
    w, h = width(u), height(u); z0 = zs(*c); ring = []
    lat = [-w * (1 - q) ** PSX for q in qs] + [w * (1 - q) ** PSX for q in qs[::-1][1:]]
    if CAR:
        ph = np.linspace(np.pi, 0, 2 * NQ - 1); lat = list(w * np.cos(ph)); qv = list(np.sin(ph) ** SE)
    for k, lt in enumerate(lat):
        q = qv[k] if CAR else qs[k] if k < NQ else qs[2 * NQ - 2 - k]; xy = c + nrm * lt; zb = zs(*xy) - SINK
        ring.append([*xy, zb + (z0 + h - zb) * q])
    for t in np.linspace(1, -1, NB + 2)[1:-1]:      # bottom, right -> left
        xy = c + nrm * w * t; ring.append([*xy, zs(*xy) - SINK - 1])
    rings.append(len(pts)); pts += ring
R = 2 * NQ - 1 + NB; FF = []
for i in range(NU - 1):
    a0, a1 = rings[i], rings[i + 1]
    for k in range(R):
        k1 = (k + 1) % R
        if i == 0: F2 = [[a0, a1 + k1, a1 + k]]
        elif i == NU - 2: F2 = [[a0 + k, a0 + k1, a1]]
        else: F2 = [[a0 + k, a0 + k1, a1 + k1], [a0 + k, a1 + k1, a1 + k]]
        FF += F2
P = np.array(pts); FF = np.array(FF)
vol = np.einsum("ij,ij->i", P[FF[:, 0]], np.cross(P[FF[:, 1]], P[FF[:, 2]])).sum()
if vol < 0: FF = FF[:, ::-1]
np.savez(OUT, v_S=P, v_D=P * [-1, 1, 1], f=FF, f_D=FF[:, ::-1])
print("FIN: lungime %.0f m, latime spate %.0f m, varf %.0f m peste suprafata la %.0f m de spate, %d v %d f" % (L, WB, HM, UA * L, len(P), len(FF)))

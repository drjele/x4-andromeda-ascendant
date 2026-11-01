# Guides for R109 set apart from the ship (asked: make its guides somewhere else so we settle the shape there; flat base; the
# general shape of a car's radio-antenna shark fin, half an arrowhead lying on its side: the back edge at 45 deg to the
# horizontal, not 90). Local frame per variant: length along +y (front = +y), width x, up z, base = the plane z = 0.
#   profile (plane x = 0): front tip -> leading edge H*(1 - t^PL) (convex) -> apex (rounded over RA m) -> back edge straight at
#       ANG deg down to the base; variant "A" = barb (the back edge goes down and forwards, the apex overhangs the base end),
#       variant "B" = wedge (the back edge goes down and backwards, the base runs out under it)
#   base outline (plane z = 0): teardrop over the base length, half-width W/2 * u^WA (1-u)^WB normalised (round back, sharp front)
#   sections (planes y = const): arches lateral = w cos(phi), height = h sin(phi)^SE, at NS stations
# Usage: blender -b <scene.blend> --python ghidaj_fin.py -- <out.blend> <x0 of variant A> [variants=A,B] [dx between them=250]
#        env L=187 H=34 W=30 ANG=45 PL=1.6 RA=6 WA=0.5 WB=1.3 SE=0.8 NS=5 RT=0 (front tip radius of the base, m) NSB=3 EG=0.3 (vertebrae in the overhanging back, A)
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, X0 = a[0], float(a[1])
VAR = (a[2] if len(a) > 2 else "A,B").split(","); DX = float(a[3]) if len(a) > 3 else 250.0
E = lambda k, d: float(os.environ.get(k, d))
L, H, W, ANG, PL, RA, WA, WB, SE, NS, RT = E("L", 187), E("H", 34), E("W", 30), E("ANG", 45), E("PL", 1.6), E("RA", 6), E("WA", .5), E("WB", 1.3), E("SE", .8), int(E("NS", 5)), E("RT", 0); NSB, EG = int(E("NSB", 3)), E("EG", .3)
col = bpy.data.collections.get("GHIDAJ_R109") or bpy.data.collections.new("GHIDAJ_R109")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def mat(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); return m
MP, MB, MS = mat("g_fin_profil", (.9, .3, .1)), mat("g_fin_baza", (.1, .5, .9)), mat("g_fin_sectiune", (.2, .8, .3))
def poly(name, P, m, closed=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.5; sp = cu.splines.new("POLY")
    sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (*q, 1)
    sp.use_cyclic_u = closed; o = bpy.data.objects.new(name, cu); o.data.materials.append(m); o.color = (*m.diffuse_color[:3], 1); col.objects.link(o); return o
def chaikin(P, n=3, keep=()):
    P = np.asarray(P, float)
    for _ in range(n):
        Q = [P[0]]
        for i in range(len(P) - 1): Q += [.75 * P[i] + .25 * P[i + 1], .25 * P[i] + .75 * P[i + 1]]
        Q.append(P[-1]); P = np.array(Q)
    return P
k = 1 / np.tan(np.radians(ANG))          # back edge run per metre of height
for vi, v in enumerate(VAR):
    ox = X0 + vi * DX
    # apex y and base span: A = barb (apex behind the base end), B = wedge (base end behind the apex)
    ya, yb0 = (0.0, H * k) if v == "A" else (H * k, 0.0)
    t = np.linspace(0, 1, 400); lead = np.c_[ya + t * (L - ya), H * (1 - t ** PL)]         # apex -> front tip
    back = np.c_[np.linspace(yb0, ya, 80), np.linspace(0, H, 80)]                          # base end -> apex
    prof = np.r_[back, lead[1:]]; ia = len(back) - 1
    # round the apex (clean lines): Gaussian smoothing whose width fades out RA m away from the apex, ends kept, 1 m resampling
    sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))]; s0 = sl[ia]
    du = np.linspace(0, sl[-1], int(sl[-1] / 0.25) + 1); U = np.c_[np.interp(du, sl, prof[:, 0]), np.interp(du, sl, prof[:, 1])]
    g = np.exp(-0.5 * (np.arange(-int(3 * RA / 0.25), int(3 * RA / 0.25) + 1) * 0.25 / (RA / 2)) ** 2); g /= g.sum()
    pad = len(g) // 2; Up = np.r_[np.repeat(U[:1], pad, 0), U, np.repeat(U[-1:], pad, 0)]
    G = np.c_[np.convolve(Up[:, 0], g, "valid"), np.convolve(Up[:, 1], g, "valid")]        # one constant-width smoothing
    bl = np.clip(1 - (np.abs(du - s0) - 2 * RA) / (2 * RA), 0, 1); bl = bl * bl * (3 - 2 * bl)   # used only around the apex
    sm = U + bl[:, None] * (G - U); prof = U
    sl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sm, axis=0), axis=1))]; ss_ = np.linspace(0, sl[-1], int(sl[-1]) + 1)
    prof = np.c_[np.interp(ss_, sl, sm[:, 0]), np.interp(ss_, sl, sm[:, 1])]; ia = int(np.argmax(prof[:, 1]))
    top = prof[ia:]; edge = prof[:ia + 1][::-1]                                             # top line / back edge, y increasing (A)
    poly("g_fin_%s_profil" % v, [(ox, y, z) for y, z in prof], MP)
    poly("g_fin_%s_baza_profil" % v, [(ox, yb0, 0), (ox, L, 0)], MP)
    # base outline over [yb0, L]
    yb = min(yb0, ya) if v == "B" else yb0
    u = (1 - np.cos(np.pi * np.linspace(0, 1, 200))) / 2; beta = u ** WA * (1 - u) ** WB / ((WA / (WA + WB)) ** WA * (WB / (WA + WB)) ** WB)
    yy = yb + u * (L - yb); ww = W / 2 * beta
    if RT > 0:   # blunt front (asked: the tip a little blunter): the tip replaced by an arc of radius RT tangent to the outline,
        # then the outline stretched back to the full base length so the profile's front still lands on it
        C = np.c_[yy, ww]; cs = np.linspace((yb + L) / 2, L, 800)
        Cf = np.c_[np.interp(np.linspace(yy[0], yy[-1], 4000), yy, yy), np.interp(np.linspace(yy[0], yy[-1], 4000), yy, ww)]
        dist = np.array([np.min(np.hypot(*(Cf - [c, 0]).T)) for c in cs]); c = cs[dist >= RT].max()   # the circle that fits inside
        tang = Cf[np.argmin(np.hypot(*(Cf - [c, 0]).T))]; a0 = np.arctan2(tang[1], tang[0] - c)
        th = np.linspace(a0, 0, 24); arc = np.c_[c + RT * np.cos(th), RT * np.sin(th)]
        C = np.r_[C[C[:, 0] < tang[0]], arc]; C[:, 0] = yb + (C[:, 0] - yb) * (L - yb) / (C[-1, 0] - yb); yy, ww = C[:, 0], C[:, 1]
    out = np.r_[np.c_[-ww, yy], np.c_[ww, yy][::-1][1:-1]]
    poly("g_fin_%s_baza" % v, [(ox + x, y, 0) for x, y in out], MB, closed=True)
    # sections: height = the profile's height at that y
    for j, s in enumerate(np.linspace(.12, .88, NS)):
        y = yb + s * (L - yb); h = np.interp(y, top[:, 0], top[:, 1])
        w = np.interp(y, yy, ww); ph = np.linspace(np.pi, 0, 61)
        poly("g_fin_%s_sectiune_%d" % (v, j), [(ox + w * np.cos(p), y, h * np.sin(p) ** SE) for p in ph], MS)
    if v == "A" and NSB > 0:   # vertebrae in the overhanging back too (asked): closed rounded loops between the back edge and
        # the top line (egg, narrower at the back edge, EG); half-thickness = the body's width where a 45 deg line through the loop's
        # middle reaches the base (base half-width there x the arch taper at that height), so they match the front arches
        for j, y in enumerate(np.linspace(ya, yb0, NSB + 2)[1:-1]):
            zt = np.interp(y, top[:, 0], top[:, 1]); ze = np.interp(y, edge[:, 0], edge[:, 1]); zm, hh = (zt + ze) / 2, (zt - ze) / 2
            yf = y + zm * k; hf = np.interp(yf, top[:, 0], top[:, 1]); t_ = np.interp(yf, yy, ww) * np.sqrt(1 - min(zm / hf, 1) ** (2 / SE))
            ph = np.linspace(-np.pi / 2, 3 * np.pi / 2, 161)[:-1]; lat = t_ * np.cos(ph) * (1 + EG * np.sin(ph)) / (1 + EG)
            poly("g_fin_%s_sectiune_spate_%d" % (v, j), [(ox + l, y, zm + hh * np.sin(p)) for l, p in zip(lat, ph)], MS, closed=True)
    print("GHIDAJ %s: x %.0f, baza y %.0f..%.0f (%.0f m), varf y %.0f la %.0f m, spatele la %.0f grade, latime %.0f m" % (v, ox, yb, L, L - yb, ya, H, ANG, W))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

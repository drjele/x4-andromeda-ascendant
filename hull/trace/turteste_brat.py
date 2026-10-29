# The back arms flattened a little on top where they meet the PS (asked: flatten gp_brat_spate_S/D a bit on top at the PS):
# above the arm's own centre line (per 2 m slice along y) the height is scaled down so the top drops DZ m at the PS end,
# fading smoothly (smoothstep) to nothing L m back along the arm. Bottom half untouched.
# env LARG=f: wider sideways at the PS; RACORD=C2: quintic (smootherstep) fades, the funnel melting into the plain tube; DZ=PS: down to the PS's top; env PALNIE=1: funnel (full drop inside, none outside); env PLIN_PANA_LA_PS=1: full drop up to the PS's back face, the fade only behind it.
# Usage: blender -b <in> --python turteste_brat.py -- <out.blend> <DZ|PS> <L> <object> ...
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, DZS, L = a[0], a[1], float(a[2])
ps = bpy.data.objects["gp_PS"]; PW = np.array([ps.matrix_world @ v.co for v in ps.data.vertices]); YP = PW[:, 1].min()   # the PS's back face
for n in a[3:]:
    o = bpy.data.objects[n]; mw = o.matrix_world; inv = mw.inverted()
    W = np.array([mw @ v.co for v in o.data.vertices])
    y0 = YP if os.environ.get("PLIN_PANA_LA_PS", "0") == "1" else W[:, 1].max()   # full flattening up to the PS's back face, then the fade
    if DZS == "PS":                                                     # DZ=PS: the arm's top brought down to the PS's top over the arm
        xa = W[W[:, 1] > y0 - 10, 0]; m = (PW[:, 0] > xa.min()) & (PW[:, 0] < xa.max()) & (PW[:, 1] < YP + 25)
        DZ = W[(W[:, 1] < y0) & (W[:, 1] > y0 - 10), 2].max() - PW[m, 2].max(); print("TINTA %s: sus PS %.1f, sus brat %.1f -> DZ %.1f" % (n, PW[m, 2].max(), PW[m, 2].max() + DZ, DZ))
    else: DZ = float(DZS)
    b = np.floor(W[:, 1] / 2).astype(int); zc = {}; zt = {}
    for k in np.unique(b): m = b == k; zc[k] = (W[m, 2].min() + W[m, 2].max()) / 2; zt[k] = W[m, 2].max()
    XC = ps.matrix_world.translation.x; r_ = np.abs(W[:, 0] - XC)
    st = [k for k in np.unique(b) if y0 - 100 <= 2 * k <= y0 - 14]      # the straight tube behind the oblique cut: stable slices
    fit = lambda vals: np.polyfit([2 * k + 1 for k in st], vals, 1)
    fzc, fzt = fit([zc[k] for k in st]), fit([zt[k] for k in st]); frin, frout = fit([r_[b == k].min() for k in st]), fit([r_[b == k].max() for k in st])
    near = W[:, 1] > y0 - 100                                           # near the PS: centre, top and sides from the fit (no jumps at the cut)
    for k in np.unique(b):
        if 2 * k > y0 - 100: zc[k] = np.polyval(fzc, 2 * k + 1); zt[k] = np.polyval(fzt, 2 * k + 1)
    ease = (lambda t: t ** 3 * (t * (6 * t - 15) + 10)) if os.environ.get("RACORD", "") == "C2" else (lambda t: t * t * (3 - 2 * t))   # C2: no kink in slope or curvature
    s = np.clip((y0 - W[:, 1]) / L, 0, 1); w = 1 - ease(s); moved = 0
    if os.environ.get("PALNIE", "0") == "1":                            # PALNIE=1: a funnel - the full drop on the inner side (towards the
        r = r_; ri = np.polyval(frin, W[:, 1]); ro = np.polyval(frout, W[:, 1])   # ship's axis), none on the outer side (its profile kept)
        u = np.clip((ro - r) / np.maximum(ro - ri, 1e-6), 0, 1)
        w = w * ease(u)
    LG = float(os.environ.get("LARG", "0")); wl = 1 - ease(s)               # LARG=f: the arm made f wider sideways at the PS (fading like the drop)
    if LG:
        rm = (np.polyval(frin, W[:, 1]) + np.polyval(frout, W[:, 1])) / 2; sg = np.sign(W[:, 0] - XC)
        Wn = W.copy(); Wn[:, 0] = XC + sg * (rm + (r_ - rm) * (1 + LG * wl))
    for i, v in enumerate(o.data.vertices):
        c, t = zc[b[i]], zt[b[i]]
        if LG and wl[i] > 0: W[i, 0] = Wn[i, 0]; v.co = inv @ __import__("mathutils").Vector(W[i])
        if W[i, 2] > c and w[i] > 0 and t > c:
            p = W[i].copy(); p[2] = c + (W[i, 2] - c) * (1 - w[i] * DZ / (t - c)); v.co = inv @ __import__("mathutils").Vector(p); moved += 1
    o.data.update(); W2 = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    b2 = (W2[:, 1] < y0) & (W2[:, 1] > y0 - 5)
    print("TURTIT %s: %d varfuri, sus la spatele PS %.1f -> %.1f m (stins pe %.0f m inapoi)" % (n, moved, W[b2, 2].max(), W2[b2, 2].max(), L))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

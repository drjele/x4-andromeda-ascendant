# The reference pieces copied next to the rest with their terrain guides on them (to confirm before building): each piece's
# copy (ORIGINAL_ANALIZA) assembled at XA and exploded at XA + DXE (the hood lifted DZE), and the guides from ref_teren.py
# drawn on both: cross sections every STEP m (top red, bottom blue), long profiles every PSTEP m in x, the plan outline at
# the top's edge (green). Pieces: name=terrain.npz:xc:dz (dz = the copy's height shift back onto PS; top_only = no bottom).
# Usage: blender -b <f.blend> --python ghid_teren_draw.py -- <out.blend> <xa> <name=npz:xc:dz:lift[:top_only]> ...
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT, XA = a[0], float(a[1]); DXE, STEP, PSTEP = 600.0, 20.0, 40.0; sc = bpy.context.scene
col = bpy.data.collections.get("ORIGINAL_ANALIZA") or bpy.data.collections.new("ORIGINAL_ANALIZA")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
def mat(n, c):
    m = bpy.data.materials.get(n) or bpy.data.materials.new(n); m.diffuse_color = c; return m
MR, MB, MG = mat("ghid_sus", (1, 0.1, 0.1, 1)), mat("ghid_jos", (0.1, 0.3, 1, 1)), mat("ghid_contur", (0.1, 0.8, 0.2, 1))
def poly(name, P, m):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.6; sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
    for p, q in zip(sp.points, P): p.co = (q[0], q[1], q[2], 1)
    cu.materials.append(m); o = bpy.data.objects.new(name, cu); col.objects.link(o)
for spec in a[2:]:
    name, rest = spec.split("="); parts = rest.split(":"); fn, xc, dz, lift = parts[0], float(parts[1]), float(parts[2]), float(parts[3]); topo = len(parts) > 4
    T = np.load(fn); top, bot, foot = T["top"], T["bot"], T["foot"].astype(bool); x0, y0, C = float(T["x0"]), float(T["y0"]), float(T["cell"])
    ny, nx = top.shape; xs = x0 + (np.arange(nx) + 0.5) * C; ys = y0 + (np.arange(ny) + 0.5) * C
    src = bpy.data.objects[name]
    for tag, X0, Z0 in (("asm", XA, 0.0), ("expl", XA + DXE, lift)):
        c = src.copy(); c.name = "orig_%s_%s" % (tag, name); col.objects.link(c); c.location.x += X0 - xc; c.location.z += dz + Z0; c.hide_set(False); c.hide_render = False
        k = 0
        for y in np.arange(np.ceil(ys[0] / STEP) * STEP, ys[-1], STEP):  # cross sections (split where the footprint breaks)
            r = int((y - y0) / C); m = foot[r]
            for run in np.split(np.nonzero(m)[0], np.nonzero(np.diff(np.nonzero(m)[0]) > 1)[0] + 1):
                if len(run) < 3: continue
                poly("g_%s_%s_s%d" % (tag, name, k), np.stack([xs[run] + X0, np.full(len(run), y), top[r, run] + Z0], 1), MR)
                if not topo: poly("g_%s_%s_j%d" % (tag, name, k), np.stack([xs[run] + X0, np.full(len(run), y), bot[r, run] + Z0], 1), MB)
                k += 1
        for x in np.arange(-np.floor(-x0 / PSTEP) * PSTEP, -x0, PSTEP):  # long profiles
            j = int((x - x0) / C); m = foot[:, j]
            for run in np.split(np.nonzero(m)[0], np.nonzero(np.diff(np.nonzero(m)[0]) > 1)[0] + 1):
                if len(run) < 3: continue
                poly("g_%s_%s_p%d" % (tag, name, k), np.stack([np.full(len(run), x + X0), ys[run], top[run, j] + Z0], 1), MR)
                if not topo: poly("g_%s_%s_q%d" % (tag, name, k), np.stack([np.full(len(run), x + X0), ys[run], bot[run, j] + Z0], 1), MB)
                k += 1
        ol = T["outline"]                                                   # smoothed outline with its own height (ref_teren.py)
        poly("g_%s_%s_contur" % (tag, name), np.c_[ol[:, 0] + X0, ol[:, 1], ol[:, 2] + Z0], MG)
        print("GHIDAJE %s (%s): %d linii la x %.0f" % (name, tag, k + 1, X0))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

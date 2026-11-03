# Top-down map (seen from below: x mirrored so it reads like the renders) of the blade / column points inside at_PS_carena per set
# (red front, yellow back; brighter = lower z) over the carena's underside (grey; darker = higher) and the arm (blue outline).
# CONT=<usi_carena_contur.npz>: the door outlines drawn over (white closed, cyan dashed slid).
# Usage: blender -b <scene> --python harta_urma.py -- <puncte.npz> <out.png>   env RES=.25
import bpy, sys, os, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; D = np.load(a[0]); OUT = a[1]; RES = float(os.environ.get("RES", .25))
X0, X1, Y0, Y1 = -125.0, 5.0, -30.0, 170.0; W, H = int((X1 - X0) / RES), int((Y1 - Y0) / RES)
img = np.zeros((H, W, 3)) + .12
def tri_fill(P, col_fn):
    for t in P:
        mn = np.floor(((t[:, :2].min(0)) - [X0, Y0]) / RES).astype(int); mx = np.ceil(((t[:, :2].max(0)) - [X0, Y0]) / RES).astype(int)
        mn = np.clip(mn, 0, [W - 1, H - 1]); mx = np.clip(mx, 0, [W - 1, H - 1])
        if (mx <= mn).any(): continue
        gx, gy = np.meshgrid(np.arange(mn[0], mx[0] + 1), np.arange(mn[1], mx[1] + 1)); px = X0 + (gx + .5) * RES; py = Y0 + (gy + .5) * RES
        (x1, y1), (x2, y2), (x3, y3) = t[0, :2], t[1, :2], t[2, :2]; d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(d) < 1e-9: continue
        l1 = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / d; l2 = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / d; l3 = 1 - l1 - l2
        k = (l1 >= 0) & (l2 >= 0) & (l3 >= 0); z = l1 * t[0, 2] + l2 * t[1, 2] + l3 * t[2, 2]
        img[gy[k], gx[k]] = col_fn(z[k])
def faces(n, down=True):
    o = bpy.data.objects[n]; me = o.data; ox = o.matrix_world.translation.x; me.calc_loop_triangles(); V = np.array([v.co[:] for v in me.vertices]); V[:, 0] += ox - (-7000 if n.startswith("at_") else 0) - ox + ox
    V[:, 0] = np.array([v.co.x for v in me.vertices])
    return [V[list(t.vertices)] for t in me.loop_triangles if (t.normal.z < -.05) == down]
tri_fill([t for t in faces("at_PS_carena")], lambda z: np.stack([.75 - (z - 257) / 40] * 3, -1))
for s, c in (("spate", (1, .85, 0)), ("fata", (1, .15, .1))):
    A = D[s]; ix = ((A[:, 0] - X0) / RES).astype(int); iy = ((A[:, 1] - Y0) / RES).astype(int); k = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    sh = np.clip(1.15 - (A[k, 2] - 256) / 40, .4, 1)[:, None]; img[iy[k], ix[k]] = np.array(c) * sh
for xx in range(int(X0) // 10 * 10, int(X1) + 1, 10):
    i = int((xx - X0) / RES)
    if 0 <= i < W: img[:, i] = img[:, i] * .7 + .3 * (np.array((.3, .5, 1)) if xx % 50 == 0 else .35)
for yy in range(int(Y0) // 10 * 10, int(Y1) + 1, 10):
    j = int((yy - Y0) / RES)
    if 0 <= j < H: img[j, :] = img[j, :] * .7 + .3 * (np.array((.3, .5, 1)) if yy % 50 == 0 else .35)
if os.environ.get("CONT"):                                                 # door outlines: closed white, slid cyan
    C = np.load(os.environ["CONT"])
    for k in C.files:
        if k in ("SL", "DY"): continue
        P = C[k]; P = np.vstack([P, P[:1]]); col = np.array((0, 1, 1)) if k.endswith("_mutat") else np.array((1, 1, 1))
        for (x0, y0), (x1, y1) in zip(P[:-1], P[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0)) / RES * 2) + 1
            for t in np.linspace(0, 1, n):
                i, j = int((x0 + (x1 - x0) * t - X0) / RES), int((y0 + (y1 - y0) * t - Y0) / RES)
                if 0 <= i < W and 0 <= j < H and (not k.endswith("_mutat") or int(t * n) % 6 < 3): img[max(j - 1, 0):j + 1, max(i - 1, 0):i + 1] = col
img = img[:, ::-1]                                                         # seen from below: x mirrored
im = bpy.data.images.new("h", W, H); im.pixels = np.concatenate([img, np.ones((H, W, 1))], -1).ravel().tolist(); im.filepath_raw = OUT; im.file_format = "PNG"; im.save()
print("HARTA", OUT, W, H, "grila 10 m (albastru la 50 m), x de la", X0, "la", X1, "(oglindit, ca de jos), y de jos in sus", Y0, "..", Y1)

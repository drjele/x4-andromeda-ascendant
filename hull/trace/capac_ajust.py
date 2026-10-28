# The 086 hood fitted round its contents (asked: wider so the front and the 3 launch tubes fit without trouble; the walls more
# sloped, curving a little outwards where they meet PS): scaled in x by K about the middle; then every vertex below the wall
# top ZW flared outwards from the hood's middle (seen from above), by up to FL m at its bottom (ZB), growing with the square
# of the depth (a curve, steeper at the foot), not at the front (the door wall). Ship coordinates (built at DX).
# Usage: blender -b <f.blend> --python capac_ajust.py -- <out.blend> [k] [flare] [zw]
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; K = float(a[1]) if len(a) > 1 else 1.3; FL = float(a[2]) if len(a) > 2 else 20.0
ZW = float(a[3]) if len(a) > 3 else 345.0; DX = -1700.0
o = bpy.data.objects["piesa_comp_086_tutie"]; me = o.data; v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
v[:, 0] = DX + (v[:, 0] - DX) * K
zb = v[:, 2].min(); yc = (v[:, 1].min() + v[:, 1].max()) / 2; yf = v[:, 1].max()
u = np.clip((ZW - v[:, 2]) / (ZW - zb), 0, 1) ** 2                     # 0 at the wall top, 1 at its foot
d = np.stack([v[:, 0] - DX, v[:, 1] - yc], 1); n = np.linalg.norm(d, axis=1); d = d / np.maximum(n, 1e-6)[:, None]
front = np.clip((yf - 30 - v[:, 1]) / 30, 0, 1)                         # no flare on the front 30 m (the door wall)
v[:, :2] += d * (FL * u * front)[:, None]
me.vertices.foreach_set("co", v.ravel()); me.update()
inner = v[(v[:, 2] > 325) & (v[:, 2] < 340) & (v[:, 1] > 120) & (v[:, 1] < 200)]
print("CAPAC: x%.2f, evazat %.0f m la baza; x %.0f..%.0f, y %.0f..%.0f; pereti la |x| %.0f..%.0f la z 325..340" % (
    K, FL, v[:, 0].min() - DX, v[:, 0].max() - DX, v[:, 1].min(), v[:, 1].max(), np.abs(inner[:, 0] - DX).min(), np.abs(inner[:, 0] - DX).max()))
bpy.ops.wm.save_as_mainfile(filepath=OUT); print("SAVED", OUT)

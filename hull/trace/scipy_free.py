import numpy as np
def noise3(p, scale, seed):                                                 # smooth value noise on a lattice, vectorised, no scipy in Blender
    q = p / scale; i = np.floor(q).astype(np.int64); f = q - i; f = f * f * f * (f * (6 * f - 15) + 10)
    def h(a): n = (a[:, 0] * 374761393 + a[:, 1] * 668265263 + a[:, 2] * 2147483647 + seed * 144665) & 0xffffffff; n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff; return ((n ^ (n >> 16)) & 0xffff) / 65535.0
    r = np.zeros(len(p))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1): r += h(i + [dx, dy, dz]) * np.abs(1 - dx - f[:, 0]) * np.abs(1 - dy - f[:, 1]) * np.abs(1 - dz - f[:, 2])
    return r

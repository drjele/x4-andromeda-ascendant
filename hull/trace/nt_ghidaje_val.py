# Guides of a validated piece read off the piece itself: planar cuts across its long axis every STEP (at most 12) + the cut along it through its middle (planar, as agreed), each kept as its longest polylines. The piece's own surface, so the guide lies on it (0 m).
# Usage: python nt_ghidaje_val.py <val.npz> <out_dir>
import sys, numpy as np, trimesh, os
Z = np.load(sys.argv[1]); OD = sys.argv[2]
for k in Z.files:
    if not k.endswith("__v"): continue
    n = k[:-3]; v = Z[k].astype(float); f = Z[n + "__f"]; m = trimesh.Trimesh(v, f, process=False); c = (v.min(0) + v.max(0)) / 2; ev, U = np.linalg.eigh(np.cov((v - c).T)); a = U[:, 2]; b = U[:, 0]; s = (v - c) @ a; G = {}
    def add(name, nrm, org):
        try: pth = trimesh.intersections.mesh_plane(m, nrm, org)
        except Exception: return
        if len(pth) == 0: return
        import networkx as nx
        key = lambda p: tuple(np.round(p, 3)); g = nx.Graph()
        for q in pth: g.add_edge(key(q[0]), key(q[1]))
        for i, cc in enumerate(sorted(nx.connected_components(g), key=len, reverse=True)[:2]):
            h = g.subgraph(cc); st = next((p for p in h if h.degree(p) == 1), next(iter(h))); order = list(nx.dfs_preorder_nodes(h, st))
            if len(order) > 4: G["%s_%d" % (name, i)] = np.array(order[::max(1, len(order) // 300)])
    N = int(np.clip(np.ptp(s) / 40, 3, 12))
    for i, t in enumerate(np.linspace(s.min(), s.max(), N + 2)[1:-1]): add("sectiune_%02d" % i, a, c + a * t)
    add("spinare", b, c)
    np.savez(os.path.join(OD, n + "_vg.npz"), **G); print("GHID", n, len(G))

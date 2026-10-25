# A proposed profile drawn before any modelling: the version's side silhouette deformed in 2D by the planned changes
# (smooth displacement fields in y/z, read from profile_sketch.json) and drawn over the ref 01 side view: the
# current outline in orange, the proposed one in green, so the user can validate the shape first.
# Usage: python profile_sketch.py <mesh.npz> <out.png>
import sys, json, numpy as np, cv2
T = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp"; MESH, OUT = sys.argv[1:3]; sys.argv = ["x", MESH]
exec(open(f"{T}/trace/ref_extents.py").read().split("R, M = ref")[0])
P = json.load(open(f"{T}/trace/profile_sketch.json"))
y, z = g[1], g[2]; M = model(1, 2); Y, Zg = np.meshgrid(y, z, indexing="ij")
def ramp(v, a, b): u = np.clip((v - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def bump(v, a, b): u = np.clip((v - a) / (b - a), 0, 1); return np.sin(np.pi * u) ** 2
# each part group deformed by the changes that concern it (in profile the parts overlap, so a field on the union
# would tear them), then the groups united again
def field(group):
    dy = np.zeros_like(Y); dz = np.zeros_like(Y)
    if group in "AVU":
        p = P["top"]; dz += p["dz"] * bump(Y, *p["y"]) * ramp(Zg, *p["z"])
        p = P["upper_aft"]; dy += p["dy"] * ramp(Zg, *p["z"]) * ramp(Y, *p["y_from"])
    if group == "C":
        p = P["bow"]; s = 1 - (1 - p["scale"]) * bump(Y, *p["y"]); dz += np.where(Zg > p["base"], (Zg - p["base"]) * (s - 1), 0)
    if group in "AG":
        p = P["rear"]; u = ramp(-Y, -p["y"][0], -p["y"][1]); dz += (p["bottom"] + (p["top"] - p["bottom"]) * ramp(Zg, p["mid"] - p["blend"], p["mid"] + p["blend"])) * u   # top down, bottom up, blended through the middle so the end does not fold
    if group == "G":
        p = P["uarch"]; dz += p["dz"] * bump(Y, *p["y"])
    if group == "A":
        p = P["tips"]; dz += p["dz"] * ramp(Y, *p["y"]) * (1 - ramp(Zg, *p["z"]))
    return dy, dz
# the current outline (orange, right as a structure) is kept and only its points move: each point takes the parts'
# displacements blended by how near each part is, so where two parts meet the line moves smoothly and never breaks
from scipy.ndimage import distance_transform_edt
groups = [gp for gp in "CVAULHG" if model(1, 2, gp).any()]
near = {gp: distance_transform_edt(~model(1, 2, gp)) for gp in groups}; fld = {gp: field(gp) for gp in groups}
R = P.get("blend_cells", 6)
cs, _ = cv2.findContours(M.T[::-1].astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
img = cv2.imread(f"{T}/overlay/ref01/side.png"); S = 2; img = cv2.resize(img, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
for c in cs:
    if len(c) < 20: continue
    c = c[:, 0, :]; iy = c[:, 0]; iz = len(z) - 1 - c[:, 1]; wy = y[iy].astype(float); wz = z[iz].astype(float)
    W = np.stack([np.exp(-(near[gp][iy, iz] / R) ** 2) for gp in groups]); W /= np.maximum(W.sum(0), 1e-9)
    dyp = sum(W[i] * fld[gp][0][iy, iz] for i, gp in enumerate(groups)); dzp = sum(W[i] * fld[gp][1][iy, iz] for i, gp in enumerate(groups))
    k = np.exp(-0.5 * (np.arange(-6, 7) / 2.5) ** 2); k /= k.sum()                    # a light smoothing along the line
    sm = lambda a: np.convolve(np.r_[a[-6:], a, a[:6]], k, "valid")
    ny, nz = sm(wy + dyp), sm(wz + dzp)
    px, py = to_ref("side", np.stack([np.zeros(len(ny)), ny, nz], 1)); pts = np.round(np.stack([px, py], 1) * S).astype(np.int32)
    cv2.polylines(img, [pts], True, (60, 255, 90), 3, cv2.LINE_AA)
cv2.putText(img, "verde = conturul propus", (20, 40), 0, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
cv2.imwrite(OUT, img); print("SKETCH", OUT)

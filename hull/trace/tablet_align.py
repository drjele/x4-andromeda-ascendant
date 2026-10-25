# Align each tablet drawing onto its ref-01 view (SIFT + RANSAC similarity), whatever the size, crop or rotation it
# came back with. Usage: python tablet_align.py <drawings_dir> desen_1=top desen_2=front ...   (adds to align.json)
import sys, json, os, numpy as np, cv2
D = sys.argv[1]; R = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"
path = f"{D}/align.json"; res = json.load(open(path)) if os.path.exists(path) else {}
sift = cv2.SIFT_create(); clahe = cv2.createCLAHE(2.0)
for arg in sys.argv[2:]:
    name, view = arg.split("=")
    a = clahe.apply(cv2.imread(f"{D}/{name}.jpg", 0)); b = clahe.apply(cv2.imread(f"{R}/{view}.png", 0))
    ka, da = sift.detectAndCompute(a, None); kb, db = sift.detectAndCompute(b, None)
    m = [x for x, y in cv2.BFMatcher().knnMatch(da, db, k=2) if x.distance < 0.75 * y.distance]
    A, inl = cv2.estimateAffinePartial2D(np.float32([ka[x.queryIdx].pt for x in m]), np.float32([kb[x.trainIdx].pt for x in m]), method=cv2.RANSAC, ransacReprojThreshold=3)
    res[name] = {"view": view, "A": A.tolist(), "inliers": int(inl.sum()), "matches": len(m)}
    print(name, view, "scale %.3f rot %.1f inliers %d/%d" % (np.hypot(A[0, 0], A[1, 0]), np.degrees(np.arctan2(A[1, 0], A[0, 0])), inl.sum(), len(m)))
json.dump(res, open(path, "w"), indent=1)

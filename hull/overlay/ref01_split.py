# Split the designer sheet (ref 01) into its five views (the views touch, so the bands are fixed by hand), and
# write a silhouette mask per view (the ship against the black background).
import numpy as np, cv2, json
IMG = "/home/adrian/Documents/Andromeda/references/01_Andromedadesignerorthographic.jpg"; OUT = "/home/adrian/projects/drjele/x4-andromeda-ascendant/.temp/overlay/ref01"
im = cv2.imread(IMG); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
bright = cv2.GaussianBlur(g, (5, 5), 0) > 28
bands = [(0, 215), (215, 600), (600, 1030), (1030, 1390), (1390, 1680)]
names = ["side", "top", "bottom", "front", "back"]; spec = {}
for (a, b), n in zip(bands, names):
    a0, b0 = a, b; crop = im[a0:b0]; m = bright[a0:b0]
    cv2.imwrite(f"{OUT}/{n}.png", crop); cv2.imwrite(f"{OUT}/{n}_mask.png", m.astype(np.uint8) * 255)
    spec[n] = {"rows": [int(a0), int(b0)], "size": [int(crop.shape[1]), int(crop.shape[0])]}
json.dump(spec, open(f"{OUT}/views.json", "w"), indent=1); print(spec)

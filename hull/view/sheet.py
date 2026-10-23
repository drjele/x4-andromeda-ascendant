# Tile renders into one sheet: python sheet.py out.png cols img1 img2 ...
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert("RGB") for f in files]; w = max(i.width for i in ims); h = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols; S = Image.new("RGB", (cols * w, rows * h), (200, 200, 200))
for k, im in enumerate(ims): S.paste(im, ((k % cols) * w + (w - im.width) // 2, (k // cols) * h + (h - im.height) // 2))
S.save(out)

"""Generate the tileable Andromeda hull panel maps.

Run with Blender 4.2 for numpy: blender -b --python scripts/make_hull_textures.py -- <output dir> [<source dir>]
With a source directory, its hull_panels_albedo.png and hull_panels_height.png (2048 px, tileable) replace the
procedural plates. Writes PNG previews and gzipped DXT5 DDS files with full mip chains.
"""

import gzip
import subprocess
import sys
from pathlib import Path

import bpy
import numpy as np

SIZE = 2048
GRID = 32
MIN_PLATE = 128
MAX_PLATE = 640
SEAM = 3
SEED = 7
ALBEDO = 0.86
NORMAL_STRENGTH = 6.0
SOURCE_NORMAL_STRENGTH = 2.0
SOURCE_HEIGHT_BLUR = 1.5

rng = np.random.default_rng(SEED)


def split_plates():
    pending = [(0, 0, SIZE, SIZE)]
    plates = []
    while pending:
        x, y, w, h = pending.pop()
        small = w <= 2 * MIN_PLATE and h <= 2 * MIN_PLATE
        if small or (max(w, h) <= MAX_PLATE and rng.random() < 0.25):
            plates.append((x, y, w, h))
            continue
        across = h > w if abs(h - w) > GRID else rng.random() < 0.5
        span = h if across else w
        if span < 2 * MIN_PLATE:
            across, span = not across, w if across else h
        cut = int(rng.integers(MIN_PLATE // GRID, (span - MIN_PLATE) // GRID + 1)) * GRID
        if across:
            pending += [(x, y, w, cut), (x, y + cut, w, h - cut)]
        else:
            pending += [(x, y, cut, h), (x + cut, y, w - cut, h)]
    return plates


def outline(mask, x, y, w, h, width):
    mask[y : y + h, x : x + width] = True
    mask[y : y + width, x : x + w] = True


def frame(mask, x, y, w, h, width):
    outline(mask, x, y, w, h, width)
    mask[y : y + h, x + w - width : x + w] = True
    mask[y + h - width : y + h, x : x + w] = True


def tileable_noise(scale):
    field = np.fft.fft2(rng.normal(size=(SIZE, SIZE)))
    fy, fx = np.meshgrid(np.fft.fftfreq(SIZE), np.fft.fftfreq(SIZE), indexing="ij")
    field *= np.exp(-(fx**2 + fy**2) * (SIZE / scale) ** 2)
    noise = np.real(np.fft.ifft2(field))
    return (noise - noise.mean()) / (noise.std() + 1e-9)


def build():
    tone = np.zeros((SIZE, SIZE))
    smooth = np.zeros((SIZE, SIZE))
    height = np.full((SIZE, SIZE), 0.5)
    seams = np.zeros((SIZE, SIZE), bool)
    bolts = np.zeros((SIZE, SIZE), bool)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    for x, y, w, h in split_plates():
        tone[y : y + h, x : x + w] = rng.normal(0.0, 0.015)
        smooth[y : y + h, x : x + w] = rng.uniform(0.66, 0.74)
        height[y : y + h, x : x + w] += rng.choice((0.0, 0.0, 0.015, -0.015))
        outline(seams, x, y, w, h, SEAM)
        if min(w, h) >= 192 and rng.random() < 0.3:
            # An inset hatch with a bolt in each corner.
            hw = int(rng.integers(3, 7)) * GRID
            hh = int(rng.integers(2, 5)) * GRID
            hx = x + int(rng.integers(1, max(2, (w - hw) // GRID))) * GRID
            hy = y + int(rng.integers(1, max(2, (h - hh) // GRID))) * GRID
            hw, hh = min(hw, x + w - hx - GRID), min(hh, y + h - hy - GRID)
            if 2 * GRID <= hw and 2 * GRID <= hh:
                tone[hy : hy + hh, hx : hx + hw] -= 0.02
                height[hy : hy + hh, hx : hx + hw] -= 0.03
                frame(seams, hx, hy, hw, hh, 2)
                for bx, by in ((hx + 8, hy + 8), (hx + hw - 9, hy + 8), (hx + 8, hy + hh - 9)):
                    bolts |= (xx - bx) ** 2 + (yy - by) ** 2 <= 9
                bolts |= (xx - (hx + hw - 9)) ** 2 + (yy - (hy + hh - 9)) ** 2 <= 9
    grain = tileable_noise(6.0)
    wear = tileable_noise(400.0)
    albedo = ALBEDO * (1.0 + tone + 0.006 * grain + 0.02 * wear)
    albedo[seams] = 0.38
    albedo[bolts] = ALBEDO * 0.92
    height[seams] = 0.2
    height[bolts] = 0.62
    smooth = np.clip(smooth - 0.05 * np.abs(wear), 0.0, 1.0)
    smooth[seams] = 0.2
    metal = np.full((SIZE, SIZE), 0.85)
    metal[seams] = 0.4
    return maps(albedo, height, smooth, metal)


def load_grey(path):
    image = bpy.data.images.load(str(path))
    image.colorspace_settings.name = "Non-Color"
    if tuple(image.size) != (SIZE, SIZE):
        raise ValueError(f"{path}: expected {SIZE} px square")
    pixels = np.empty(SIZE * SIZE * 4, np.float32)
    image.pixels.foreach_get(pixels)
    return np.flipud(pixels.reshape(SIZE, SIZE, 4)[..., :3].mean(-1)).astype(np.float64)


def from_source(source):
    albedo = load_grey(source / "hull_panels_albedo.png")
    # A height derived from albedo has one-pixel steps that glint like scratches; soften it first.
    height = blur(load_grey(source / "hull_panels_height.png"), SOURCE_HEIGHT_BLUR)
    # Seams and recesses sit below the plate faces; they get less shine and less bare metal.
    recess = np.clip((0.5 - height) * 4.0, 0.0, 1.0)
    smooth = 0.72 - 0.47 * recess
    metal = 0.85 - 0.45 * recess
    return maps(albedo, height, smooth, metal, SOURCE_NORMAL_STRENGTH)


def blur(values, sigma):
    fy, fx = np.meshgrid(np.fft.fftfreq(SIZE), np.fft.fftfreq(SIZE), indexing="ij")
    kernel = np.exp(-2.0 * (np.pi * sigma) ** 2 * (fx**2 + fy**2))
    return np.real(np.fft.ifft2(np.fft.fft2(values) * kernel))


def maps(albedo, height, smooth, metal, strength=NORMAL_STRENGTH):
    # Wrap-around differences keep the normal map tileable; green follows the DirectX convention.
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength
    length = np.sqrt(dx**2 + dy**2 + 1.0)
    normal = np.stack((-dx / length, dy / length, np.zeros_like(dx)), -1) * 0.5 + 0.5
    normal[..., 2] = 0.0
    return {
        "diff": np.repeat(np.clip(albedo, 0, 1)[..., None], 3, -1),
        "normal": normal,
        "smooth": np.repeat(smooth[..., None], 3, -1),
        "metal": np.repeat(metal[..., None], 3, -1),
    }


def save_png(path, rgb):
    image = bpy.data.images.new(path.stem, SIZE, SIZE, alpha=True, float_buffer=False)
    image.colorspace_settings.name = "Non-Color"
    rgba = np.concatenate((rgb, np.ones((SIZE, SIZE, 1))), -1)
    # Blender stores rows bottom-up.
    image.pixels.foreach_set(np.flipud(rgba).astype(np.float32).ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()


def save_dds(png, target):
    dds = target.with_suffix(".dds")
    mips = SIZE.bit_length()
    subprocess.run(
        [
            "magick",
            str(png),
            "-define",
            "dds:compression=dxt5",
            "-define",
            f"dds:mipmaps={mips - 1}",
            f"DDS:{dds}",
        ],
        check=True,
    )
    with gzip.open(target.with_suffix(".gz"), "wb") as output:
        output.write(dds.read_bytes())
    dds.unlink()


arguments = sys.argv[sys.argv.index("--") + 1 :]
output = Path(arguments[0])
output.mkdir(parents=True, exist_ok=True)
for name, data in (from_source(Path(arguments[1])) if 1 < len(arguments) else build()).items():
    png = output / f"andromeda_panels_{name}.png"
    save_png(png, data)
    save_dds(png, output / f"andromeda_panels_{name}")
print(f"Wrote {SIZE} px tileable hull maps to {output}")

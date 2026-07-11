#!/usr/bin/env python3
"""
prep_photo.py <input.jpg> <output.png>

Step 1 of the portrait pipeline:
  1. Remove background with rembg (u2net model)
  2. Composite onto flat dark background (so ascii step has clean, even backdrop)
  3. Boost LOCAL contrast with CLAHE so facial features stay legible instead of
     collapsing into a dark blob (mirror selfies / phone shots are usually
     underlit -- CLAHE fixes this far better than a global contrast/brightness bump)

Tune here:
  CLIP_LIMIT   - how aggressive the local contrast boost is (try 2.0 - 4.0)
  TILE_GRID    - size of the local regions CLAHE equalizes independently
  BG_COLOR     - flat backdrop color composited behind the cutout (0-255, grayscale)
"""
import sys
import numpy as np
from PIL import Image
import cv2

CLIP_LIMIT = 4.0
TILE_GRID = (6, 6)
BG_COLOR = 18  # near-black flat background behind the subject


def remove_background(img: Image.Image) -> Image.Image:
    from rembg import remove, new_session
    session = new_session("u2net")
    return remove(img, session=session)


def apply_clahe(rgba: Image.Image) -> Image.Image:
    arr = np.array(rgba.convert("RGBA"))
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=TILE_GRID)
    gray_eq = clahe.apply(gray)

    # composite onto flat background using alpha as mask
    bg = np.full_like(gray_eq, BG_COLOR)
    mask = alpha.astype(np.float32) / 255.0
    composited = (gray_eq.astype(np.float32) * mask + bg.astype(np.float32) * (1 - mask))
    composited = composited.astype(np.uint8)

    return Image.fromarray(composited, mode="L")


def main():
    if len(sys.argv) != 3:
        print("usage: python prep_photo.py <input.jpg> <output.png>")
        sys.exit(1)

    src, dst = sys.argv[1], sys.argv[2]
    print(f"[prep_photo] loading {src}")
    img = Image.open(src).convert("RGB")

    print("[prep_photo] removing background (rembg/u2net)...")
    try:
        cut = remove_background(img)
    except Exception as e:
        print(f"[prep_photo] WARNING: rembg failed ({e}); falling back to no bg-removal")
        cut = img.convert("RGBA")

    print(f"[prep_photo] applying CLAHE (clipLimit={CLIP_LIMIT}, tile={TILE_GRID})...")
    out = apply_clahe(cut)

    out.save(dst)
    print(f"[prep_photo] wrote {dst}  ({out.size[0]}x{out.size[1]}, grayscale)")


if __name__ == "__main__":
    main()

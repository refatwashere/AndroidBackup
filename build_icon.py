"""
build_icon.py — Assembles all PNG icon sizes into a multi-resolution Icon.ico
Run once before building the executable:
    python build_icon.py
"""
from PIL import Image
import os

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SIZES  = [16, 32, 48, 64, 128, 256]
OUT    = os.path.join(ASSETS, "Icon.ico")

images = []
for s in SIZES:
    path = os.path.join(ASSETS, f"Icon_{s}x{s}.png")
    if os.path.exists(path):
        images.append(Image.open(path).convert("RGBA"))
        print(f"  + {s}x{s}")
    else:
        print(f"  ! Missing: Icon_{s}x{s}.png")

if images:
    images[0].save(OUT, format="ICO", sizes=[(i.width, i.height) for i in images],
                   append_images=images[1:])
    print(f"\nSaved -> {OUT}")
else:
    print("No images found.")

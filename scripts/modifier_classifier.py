import os
import numpy as np
from PIL import Image

# === CONFIG ===
MODIFIER_CLASSES = ['normal', 'DL', 'TL', 'DW', 'TW']
MODIFIER_RGB = {
    'DL': (102, 178, 255),   # Light blue
    'TL': (0, 102, 204),     # Dark blue
    'DW': (255, 204, 204),   # Light red/pink
    'TW': (204, 0, 0),       # Dark red
}
THRESHOLD = 50  # Max RGB distance allowed for match

def rgb_distance(c1, c2):
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def classify_modifier(tile_img: Image.Image) -> str:
    """Classify a tile as one of the MODIFIER_CLASSES based on average RGB"""
    tile_rgb = np.array(tile_img.resize((16, 16))).mean(axis=(0, 1))  # avg RGB
    for label, rgb in MODIFIER_RGB.items():
        if rgb_distance(tile_rgb, rgb) < THRESHOLD:
            return label
    return 'normal'

# === Example Usage ===
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python modifier_classifier.py path/to/tile.png")
        exit(1)

    img = Image.open(sys.argv[1]).convert("RGB")
    label = classify_modifier(img)
    print(f"Modifier detected: {label}")

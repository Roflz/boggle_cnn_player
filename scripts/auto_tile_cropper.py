import os
from PIL import Image

# === CONFIG ===
CROP_BOX        = (811, 508, 1395, 1090)
GRID_SIZE       = 4
RESIZED_TILE    = (64, 64)

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR  = os.path.join(BASE_DIR, "data", "screenshots")
TILE_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "unlabeled_tiles")

def crop_tiles_from_image(image_path, output_dir):
    image = Image.open(image_path)
    cropped = image.crop(CROP_BOX)
    width, height = cropped.size
    tile_w, tile_h = width // GRID_SIZE, height // GRID_SIZE

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    tile_num = 0

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            left   = col * tile_w
            top    = row * tile_h
            right  = left + tile_w
            bottom = top + tile_h

            tile = cropped.crop((left, top, right, bottom))
            tile = tile.resize(RESIZED_TILE)
            out_fname = f"{base_name}_tile_{tile_num:02}.png"
            tile.save(os.path.join(output_dir, out_fname))

            tile_num += 1

def process_all_screenshots():
    os.makedirs(TILE_OUTPUT_DIR, exist_ok=True)
    screenshots = [
        f for f in os.listdir(SCREENSHOT_DIR)
        if f.lower().endswith(".png")
    ]
    print(f"Found {len(screenshots)} screenshot(s).")

    for fname in screenshots:
        image_path = os.path.join(SCREENSHOT_DIR, fname)

        # 1) Crop & save tiles
        crop_tiles_from_image(image_path, TILE_OUTPUT_DIR)
        print(f"Cropped tiles from: {fname}")

        # 2) Delete the original screenshot
        try:
            os.remove(image_path)
            print(f"Deleted screenshot: {fname}")
        except OSError as e:
            print(f"⚠️ Could not delete {fname}: {e}")

if __name__ == "__main__":
    process_all_screenshots()

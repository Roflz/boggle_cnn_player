import argparse
from predict_tile_letter import Predictor
from solver.boggle_game_engine import BoggleSolver, load_dictionary
from play_boggle import play_words
from score_optimizer import optimize_word_order
from PIL import ImageGrab, Image
import time
import os

# === CONFIG ===
MODEL_PATH = "models/cnn_model.pt"
CROP_BOX = (811, 508, 1395, 1090)
SCREENSHOT_PATH = "data/screenshots/latest.png"

# === MAIN PIPELINE ===
def capture_board():
    print("\n📸 Capturing screenshot...")
    os.makedirs(os.path.dirname(SCREENSHOT_PATH), exist_ok=True)
    screenshot = ImageGrab.grab(bbox=CROP_BOX)
    screenshot.save(SCREENSHOT_PATH)
    time.sleep(0.2)

def classify_board(predictor, image_path):
    image = Image.open(image_path)
    width, height = image.size
    tile_w, tile_h = width // 4, height // 4

    board = []
    modifiers = []
    for r in range(4):
        row = []
        mod_row = []
        for c in range(4):
            tile = image.crop((c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h))
            letter, bonus, _, _ = predictor.predict_letter_bonus_confidence(tile)
            row.append(letter)
            mod_row.append(bonus)
        board.append(row)
        modifiers.append(mod_row)
    return board, modifiers

def solve_board(board, modifiers):
    dictionary = load_dictionary()
    solver = BoggleSolver(board, modifiers, dictionary)
    return solver.find_all_words()

def main(preview_mode):
    capture_board()

    print("\n🔍 Loading model and classifying board...")
    predictor = Predictor(MODEL_PATH)
    board, modifiers = classify_board(predictor, SCREENSHOT_PATH)

    print("\n🧠 Predicted Board:")
    for row in board:
        print(" ".join(row))

    print("\n🔎 Solving board...")
    raw_paths = solve_board(board, modifiers)
    print(f"✅ Found {len(raw_paths)} words")

    print("\n🎯 Optimizing word order for scoring...")
    paths = optimize_word_order(raw_paths)

    print("\n🎮 Executing moves...")
    play_words(paths, preview_only=preview_mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Only preview paths (no clicks)")
    args = parser.parse_args()
    main(args.preview)

# auto_boggle_runner.py

import argparse
import time
import os
from PIL import ImageGrab, Image

# === IMPORT YOUR OPTIMIZERS ===
from score_optimizer import (
    word_score,
    tune_coverage_params,
    ensure_efficient_coverage,
)

# === CONFIG ===
MODEL_PATH = "models/cnn_model.pt"
CROP_BOX   = (811, 508, 1395, 1090)

# How many top-scoring words to consider for tuning
TUNE_CANDIDATES = 60

def capture_full_screenshot():
    os.makedirs("data/screenshots", exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = f"data/screenshots/{ts}.png"
    print(f"\n📸 Capturing screenshot to {path}")
    img = ImageGrab.grab()
    img.save(path)
    time.sleep(0.2)
    return img

def classify_board(predictor, full_img):
    board_img = full_img.crop(CROP_BOX)
    w, h = board_img.size
    tw, th = w // 4, h // 4
    board, mods = [], []
    for r in range(4):
        row, mrow = [], []
        for c in range(4):
            tile = board_img.crop((c*tw, r*th, (c+1)*tw, (r+1)*th))
            letter, bonus, _, _ = predictor.predict_letter_bonus_confidence(tile)
            row.append(letter)
            mrow.append(bonus)
        board.append(row)
        mods.append(mrow)
    return board, mods

def solve_board(board, mods):
    from solver.boggle_game_engine import BoggleSolver, load_dictionary
    dictionary = load_dictionary()
    solver = BoggleSolver(board, mods, dictionary)
    return solver.find_all_words()

def main(preview_mode: bool):
    # import heavy modules inside main
    from predict_tile_letter import Predictor
    from play_boggle import play_words

    # 1) Screenshot & classify
    img = capture_full_screenshot()
    print("\n🔍 Loading model and classifying board...")
    predictor = Predictor(MODEL_PATH)
    board, mods = classify_board(predictor, img)

    print("\n🧠 Predicted Board:")
    for row in board:
        print(" ".join(row))

    # 2) Solve
    print("\n🔎 Solving board...")
    raw = solve_board(board, mods)
    print(f"✅ Found {len(raw)} words")

    # 3) Build list of (word, path)
    all_paths = [(w, p) for w, (_, p) in raw.items()]

    # 4) Pre‑sort by base score and take top candidates for tuning
    sorted_by_score = sorted(all_paths, key=lambda x: -word_score(x[0]))
    candidates = sorted_by_score[:TUNE_CANDIDATES]
    print(f"\n🔧 Tuning on top {len(candidates)} words to maximize efficiency + coverage…")
    best_params = tune_coverage_params(
        candidates,
        grid_size=4,
        max_words=len(candidates),
    )
    # remove the 'score' entry
    tune_cfg = {
        k: v for k, v in best_params.items()
        if k in ("time_per_tile", "overhead_per_word", "lambda_eff", "lambda_cov")
    }

    # 5) Pick the optimal subset + order
    selected, remaining = ensure_efficient_coverage(
        candidates,
        grid_size=4,
        max_words=len(candidates),
        **tune_cfg
    )
    final_list = selected + remaining

    # 6) Print the final play order & points
    print("\n🎯 Final optimized play order:")
    total_base = 0
    for idx, (word, path) in enumerate(final_list, start=1):
        pts = word_score(word)
        print(f"  {idx:2d}. {word:10s} → base {pts:3d}")
        total_base += pts

    # Check full coverage bonus
    all_tiles = {(r, c) for r in range(4) for c in range(4)}
    covered = set()
    for _, path in final_list:
        covered |= set(path)
    if covered == all_tiles:
        print("\n🎉 All tiles covered — +100 point bonus!")
        total_base += 100

    print(f"\n💯 Total score (including bonus): {total_base}\n")

    # 7) Play!
    print("🎮 Executing moves…")
    play_words(final_list, preview_only=preview_mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preview", action="store_true",
        help="Only preview paths (no clicks)"
    )
    args = parser.parse_args()
    main(args.preview)

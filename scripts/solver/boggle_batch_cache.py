import os
import time
import argparse
import pickle
import random
from typing import List
from collections import Counter
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from boggle_game_engine import generate_random_board, load_dictionary, is_word_possible, board_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, ".boggle_cache")
LOG_FILE = os.path.join(BASE_DIR, "logs")

# Load previously cached board hashes from log file
def load_cached_hashes(log_path: str) -> set:
    if not os.path.exists(log_path):
        return set()
    with open(log_path, "r") as f:
        return {line.split(" -> ")[0] for line in f if "->" in line}

# Generate unique random boards
def generate_unique_boards(limit: int, exclude: set) -> List[List[List[str]]]:
    seen = set(exclude)
    boards = []
    with tqdm(total=limit, desc="Generating boards") as pbar:
        while len(boards) < limit:
            board = generate_random_board([chr(c) for c in range(ord('a'), ord('z') + 1)])
            h = board_hash(board)
            if h not in seen:
                seen.add(h)
                boards.append(board)
                pbar.update(1)
    return boards

# Cache one board to file if not already cached
def cache_single_board(board: List[List[str]]):
    hash_key = board_hash(board)
    cache_file = os.path.join(CACHE_DIR, f"{hash_key}.pkl")

    if not os.path.exists(cache_file):
        all_words = load_dictionary()
        board_counter = Counter(ch for row in board for ch in row)
        filtered = [word for word in all_words if is_word_possible(word, board_counter)]

        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump(filtered, f)

        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a') as log:
            log.write(f"{hash_key} -> {board}\n")

        return 1
    return 0

# Batch process all boards with multiprocessing and progress
def batch_cache_boards(boards: List[List[List[str]]]):
    os.makedirs(CACHE_DIR, exist_ok=True)
    start = time.time()
    total_cached = 0

    with Pool(processes=cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(cache_single_board, boards), total=len(boards), desc="Caching boards"):
            total_cached += result

    elapsed = time.time() - start
    avg_time = elapsed / max(total_cached, 1)

    print(f"✅ Cached {total_cached} new boards in {elapsed:.2f}s. Avg: {avg_time:.4f}s per board.")

# === Entry Point ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cache random Boggle boards")
    parser.add_argument("--count", type=int, default=10000, help="Number of unique boards to cache")
    args = parser.parse_args()

    already_cached = load_cached_hashes(LOG_FILE)
    print(f"Found {len(already_cached)} cached boards. Target: {args.count}")
    needed = max(0, args.count - len(already_cached))

    if needed == 0:
        print("All requested boards already cached.")
    else:
        boards = generate_unique_boards(needed, already_cached)
        batch_cache_boards(boards)

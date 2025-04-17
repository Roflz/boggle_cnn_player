import random
from typing import List, Tuple, Dict, Set
from collections import defaultdict, Counter
from colorama import Fore, Style, init
import hashlib
import pickle
import os
from PIL import Image, ImageOps
import pytesseract
import numpy as np

init(autoreset=True)

# ---- Letter values like Scrabble ----
LETTER_POINTS = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2,
    'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1,
    'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1,
    'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10
}

# ---- Boggle Dice for Random Boards ----
BOGGLE_DICE_4x4 = [
    "aaeegn", "abbjoo", "achops", "affkps",
    "aoottw", "cimotu", "deilrx", "delrvy",
    "distty", "eeghnw", "eeinsu", "ehrtvw",
    "eiosst", "elrtty", "himnqu", "hlnnrz"
]

def extract_board_from_image(image_path: str, crop_coords: Tuple[int, int, int, int], grid_size=4):
    img = Image.open(image_path).convert("RGB")
    cropped = img.crop(crop_coords)
    gray = ImageOps.grayscale(cropped)

    width, height = gray.size
    tile_w, tile_h = width // grid_size, height // grid_size

    letters = []
    modifiers = []

    for r in range(grid_size):
        letter_row = []
        mod_row = []
        for c in range(grid_size):
            left = c * tile_w
            top = r * tile_h
            right = left + tile_w
            bottom = top + tile_h
            tile = gray.crop((left, top, right, bottom))
            tile = tile.resize((tile_w * 2, tile_h * 2))  # enlarge for OCR
            processed = tile.point(lambda x: 0 if x < 160 else 255, '1')
            text = pytesseract.image_to_string(processed, config='--psm 10 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ').strip()
            letter_row.append(text[0].lower() if text else '?')

            rgb_tile = cropped.crop((left, top, right, bottom)).resize((10, 10))
            avg_color = np.array(rgb_tile).mean(axis=(0, 1))
            mod_row.append(identify_modifier_from_color(avg_color))

        letters.append(letter_row)
        modifiers.append(mod_row)

    return letters, modifiers

def identify_modifier_from_color(rgb):
    r, g, b = rgb
    if g > 180 and r < 150 and b < 150:
        return 'DW'  # greenish
    elif r > 180 and b > 180 and g < 160:
        return 'TW'  # purple/magenta
    elif b > 180 and r < 150 and g < 150:
        return 'DL'  # blueish
    elif r > 180 and g < 150 and b < 150:
        return 'TL'  # red/orange
    else:
        return ''

# ---- Board Scoring Modifiers Default ----
MODIFIERS_4x4 = [
    ['DL', '', '', 'TL'],
    ['', 'DW', '', ''],
    ['', '', 'TW', ''],
    ['DL', '', '', 'DL']
]

class TrieNode:
    def __init__(self):
        self.children = {}
        self.word = None

class BoggleSolver:
    def __init__(self, board: List[List[str]], modifiers: List[List[str]], dictionary: List[str]):
        # Normalize board letters to lowercase
        self.board = [[ch.lower() for ch in row] for row in board]
        self.modifiers = modifiers
        self.rows = len(board)
        self.cols = len(board[0])
        self.trie_root = self.build_trie(dictionary)
        self.found_words: Dict[str, Tuple[int, List[Tuple[int, int]]]] = {}

    def build_trie(self, words: List[str]) -> TrieNode:
        root = TrieNode()
        for word in words:
            node = root
            for char in word:
                node = node.children.setdefault(char, TrieNode())
            node.word = word
        return root

    def dfs(self, r: int, c: int, node: TrieNode, visited: Set[Tuple[int, int]],
            score: int = 0, word_multiplier: int = 1, path: List[Tuple[int, int]] = []):

        if (r < 0 or r >= self.rows or c < 0 or c >= self.cols or
            (r, c) in visited):
            return

        letter = self.board[r][c]

        # Special handling for 'qu'
        if letter == 'qu':
            if 'q' not in node.children:
                return
            node = node.children['q']
            if 'u' not in node.children:
                return
            node = node.children['u']
            letter_score = LETTER_POINTS.get('q', 0) + LETTER_POINTS.get('u', 0)
        else:
            if letter not in node.children:
                return
            node = node.children[letter]
            letter_score = LETTER_POINTS.get(letter, 0)

        visited.add((r, c))
        path.append((r, c))

        mod = self.modifiers[r][c]
        if mod == 'DL':
            letter_score *= 2
        elif mod == 'TL':
            letter_score *= 3
        elif mod == 'DW':
            word_multiplier *= 2
        elif mod == 'TW':
            word_multiplier *= 3

        score += letter_score

        if node.word and node.word not in self.found_words:
            self.found_words[node.word] = (score * word_multiplier, path[:])

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr != 0 or dc != 0:
                    self.dfs(r + dr, c + dc, node, visited, score, word_multiplier, path)

        visited.remove((r, c))
        path.pop()

    def find_all_words(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.dfs(r, c, self.trie_root, set())
        return self.found_words


def generate_random_board(dice: List[str]) -> List[List[str]]:
    selected = [random.choice(die) for die in random.sample(dice, len(dice))]
    return [selected[i:i+4] for i in range(0, 16, 4)]


def load_dictionary(min_length=3) -> list[str]:
    # Try multiple paths to find the dictionary file
    possible_paths = [
        os.path.join("data", "words_alpha.txt"),  # Relative to project root
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "words_alpha.txt"),  # From script
        "words_alpha.txt"  # Fallback: same directory
    ]

    for path in possible_paths:
        if os.path.exists(path):
            with open(path) as f:
                return [line.strip() for line in f if len(line.strip()) >= min_length]

    raise FileNotFoundError("❌ Could not find 'words_alpha.txt' in any expected location.")


def is_word_possible(word: str, board_counter: Counter) -> bool:
    word_counter = Counter(word)
    return all(word_counter[ch] <= board_counter[ch] for ch in word_counter)

def board_hash(board: List[List[str]]) -> str:
    flat = ''.join(''.join(row) for row in board)
    return hashlib.md5(flat.encode()).hexdigest()

def get_or_cache_filtered_words(board, wordlist_path="words_alpha.txt", cache_dir=".boggle_cache"):
    os.makedirs(cache_dir, exist_ok=True)
    hash_key = board_hash(board)
    cache_file = os.path.join(cache_dir, f"{hash_key}.pkl")

    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    all_words = load_dictionary()
    board_counter = Counter(ch for row in board for ch in row)
    filtered = [
        word for word in all_words
        if is_word_possible(word, board_counter)
    ]

    with open(cache_file, 'wb') as f:
        pickle.dump(filtered, f)

    return filtered

def main():
    # Uncomment to run from a screenshot
    board, modifiers = extract_board_from_image("data\\screenshots\\Screenshot 2025-04-16 155123.png", (811, 508, 1395, 1090))

    # Uncomment to run from a randomly generated board
    # board = generate_random_board(BOGGLE_DICE_4x4)
    # modifiers = MODIFIERS_4x4
    dictionary = get_or_cache_filtered_words(board)

    solver = BoggleSolver(board, modifiers, dictionary)
    solver.print_board()
    solver.solve()
    solver.print_results()


if __name__ == "__main__":
    main()

# boggle_game_engine.py

import os
import hashlib
import pickle
from typing import List, Tuple, Dict
from collections import Counter

# ---- Letter values like Scrabble ----
LETTER_POINTS: Dict[str, int] = {
    'a': 1, 'b': 3, 'c': 3, 'd': 2,
    'e': 1, 'f': 4, 'g': 2, 'h': 4,
    'i': 1, 'j': 8, 'k': 5, 'l': 1,
    'm': 3, 'n': 1, 'o': 1, 'p': 3,
    'q': 10, 'r': 1, 's': 1, 't': 1,
    'u': 1, 'v': 4, 'w': 4, 'x': 8,
    'y': 4, 'z': 10
}

GRID_SIZE = 4
TRIE_CACHE_DIR = ".trie_cache"
DICT_CACHE_DIR = ".boggle_cache"
DICT_PATH = os.path.join("data", "twl06.txt")

os.makedirs(TRIE_CACHE_DIR, exist_ok=True)
os.makedirs(DICT_CACHE_DIR, exist_ok=True)

class TrieNode:
    __slots__ = ('children', 'word')
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.word: str = None

def board_hash(board: List[List[str]]) -> str:
    flat = ''.join(ch for row in board for ch in row)
    return hashlib.md5(flat.encode()).hexdigest()

def load_dictionary(min_length: int = 3) -> List[str]:
    with open(DICT_PATH, encoding='utf-8') as f:
        return [w.strip().lower() for w in f if len(w.strip()) >= min_length]

def get_or_cache_filtered_words(board: List[List[str]]) -> List[str]:
    key = board_hash(board)
    cache_file = os.path.join(DICT_CACHE_DIR, f"{key}.pkl")
    if os.path.exists(cache_file):
        return pickle.load(open(cache_file, 'rb'))
    full = load_dictionary()
    counts = Counter(ch for row in board for ch in row)
    filtered = [w for w in full if all(w.count(ch) <= counts[ch] for ch in set(w))]
    with open(cache_file, 'wb') as f:
        pickle.dump(filtered, f)
    return filtered

def _dfs_worker(args):
    start, B, M, neighbors, trie_root = args
    found: Dict[str, Tuple[int, List[int]]] = {}

    # initialize for start position
    ch0 = B[start]
    node = trie_root
    score0, wmul0 = 0, 1

    # handle 'qu'
    if ch0 == 'qu':
        if 'q' not in node.children: return found
        node = node.children['q']
        if 'u' not in node.children: return found
        node = node.children['u']
        ls = LETTER_POINTS['q'] + LETTER_POINTS['u']
    else:
        if ch0 not in node.children: return found
        node = node.children[ch0]
        ls = LETTER_POINTS.get(ch0, 0)

    # apply modifier
    mod0 = M[start]
    if mod0 == 'DL': ls *= 2
    elif mod0 == 'TL': ls *= 3
    elif mod0 == 'DW': wmul0 *= 2
    elif mod0 == 'TW': wmul0 *= 3

    score0 = ls
    if node.word:
        found[node.word] = (score0*wmul0, [start])

    # DFS stack
    stack = [(start, node, 1<<start, score0, wmul0, [start])]
    while stack:
        pos, nd, vis, sc, wm, path = stack.pop()
        for nxt in neighbors[pos]:
            if vis & (1<<nxt):
                continue
            ch = B[nxt]
            node2 = nd
            sc2, wm2 = sc, wm

            if ch == 'qu':
                if 'q' not in node2.children: continue
                node2 = node2.children['q']
                if 'u' not in node2.children: continue
                node2 = node2.children['u']
                ls2 = LETTER_POINTS['q'] + LETTER_POINTS['u']
            else:
                if ch not in node2.children: continue
                node2 = node2.children[ch]
                ls2 = LETTER_POINTS.get(ch, 0)

            mod2 = M[nxt]
            if mod2 == 'DL': ls2 *= 2
            elif mod2 == 'TL': ls2 *= 3
            elif mod2 == 'DW': wm2 *= 2
            elif mod2 == 'TW': wm2 *= 3

            sc2 += ls2
            new_path = path + [nxt]

            if node2.word and node2.word not in found:
                found[node2.word] = (sc2*wm2, new_path[:])

            stack.append((nxt, node2, vis | (1<<nxt), sc2, wm2, new_path))

    return found

class BoggleSolver:
    def __init__(
        self,
        board: List[List[str]],
        modifiers: List[List[str]],
        words: List[str]
    ):
        self.B = [ch.lower() for row in board for ch in row]
        self.M = [mod for row in modifiers for mod in row]

        # neighbors
        self.neighbors = [[] for _ in range(GRID_SIZE**2)]
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                i = r*GRID_SIZE + c
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            rr, cc = r+dr, c+dc
                            if 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE:
                                self.neighbors[i].append(rr*GRID_SIZE + cc)

        # build/load trie
        h = board_hash([
            self.B[i:i+GRID_SIZE]
            for i in range(0, GRID_SIZE**2, GRID_SIZE)
        ])
        trie_file = os.path.join(TRIE_CACHE_DIR, f"{h}.trie.pkl")
        if os.path.exists(trie_file):
            self.trie_root = pickle.load(open(trie_file, 'rb'))
        else:
            self.trie_root = BoggleSolver.build_trie(words)
            pickle.dump(self.trie_root, open(trie_file, 'wb'))

    @staticmethod
    def build_trie(words: List[str]) -> TrieNode:
        root = TrieNode()
        for w in words:
            node = root
            for ch in w:
                node = node.children.setdefault(ch, TrieNode())
            node.word = w
        return root

    def find_all_words(self) -> Dict[str, Tuple[int, List[Tuple[int,int]]]]:
        # prepare args
        args = [
            (i, self.B, self.M, self.neighbors, self.trie_root)
            for i in range(GRID_SIZE**2)
        ]

        # sequential DFS so KeyboardInterrupt is handled
        results = list(map(_dfs_worker, args))

        combined: Dict[str, Tuple[int, List[int]]] = {}
        for part in results:
            combined.update(part)

        # convert to (row,col)
        return {
            w: (pts, [(i//GRID_SIZE, i%GRID_SIZE) for i in path])
            for w, (pts, path) in combined.items()
        }

def generate_random_board(dice: List[str]) -> List[List[str]]:
    import random
    sel = [random.choice(d) for d in random.sample(dice, len(dice))]
    return [sel[i:i+GRID_SIZE] for i in range(0, GRID_SIZE**2, GRID_SIZE)]

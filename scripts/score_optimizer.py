from typing import List, Tuple

LETTER_SCORES = {
    **dict.fromkeys("EAIONRTLSU", 1),
    **dict.fromkeys("DG", 2),
    **dict.fromkeys("BCMP", 3),
    **dict.fromkeys("FHVWY", 4),
    "K": 5,
    **dict.fromkeys("JX", 8),
    **dict.fromkeys("QZ", 10)
}

def word_score(word: str) -> int:
    base = sum(LETTER_SCORES.get(ch, 0) for ch in word.upper())
    length_bonus = 1 if len(word) == 3 else max(1, len(word) - 2)
    return base * length_bonus

def optimize_word_order(paths: List[Tuple[str, List[Tuple[int, int]]]]) -> List[Tuple[str, List[Tuple[int, int]]]]:
    used = set()
    best_order = []
    covered_tiles = set()
    remaining = sorted(paths, key=lambda x: -word_score(x[0]))

    while remaining:
        best_word = None
        best_gain = -1

        for word, path in remaining:
            path_set = set(path)
            new_tiles = path_set - covered_tiles
            bonus = len(new_tiles) * 2  # reward for using more new tiles
            gain = word_score(word) + bonus
            if gain > best_gain:
                best_gain = gain
                best_word = (word, path)

        if best_word:
            best_order.append(best_word)
            covered_tiles.update(best_word[1])
            remaining.remove(best_word)

    all_tiles = {(r, c) for r in range(4) for c in range(4)}
    if covered_tiles == all_tiles:
        print("\n🎉 All tiles covered — +100 point bonus!")

    return best_order

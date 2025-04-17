# score_optimizer.py

from typing import List, Tuple, Set, Dict
import itertools

# ---- Letter scores akin to Scrabble ----
LETTER_SCORES: Dict[str, int] = {
    **dict.fromkeys("EAIONRTLSU", 1),
    **dict.fromkeys("DG", 2),
    **dict.fromkeys("BCMP", 3),
    **dict.fromkeys("FHVWY", 4),
    "K": 5,
    **dict.fromkeys("JX", 8),
    **dict.fromkeys("QZ", 10)
}

def word_score(word: str) -> int:
    """
    Compute the base score of a word, with a length bonus:
      - 3 letters = ×1
      - 4+ letters = ×(length−2)
    """
    base = sum(LETTER_SCORES.get(ch, 0) for ch in word.upper())
    length_bonus = 1 if len(word) == 3 else max(1, len(word) - 2)
    return base * length_bonus

def optimize_word_order(
    paths: List[Tuple[str, List[Tuple[int, int]]]]
) -> List[Tuple[str, List[Tuple[int, int]]]]:
    """
    Greedily order words by (score + coverage bonus) to maximize points and new tiles.
    """
    used: Set[str] = set()
    best_order: List[Tuple[str, List[Tuple[int, int]]]] = []
    covered_tiles: Set[Tuple[int, int]] = set()
    remaining = sorted(paths, key=lambda x: -word_score(x[0]))

    while remaining:
        best_word = None
        best_gain = -1
        for word, path in remaining:
            new_tiles = set(path) - covered_tiles
            bonus = len(new_tiles) * 2  # reward for covering new tiles
            gain = word_score(word) + bonus
            if gain > best_gain:
                best_gain = gain
                best_word = (word, path)
        if not best_word:
            break
        best_order.append(best_word)
        covered_tiles |= set(best_word[1])
        remaining.remove(best_word)

    all_tiles = {(r, c) for r in range(4) for c in range(4)}
    if covered_tiles == all_tiles:
        print("\n🎉 All tiles covered — +100 point bonus!")

    return best_order

def ensure_tile_coverage(
    paths: List[Tuple[str, List[Tuple[int, int]]]],
    grid_size: int = 4,
    max_words: int = 10
) -> Tuple[
    List[Tuple[str, List[Tuple[int, int]]]],
    List[Tuple[str, List[Tuple[int, int]]]]
]:
    """
    Phase 1: select up to max_words that maximize new‐tile coverage.
    Returns (coverage_list, remaining_list).
    """
    all_tiles = {(r, c) for r in range(grid_size) for c in range(grid_size)}
    covered: Set[Tuple[int, int]] = set()
    coverage: List[Tuple[str, List[Tuple[int, int]]]] = []
    remaining = paths.copy()

    for _ in range(max_words):
        if covered == all_tiles:
            break
        best = None
        best_new = -1
        for word, path in remaining:
            new_tiles = set(path) - covered
            if len(new_tiles) > best_new:
                best, best_new = (word, path), len(new_tiles)
        if not best or best_new == 0:
            break
        coverage.append(best)
        covered |= set(best[1])
        remaining.remove(best)

    return coverage, remaining

def ensure_efficient_coverage(
    paths: List[Tuple[str, List[Tuple[int, int]]]],
    grid_size: int = 4,
    max_words: int = 10,
    time_per_tile: float = 0.15,
    overhead_per_word: float = 0.5,
    lambda_eff: float = 1.0,
    lambda_cov: float = 2.0
) -> Tuple[
    List[Tuple[str, List[Tuple[int, int]]]],
    List[Tuple[str, List[Tuple[int, int]]]]
]:
    """
    Phase 1: Greedily pick up to max_words maximizing:
      lambda_eff * (points / est_time) + lambda_cov * new_tile_count
    Returns (selected, remaining).
    """
    all_tiles = {(r, c) for r in range(grid_size) for c in range(grid_size)}
    covered: Set[Tuple[int, int]] = set()
    selected: List[Tuple[str, List[Tuple[int, int]]]] = []
    remaining = paths.copy()

    for _ in range(max_words):
        if covered == all_tiles:
            break
        best_score = -float("inf")
        best_word = None
        for word, path in remaining:
            new_tiles = set(path) - covered
            if not new_tiles:
                continue
            pts = word_score(word)
            est_time = overhead_per_word + len(path) * time_per_tile
            eff = pts / est_time
            cov = len(new_tiles)
            score = lambda_eff * eff + lambda_cov * cov
            if score > best_score:
                best_score = score
                best_word = (word, path)
        if not best_word:
            break
        selected.append(best_word)
        covered |= set(best_word[1])
        remaining.remove(best_word)

    return selected, remaining

def tune_coverage_params(
    paths: List[Tuple[str, List[Tuple[int, int]]]],
    grid_size: int = 4,
    max_words: int = 10,
    time_per_tile_choices=(0.1, 0.15, 0.2),
    overhead_choices=(0.2, 0.5, 0.8),
    lambda_eff_choices=(0.5, 1.0, 2.0),
    lambda_cov_choices=(1.0, 2.0, 3.0),
) -> dict:
    """
    Grid‑search over parameter choices to maximize total points.
    Returns the best parameter set (and its total score).
    """
    # Pre‑sort by score to feed into coverage
    scored = optimize_word_order(paths)
    best_params = {"score": -1}

    for tpt, overhead, le, lc in itertools.product(
        time_per_tile_choices,
        overhead_choices,
        lambda_eff_choices,
        lambda_cov_choices,
    ):
        cov, rest = ensure_efficient_coverage(
            scored,
            grid_size=grid_size,
            max_words=max_words,
            time_per_tile=tpt,
            overhead_per_word=overhead,
            lambda_eff=le,
            lambda_cov=lc,
        )
        final = cov + rest
        total_pts = sum(word_score(w) for w, _ in final)
        if total_pts > best_params["score"]:
            best_params = {
                "score": total_pts,
                "time_per_tile": tpt,
                "overhead_per_word": overhead,
                "lambda_eff": le,
                "lambda_cov": lc,
            }

    print(f"\n🔧 Best tuning → {best_params}")
    return best_params

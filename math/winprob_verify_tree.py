"""End-to-end check of a saved winprob tree.

Loads a len{L}_uniform_n{N}.json strategy tree and *plays it* against every
word of that length: walk from the root, at each node read the guessed letter,
compute that letter's revealed template for the true word, follow the matching
branch (counting a miss when the letter is absent), and stop at a leaf. Then
confirm the tree's realized numbers match what the solver reported and saved:
  - every won word used <= n misses,
  - fraction of words won        == file's p_win,
  - mean misses over won words   == file's e_misses.

This validates the artifact itself (not just the DP): the saved tree really does
realize the claimed win-probability and conditional miss average.

usage:  python math/winprob_verify_tree.py math/data/shared/winprob/len14_uniform_n02.json
        python math/winprob_verify_tree.py            # checks every saved tree
"""
import glob
import json
import sys

sys.path.insert(0, "math")
from strategy import GreedyGame, ALPHABET


def template(word, letter):
    """Revealed pattern of `letter` in `word`: e.g. play 'e' on 'been' -> '_ee_'."""
    return "".join(letter if ch == letter else "_" for ch in word)


def play(tree, word, n):
    """Walk `word` down `tree`. Returns (won: bool, misses: int)."""
    node = tree
    misses = 0
    while True:
        if "word" in node:                       # resolved to a single candidate
            return node["word"] == word, misses
        if "lost" in node:                       # truncated group -> a loss
            return False, misses
        letter = node["guess"]
        if letter not in word:                   # absent -> a wrong guess
            misses += 1
        node = node["branches"][template(word, letter)]


def verify(path):
    data = json.loads(open(path).read())
    L, n = data["length"], data["n"]
    words = GreedyGame(length=L).words
    tree = data["tree"]

    # weight words the same way the run did (uniform, or zipf frequency)
    if data.get("weighting", "uniform") == "uniform":
        wt = {w: 1.0 for w in words}
    else:
        import wordlist
        wt = wordlist.freq_weights(min_len=L, max_len=L)
    total_w = sum(wt.get(w, 1.0) for w in words)

    won_w = 0.0
    miss_w = 0.0
    over_budget = []                             # won words that somehow exceeded n
    unreached = []                               # words with no path in the tree (bug)
    for w in words:
        try:
            w_won, m = play(tree, w, n)
        except KeyError:
            unreached.append(w)
            continue
        if w_won:
            g = wt.get(w, 1.0)
            won_w += g
            miss_w += g * m
            if m > n:
                over_budget.append((w, m))

    p_win = won_w / total_w if total_w else 0.0
    e_miss = miss_w / won_w if won_w else 0.0
    dp = abs(p_win - (data["p_win"] or 0.0))
    de = abs(e_miss - (data["e_misses"] or 0.0))
    ok = (dp < 1e-9 and de < 1e-9 and not over_budget and not unreached)

    print(f"{path.split('/')[-1]}: len{L} n={n}  "
          f"P(win) {p_win:.4f} (file {data['p_win']:.4f}, d={dp:.1e})  "
          f"E[miss|won] {e_miss:.4f} (file {data['e_misses']:.4f}, d={de:.1e})  "
          f"-> {'OK' if ok else 'FAIL'}")
    if over_budget:
        print(f"    !! {len(over_budget)} won words exceeded n={n} misses: {over_budget[:5]}")
    if unreached:
        print(f"    !! {len(unreached)} words had no path in the tree: {unreached[:5]}")
    return ok


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("math/data/shared/winprob/*.json"))
    if not paths:
        print("no saved trees found in math/data/shared/winprob/")
        sys.exit(1)
    ok = all(verify(p) for p in paths)
    print("\nALL TREES OK" if ok else "\nSOME TREES FAILED")
    sys.exit(0 if ok else 1)

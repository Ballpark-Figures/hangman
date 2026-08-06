"""Neutrality check: does dropping zero-frequency words change the numbers?

Under the adversarial weightings (``best_opener``/``greedy``/``*_word``) most
words weigh exactly 0 -- they can never be the secret. They inflate the candidate
set (and the solvers' state space) but should NOT affect any headline number,
because a 0-weight word is invisible to every guess choice and separating a real
word from it is always free (the real word's letter at any differing position
distinguishes them at no cost).

This script verifies that claim empirically for the GREEDY strategy: it compares
the per-word miss count of every positive-weight word computed over the FULL
candidate set vs. over the set with all 0-weight words removed. They must match
exactly. Run:

    python math/zero_freq_check.py [length ...] [--weighting best_opener greedy ...]
"""

from __future__ import annotations

import sys

import numpy as np

import wordlist
from strategy import GreedyGame


def _reduced(length: int, weighting: str):
    """(full game, full freq, positive-only game, positive-only freq)."""
    g_full = GreedyGame(length)
    f = g_full._coerce_freq(wordlist.resolve_weighting(weighting, length))
    pos = np.where(f > 0)[0]
    g_red = GreedyGame(length, words=[g_full.words[i] for i in pos])
    return g_full, f, g_red, f[pos]


def check_optimal(length: int, weighting: str, cap: int) -> dict:
    """Compare optimal capped_avg at a fixed cap, full set vs. zeros-removed.
    capped_avg is frequency-weighted, so it should be identical."""
    from optimal import OptimalSolver
    g_full, f, g_red, pos_freq = _reduced(length, weighting)
    avg_full = OptimalSolver(g_full).solve(f, max_misses=cap, verbose=False)
    avg_red = OptimalSolver(g_red).solve(pos_freq, max_misses=cap, verbose=False)
    return {"length": length, "weighting": weighting, "cap": cap,
            "N_full": g_full.N, "N_pos": g_red.N,
            "avg_full": avg_full, "avg_red": avg_red,
            "avg_diff": abs(avg_full - avg_red)}


def _pattern_str(c: int, mask: int, length: int) -> str:
    from strategy import ALPHABET
    return "".join(ALPHABET[c] if (mask >> p) & 1 else "_" for p in range(length))


def _replay(tree: dict, i: int, masks, length: int):
    """Walk `tree` for word index `i`; return (misses, capped). Raises KeyError if
    the tree has no branch for a pattern the word produces (= tree incomplete)."""
    node, misses = tree, 0
    while "branches" in node:
        c = ord(node["guess"]) - 97
        mask = int(masks[i, c])
        if mask == 0:
            misses += 1
        node = node["branches"][_pattern_str(c, mask, length)]   # KeyError => incomplete
    return misses, ("capped" in node)


def check_optimal_tree(length: int, weighting: str, cap: int) -> dict:
    """Build the optimal tree over positive words + greedy-completed zeros, then
    replay EVERY word (incl. zero-freq) through it: verifies (a) completeness -- no
    word falls off -- and (b) that the solver's reported capped_avg is unchanged
    (the neutrality invariant; the tree-vs-DP gap for partial caps is the
    pre-existing reconstruction gap in optimal_discrepancy_report.md)."""
    from optimal import OptimalSolver
    g, f, _, _ = _reduced(length, weighting)
    solver = OptimalSolver(g)
    avg = solver.solve(f, max_misses=cap, verbose=False)
    tree = solver.optimal_tree()

    fell_off, capped = 0, 0
    misses = np.zeros(g.N)
    for i in range(g.N):
        try:
            m, cap_hit = _replay(tree, i, g.masks, length)
        except KeyError:
            fell_off += 1
            continue
        misses[i] = m
        capped += int(cap_hit)
    denom = float(f.sum())
    tree_avg = float(f @ misses / denom) if denom else 0.0   # zeros weigh 0
    return {"length": length, "weighting": weighting, "cap": cap,
            "N": g.N, "fell_off": fell_off, "capped_leaves": capped,
            "solver_avg": avg, "tree_avg": tree_avg}


def _play_wp(tree: dict, i: int, masks, length: int):
    """Walk a winprob tree for word i; return (won, misses). Raises KeyError if the
    word has no path (tree incomplete)."""
    from strategy import ALPHABET
    node, misses, word_i = tree, 0, i
    while True:
        if "word" in node:
            return (node["word"] == _WORDS[length][word_i]), misses
        if "lost" in node:
            return False, misses
        c = ord(node["guess"]) - 97
        mask = int(masks[i, c])
        if mask == 0:
            misses += 1
        node = node["branches"][_pattern_str(c, mask, length)]


_WORDS: dict = {}


def check_winprob(length: int, weighting: str, n: int) -> dict:
    """p_win over possible-secret words + full-tree replay: verifies completeness
    (no word falls off), no over-budget 'win', and that p_win matches the committed
    JSON (if present). Zero-freq words carry no mass, so p_win is unchanged."""
    import json
    from pathlib import Path
    from winprob import WinProbSolver
    from tree_complete import complete_tree
    g, f, _, _ = _reduced(length, weighting)
    _WORDS[length] = g.words
    wp = WinProbSolver(length, freq=f, weighting=weighting, game=g)
    wp._verbose = False
    letter, w, m = wp.best_opener(n)
    p_win = w / wp.total if wp.total else 0.0
    tree = complete_tree(wp.build_tree(np.arange(g.N, dtype=wp._idt), n, n))

    unreached, over, won_w = 0, 0, 0.0
    for i in range(g.N):
        try:
            won_i, miss_i = _play_wp(tree, i, g.masks, length)
        except KeyError:
            unreached += 1
            continue
        if won_i:
            won_w += float(f[i])
            over += int(miss_i > n)
    total_w = float(f.sum())
    replay_p = won_w / total_w if total_w else 0.0

    committed = None
    cf = Path(f"data/shared/winprob/len{length:02d}_{weighting}_n{n:02d}.json")
    if cf.exists():
        committed = json.loads(cf.read_text()).get("p_win")
    return {"length": length, "weighting": weighting, "n": n, "N": g.N,
            "p_win": p_win, "replay_p": replay_p, "unreached": unreached,
            "over_budget": over, "committed_p": committed}


def check(length: int, weighting: str) -> dict:
    """Compare greedy per-word misses (positive words) full vs. zeros-removed."""
    g_full = GreedyGame(length)
    f = g_full._coerce_freq(wordlist.resolve_weighting(weighting, length))
    pos = np.where(f > 0)[0]
    pos_words = [g_full.words[i] for i in pos]
    pos_freq = f[pos]

    misses_full = g_full.per_word_misses(f)[pos]        # positive words, full set
    g_red = GreedyGame(length, words=pos_words)
    misses_red = g_red.per_word_misses(pos_freq)        # same words, zeros dropped

    max_diff = float(np.max(np.abs(misses_full - misses_red))) if pos.size else 0.0
    denom = float(pos_freq.sum())
    avg_full = float(pos_freq @ misses_full / denom) if denom else 0.0
    avg_red = float(pos_freq @ misses_red / denom) if denom else 0.0
    return {
        "length": length, "weighting": weighting,
        "N_full": g_full.N, "N_pos": int(pos.size), "N_zero": g_full.N - int(pos.size),
        "max_perword_diff": max_diff,
        "avg_full": avg_full, "avg_red": avg_red, "avg_diff": abs(avg_full - avg_red),
    }


def main(argv):
    if argv and argv[0] == "optimal":
        # optimal <length> <cap> [weighting ...]
        length, cap = int(argv[1]), int(argv[2])
        weightings = argv[3:] or ["best_opener"]
        ok = True
        for w in weightings:
            r = check_optimal(length, w, cap)
            print(f"len {r['length']} cap {r['cap']} {r['weighting']:<16} "
                  f"N {r['N_full']}->{r['N_pos']}  avg_full={r['avg_full']:.6f}  "
                  f"avg_red={r['avg_red']:.6f}  diff={r['avg_diff']:.2e}")
            ok = ok and r["avg_diff"] == 0.0
        print("\nNEUTRAL" if ok else "\n!! NON-NEUTRAL")
        return 0 if ok else 1

    if argv and argv[0] == "winprob":
        # winprob <length> <n> [weighting ...]
        length, n = int(argv[1]), int(argv[2])
        weightings = argv[3:] or ["best_opener"]
        ok = True
        for w in weightings:
            r = check_winprob(length, w, n)
            cp = f"{r['committed_p']:.6f}" if r["committed_p"] is not None else "n/a"
            cdiff = (abs(r["p_win"] - r["committed_p"]) if r["committed_p"] is not None else 0.0)
            print(f"len {r['length']} n {r['n']} {r['weighting']:<16} N {r['N']}  "
                  f"p_win={r['p_win']:.6f}  replay_p={r['replay_p']:.6f}  "
                  f"committed={cp} (d={cdiff:.1e})  unreached={r['unreached']}  "
                  f"over_budget={r['over_budget']}")
            ok = ok and r["unreached"] == 0 and r["over_budget"] == 0 \
                and abs(r["p_win"] - r["replay_p"]) < 1e-9 and cdiff < 1e-9
        print("\nCOMPLETE + NEUTRAL" if ok else "\n!! PROBLEM")
        return 0 if ok else 1

    if argv and argv[0] == "tree":
        # tree <length> <cap> [weighting ...] -- completeness + solver-avg vs committed CSV
        length, cap = int(argv[1]), int(argv[2])
        weightings = argv[3:] or ["best_opener"]
        ok = True
        for w in weightings:
            r = check_optimal_tree(length, w, cap)
            print(f"len {r['length']} cap {r['cap']} {r['weighting']:<16} N {r['N']}  "
                  f"fell_off={r['fell_off']}  capped_leaves={r['capped_leaves']}  "
                  f"solver_avg={r['solver_avg']:.6f}  tree_replay={r['tree_avg']:.6f}")
            ok = ok and r["fell_off"] == 0
        print("\nCOMPLETE (every word replays)" if ok else "\n!! INCOMPLETE: a word fell off")
        return 0 if ok else 1

    lengths, weightings = [], []
    it = iter(argv)
    for a in it:
        if a == "--weighting":
            weightings = list(it)
            break
        lengths.append(int(a))
    if not lengths:
        lengths = [5, 6]
    if not weightings:
        weightings = ["best_opener", "greedy"]

    print(f"{'len':>3} {'weighting':<16} {'N_full':>7} {'N_pos':>6} {'N_zero':>7} "
          f"{'max_pw_diff':>12} {'avg_full':>10} {'avg_red':>10} {'avg_diff':>10}")
    ok = True
    for L in lengths:
        for w in weightings:
            try:
                r = check(L, w)
            except Exception as e:
                print(f"{L:>3} {w:<16} -- skipped: {type(e).__name__}: {e}")
                continue
            print(f"{r['length']:>3} {r['weighting']:<16} {r['N_full']:>7} "
                  f"{r['N_pos']:>6} {r['N_zero']:>7} {r['max_perword_diff']:>12.2e} "
                  f"{r['avg_full']:>10.5f} {r['avg_red']:>10.5f} {r['avg_diff']:>10.2e}")
            ok = ok and r["max_perword_diff"] == 0.0 and r["avg_diff"] == 0.0
    print("\nNEUTRAL (all diffs exactly 0)" if ok else "\n!! NON-NEUTRAL: a diff was nonzero")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

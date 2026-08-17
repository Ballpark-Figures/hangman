"""Tier-backbone analysis: how far do the TOP + HIGH tier letters get you?

Scene 11's premise: you open EVERY game by guessing the eight top-3-tier letters
(the "backbone") -- A E I N O R S T -- regardless of hits and misses, and only
THEN start thinking. This module measures, over the whole curated word list
(unweighted, ``zipf >= 2.5`` = 34,483 words), how words break down AFTER that
fixed opening:

  - only_tier      the word uses ONLY backbone letters, so the opening reveals it
                   outright (beat b).
  - single_option  the word has non-backbone letters, but its backbone pattern
                   (which of the eight appear, at which positions, given the known
                   LENGTH) is unique in the list -- you already know the word, 0
                   further misses (beat c).
  - miss_dist[k]   the number of words that, continuing with the OPTIMAL strategy
                   after the backbone opening, take exactly ``k`` ADDITIONAL misses
                   (misses during the backbone opening itself are NOT counted).
                   only_tier and single_option are both inside miss_dist[0].

Method (as close to ``optimal.py`` as possible -- it REUSES that solver). Guessing
all eight backbone letters, in any order, partitions each length's words into
groups sharing an identical backbone signature (the eight per-letter position
masks). Words in the same group are indistinguishable after the opening, so the
optimal continuation is solved INDEPENDENTLY per group. Within a group the eight
backbone letters no longer split anything (every word shares their masks), so
``OptimalSolver``'s own recursion never guesses them again -- it only spends
guesses (and counts misses) on the remaining 18 letters. That means:

    additional misses for a word  =  optimal misses to resolve its group

with uniform weights -- exactly ``optimal.py``'s objective (minimise the average /
total misses) restricted to that group. We call the identical ``_V`` recursion for
the exact VALUES, then walk once per word to read off its miss count.

WHY WE RE-DERIVE THE MOVE (not ``_move``/``best_letter``). ``optimal.py``'s DP
*value* is exact, but its serialized *tree* policy is known to be slightly
suboptimal (~0.3-1%; see ``optimal_discrepancy_report.md``): walking ``_move``'s
stored ``best_letter`` at every node realises a tree whose per-word misses do NOT
sum back to the exact optimum. Since we need a per-word DISTRIBUTION, we instead
pick each node's move by the VALUE-CONSISTENT rule -- the letter minimising
``W_absent(c) + sum of exact child V*`` (child values via the same ``_V``). That
is the correct move reconstruction: the chosen letter's cost EQUALS ``V*(S)`` by
definition, so following it (and recursing the same way) yields a single optimal
tree whose per-word misses provably sum to the optimum.

CAVEAT on the DISTRIBUTION. Minimising the average (= total, since uniform) misses
pins the AVERAGE additional misses exactly, but NOT the per-word split across
0/1/2/... : two optimal trees with the same total can move a miss from one word to
another (e.g. {0,2} vs {1,1}). The buckets below are the split produced by the
solver's deterministic optimal tree (greedy-first tie-breaking, as in optimal.py).
The average is canonical; the exact bucket sizes are one optimal realisation.

Run ``python math/tier_backbone.py [max_len] [--verify] [--no-cache]``:
prints an ``optimal.py``-style per-length progress log (greedy reference avg,
60 s heartbeats, a completion line each length), then the totals and each
headline number's provenance, and writes the committed scene cache
``animations/assets/scene11_cache.json``. ``--verify`` cross-checks each SMALL
group's optimal miss-SUM against an independent unpruned brute force
(``optimal.optimal_bruteforce``; groups above ``VERIFY_MAX`` words are skipped
because the unpruned reference is exponential) -- the exactness gate.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

from strategy import GreedyGame, ALPHABET
from optimal import OptimalSolver, optimal_bruteforce, INF
from wordlist import DEFAULT_ZIPF

# The TOP + HIGH tiers (scenes 07 / 09 / 10) = tier-list rows 0-2 = "EIA","SR","TNO".
# Hand-kept in sync with animations/assets/tier_list.py TIER_LETTERS[:3].
TIER_LETTERS = "aeinorst"                       # A E I N O R S T
TIER_COLS = [ord(c) - 97 for c in TIER_LETTERS]
TIER_SET = set(TIER_LETTERS)

# The full analysis set is every length with a curated word at the default cutoff.
LENGTHS = list(range(1, 21))                     # 1..20 (see the length histogram)
EXPECTED_TOTAL = 34483                            # zipf >= 2.5 guard
VERIFY_MAX = 12                                   # brute force is exponential -> only tiny groups
HEARTBEAT = 60.0                                  # seconds between progress lines (as in optimal.py)

# committed scene cache: math/ -> ../animations/assets/scene11_cache.json
CACHE_PATH = (Path(__file__).resolve().parent.parent
              / "animations" / "assets" / "scene11_cache.json")


def _emit(msg: str) -> None:
    print(msg, flush=True)


def _prime(solver: OptimalSolver) -> None:
    """Prime an ``OptimalSolver`` so its ``_V``/``_move`` run uncapped with uniform
    weights on ARBITRARY subsets, WITHOUT the full-length root solve. Sets exactly
    the state ``solve()`` would set, minus actually calling ``_solve_root``."""
    g = solver.game
    solver.freq = g._coerce_freq(None)           # uniform (all ones) -> minimise TOTAL misses
    solver.memo, solver.lb = {}, {}
    solver._ubbuf = np.zeros(solver.N, dtype=np.float64)
    solver._verbose = False
    solver._heartbeat = INF
    solver._ub_depth = 8
    solver._opener_ub_depth = 2
    solver._total = float(solver.freq.sum())
    solver._pos = solver._positive_root()
    solver._cap = None
    solver._solve_cap = None
    solver._reset_progress()
    solver._calls = 0
    solver._t0 = solver._last_beat = time.perf_counter()


def _groups(game: GreedyGame):
    """Partition this length's word indices by identical backbone signature (the
    eight tier-letter position masks). Returns index arrays, LARGEST group first
    (so the expensive solves surface early in the progress log)."""
    if game.N == 0:
        return []
    sig = np.ascontiguousarray(game.masks[:, TIER_COLS])     # (N, 8) uint32
    _, inv = np.unique(sig, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    order = np.argsort(inv, kind="stable")
    inv_sorted = inv[order]
    cuts = np.nonzero(np.diff(inv_sorted))[0] + 1
    grps = [order[a:b] for a, b in zip([0, *cuts], [*cuts, len(order)])]
    grps.sort(key=len, reverse=True)
    return grps


def _opt_value(solver: OptimalSolver, S: np.ndarray) -> float:
    """Exact uncapped optimal V(S) via ``optimal.py``'s own ``_V`` (its fast B&B),
    mirroring its base cases (|S|<=1 -> 0, |S|==2 -> ``_sep_two``)."""
    n = int(S.shape[0])
    if n <= 1:
        return 0.0
    if n == 2:
        return float(solver._sep_two(int(S[0]), int(S[1]))[0])
    return solver._V(S, None, INF, 99)


def _opt_move(solver: OptimalSolver, S: np.ndarray, cache: dict) -> int:
    """Value-consistent optimal first letter for ``S``: the splitting letter c
    minimising ``W_absent(c) + sum of exact child V*`` (uniform -> W_absent = number
    of words absent for c). Its cost equals V*(S) by definition, so following it
    reconstructs a single faithful optimal tree (unlike ``_move``'s best_letter --
    see the module docstring). Deterministic (first argmin), so every word in the
    group walks the SAME tree. Memoised per state in ``cache``."""
    key = S.tobytes()
    hit = cache.get(key)
    if hit is not None:
        return hit
    MS = solver.masks[S]
    splits = MS.min(0) != MS.max(0)
    best_c, best_cost = -1, INF
    for c in range(26):
        if not splits[c]:
            continue
        pats = MS[:, c]
        cost = 0.0
        for pv in np.unique(pats):
            grp = S[pats == pv]
            if pv == 0:
                cost += int(grp.shape[0])        # uniform: one miss per absent word
            cost += _opt_value(solver, grp)
            if cost >= best_cost:
                break
        if cost < best_cost:
            best_cost, best_c = cost, c
    cache[key] = best_c
    return best_c


def _walk_misses(solver: OptimalSolver, root: np.ndarray, i: int, cache: dict) -> int:
    """ADDITIONAL misses for word ``i`` resolving its group ``root`` under the
    value-consistent optimal tree -- follow word ``i``'s branch at each node,
    counting only misses (an absent letter). Uncapped throughout."""
    S = root
    misses = 0
    while S.shape[0] > 1:
        c = _opt_move(solver, S, cache)
        if c < 0:
            break
        if solver.masks[i, c] == 0:              # letter absent -> a miss
            misses += 1
        S = S[solver.masks[S, c] == solver.masks[i, c]]
    return misses


def _only_tier(word: str) -> bool:
    return all(ch in TIER_SET for ch in word)


def analyse_length(length: int, *, verify: bool = False, verbose: bool = True):
    """Backbone breakdown for one word length. Returns
    ``(only_tier, single_option, Counter{misses: count}, N, total_misses)``."""
    game = GreedyGame(length)
    N = game.N
    if N == 0:
        return 0, 0, Counter(), 0, 0
    solver = OptimalSolver(game)
    _prime(solver)
    idt = solver._idt
    grps = _groups(game)
    G = len(grps)
    if verbose:
        greedy_avg = game.average_misses()       # reference (full greedy, no backbone) -- as optimal.py
        biggest = len(grps[0]) if grps else 0
        _emit(f"length {length}: {N:,} words  (greedy avg {greedy_avg:.4f}); "
              f"backbone opening {''.join(sorted(TIER_SET)).upper()} -> {G:,} groups "
              f"(biggest |S|={biggest})")

    only_tier = single_option = 0
    dist: Counter = Counter()
    total_misses = 0
    t0 = last_beat = time.perf_counter()
    words_done = 0
    move_cache: dict = {}
    for gi, grp in enumerate(grps):
        grp = grp.astype(idt)
        if grp.shape[0] == 1:
            i = int(grp[0])
            dist[0] += 1
            if _only_tier(game.words[i]):
                only_tier += 1                    # beat b: revealed by the opening
            else:
                single_option += 1                # beat c: uniquely pinned, 0 misses
        else:
            val = _opt_value(solver, grp)         # exact optimal TOTAL additional misses
            per = [_walk_misses(solver, grp, int(i), move_cache) for i in grp]
            assert sum(per) == round(val), (      # faithful tree walk must match V*
                f"len {length}: group sum {sum(per)} != V {val}")
            if verify and grp.shape[0] <= VERIFY_MAX:
                syn = GreedyGame(length, words=[game.words[int(i)] for i in grp])
                bf = optimal_bruteforce(syn, None) * syn.N   # independent min total misses
                assert abs(bf - val) < 1e-6, (
                    f"len {length}: brute force {bf} != solver {val} on a group")
            dist.update(per)
            total_misses += int(round(val))
        words_done += grp.shape[0]

        now = time.perf_counter()
        if verbose and now - last_beat >= HEARTBEAT:
            last_beat = now
            _emit(f"  len {length} | group {gi + 1:,}/{G:,} | "
                  f"words {words_done:,}/{N:,} ({100.0 * words_done / N:.0f}%) | "
                  f"|S|={grp.shape[0]} | {len(solver.memo):,} states, {now - t0:.0f}s")

    if verbose:
        avg_add = total_misses / N if N else 0.0
        _emit(f"length {length}: DONE  backbone-optimal additional avg = {avg_add:.4f} "
              f"(over {N:,} words); {G:,} groups, {len(solver.memo):,} states, "
              f"{time.perf_counter() - t0:.1f}s")
    return only_tier, single_option, dist, N, total_misses


def compute(max_len: int | None = None, *, verify: bool = False, verbose: bool = True):
    """Aggregate the backbone breakdown over every length. Returns a result dict
    (see the module docstring for the fields)."""
    lengths = [L for L in LENGTHS if max_len is None or L <= max_len]
    only_tier = single_option = 0
    dist: Counter = Counter()
    total = 0
    total_misses = 0
    for L in lengths:
        ot, so, d, N, tm = analyse_length(L, verify=verify, verbose=verbose)
        only_tier += ot
        single_option += so
        dist.update(d)
        total += N
        total_misses += tm

    if max_len is None:
        assert total == EXPECTED_TOTAL, f"total {total} != expected {EXPECTED_TOTAL}"
    max_misses = max(dist) if dist else 0
    return {
        "letters": "".join(sorted(TIER_LETTERS)).upper(),
        "weighting": "unweighted",
        "min_zipf": DEFAULT_ZIPF,
        "total_words": total,
        "only_tier": only_tier,               # beat b
        "single_option": single_option,       # beat c
        # beat d: the additional-miss distribution over ALL words (0 includes b + c)
        "miss_dist": {int(k): int(dist[k]) for k in range(max_misses + 1)},
        "rest_zero_miss": int(dist[0]) - only_tier - single_option,  # 0-miss beyond b + c
        "max_misses": int(max_misses),
        "avg_additional_misses": total_misses / total if total else 0.0,
    }


def _pct(n, d):
    return 100.0 * n / d if d else 0.0


def main(argv):
    max_len = None
    verify = "--verify" in argv
    write_cache = "--no-cache" not in argv
    for a in argv:
        if not a.startswith("-"):
            max_len = int(a)
    _emit(f"tier-backbone analysis  |  backbone letters = {''.join(sorted(TIER_SET)).upper()}"
          f"  |  unweighted, zipf >= {DEFAULT_ZIPF}"
          + (f"  |  lengths <= {max_len} (partial)" if max_len else "")
          + ("  |  VERIFYING vs brute force" if verify else ""))
    t0 = time.perf_counter()
    res = compute(max_len, verify=verify)
    T = res["total_words"]
    md = res["miss_dist"]

    _emit(f"\n===== totals over {T:,} words =====")
    _emit(f"  only_tier      (beat b): {res['only_tier']:6d}  ({_pct(res['only_tier'], T):5.2f}%)")
    _emit(f"  single_option  (beat c): {res['single_option']:6d}  ({_pct(res['single_option'], T):5.2f}%)")
    _emit(f"  rest 0-miss    (beat d): {res['rest_zero_miss']:6d}  ({_pct(res['rest_zero_miss'], T):5.2f}%)")
    _emit(f"  -- 0 additional misses total: {md[0]:6d}  ({_pct(md[0], T):5.2f}%)")
    for k in range(1, res["max_misses"] + 1):
        _emit(f"  {k} additional miss{'es' if k != 1 else ' '}      : {md[k]:6d}  ({_pct(md[k], T):5.2f}%)")
    _emit(f"  avg additional misses (canonical): {res['avg_additional_misses']:.4f}")

    _emit("\n===== provenance =====")
    _emit(f"  wordlist        : math/data/wordlist_master.txt @ zipf >= {DEFAULT_ZIPF} "
          f"(via wordlist.load / GreedyGame), {T:,} words -- unweighted")
    _emit(f"  backbone letters: TIER_LETTERS[:3] of animations/assets/tier_list.py "
          f"= {''.join(sorted(TIER_SET)).upper()}")
    _emit(f"  only_tier       : word's letter-set subset of the 8 backbone letters")
    _emit(f"  single_option   : not only_tier, but unique backbone signature at its length")
    _emit(f"  miss_dist       : optimal.OptimalSolver (uniform, uncapped) per residual group; "
          f"per-word misses by walking the optimal tree")

    if write_cache and max_len is None:
        CACHE_PATH.write_text(json.dumps(res, indent=2))
        _emit(f"\n  wrote cache -> {CACHE_PATH}")
    elif write_cache:
        _emit(f"\n  (partial run: cache NOT written -- rerun without a max_len to write "
              f"{CACHE_PATH.name})")
    _emit(f"  computed in {time.perf_counter() - t0:.1f}s"
          + ("  [brute-force gate PASSED]" if verify else ""))
    return res


if __name__ == "__main__":
    main(sys.argv[1:])

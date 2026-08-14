"""Cached data for scene 23 (fair_game) — SOURCED, nothing invented; the render
reads only the committed cache (`scene23_cache.json`).

Product: `cdf` — per word length, the survival CDF of the WINPROB (survival-optimal)
guesser playing against the BEST_OPENER word-choice distribution. Each point is
    {misses: k, p_win: P(survive within k misses), exact: bool}
"Chance of Surviving" at a miss budget k = the frequency-weighted probability (under
best_opener) that the chooser hands the guesser a word the best budget-k guesser wins.

Two sources, stitched at the top solved budget:
  • EXACT (exact=True) — the committed winprob solves
    `math/data/shared/winprob/lenNN_best_opener_nNN.json`, one file per budget n, each
    holding the exact `p_win`. winprob solves each budget independently and exactly, so
    every one of these points is exact. Read straight across n.
  • GREEDY TAIL (exact=False) — for lengths whose top solved budget has p_win < 1 (3–7),
    the winprob tree TRUNCATES at its budget (dumps un-winnable words into a flat "lost"
    list, no further guessing). To extend the CDF past the top budget we greedy-COMPLETE
    those lost branches (the repo's standard capped-leaf finish, reusing
    strategy_view.TreeStrategyView._fill_capped) and read off the additional survival at
    each higher k. These are NOT exact — greedy-from-the-give-up-point is an achievable
    LOWER BOUND on the true budget-k optimum, not the optimum. The scene draws them in
    crimson with a "values not exact" asterisk. Regenerate exact values by solving higher
    winprob budgets: `python math/winprob.py <L> --weighted best_opener`.

Regenerate: `python3 scene23_data.py` (from the assets dir).
"""
from pathlib import Path
import json
import re
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
_WIN = _MATH / "data" / "shared" / "winprob"
CACHE = _ASSETS / "scene23_cache.json"

WEIGHTING = "best_opener"
LENGTHS = range(1, 21)
RESOLVED_EPS = 1e-9          # p_win >= 1 - eps counts as fully resolved (CDF complete)


def get():
    return json.loads(CACHE.read_text())


def _win_budgets(L):
    """[(n, p_win)] for every committed winprob budget file at length L, sorted by n."""
    out = []
    for p in _WIN.glob(f"len{L:02d}_{WEIGHTING}_n*.json"):
        m = re.search(r"_n(\d+)\.json$", p.name)
        if m and "_word_" not in p.name:
            out.append((int(m.group(1)), float(json.loads(p.read_text())["p_win"])))
    return sorted(out)


def _greedy_tail(np, sview, L):
    """Per-word (misses, weights) from the TOP-budget winprob tree with its 'lost'
    branches greedy-completed, so every word gets a finite miss count. Reuses the
    existing capped-leaf machinery by relabelling 'lost' leaves as 'capped'."""
    sv = sview.make_strategy("winprob", L, weighting=WEIGHTING)   # None budget = top
    if not sv.available:
        return None, None

    def relabel(node):
        if "lost" in node:
            node["capped"] = node.pop("lost")        # trigger the greedy finish
            return
        for child in node.get("branches", {}).values():
            relabel(child)

    relabel(sv.tree)
    sv._greedy_mask = np.zeros(sv.g.N, dtype=bool)
    sv.tree = sv._fill_capped(sv.tree, 0, np.arange(sv.g.N))
    sv._pw = None
    return sv.per_word_misses(), sv.word_freq()


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import numpy as np
    import strategy_view as sview

    cdf = {}
    for L in LENGTHS:
        budgets = _win_budgets(L)
        if not budgets:
            continue
        pts = [{"misses": n, "p_win": round(p, 6), "exact": True} for n, p in budgets]
        top_n, top_p = budgets[-1]
        if top_p < 1 - RESOLVED_EPS:                 # unresolved -> greedy tail
            misses, w = _greedy_tail(np, sview, L)
            if misses is not None:
                total = float(w.sum())
                hi = int(np.nanmax(misses))
                for k in range(top_n + 1, hi + 1):
                    pk = float(w[misses <= k].sum() / total)
                    pts.append({"misses": k, "p_win": round(pk, 6), "exact": False})
                    if pk >= 1 - RESOLVED_EPS:
                        break
        cdf[str(L)] = pts

    out = {"cdf": cdf}
    CACHE.write_text(json.dumps(out, indent=2))
    _report(out)
    return out


def _report(out):
    print(f"scene 23 data -> {CACHE.name}\n")
    print("SURVIVAL CDF  P(win within k misses)  winprob vs best_opener  "
          "(* = greedy tail, not exact)")
    for L, pts in out["cdf"].items():
        cells = " ".join(f"{p['misses']}:{p['p_win']:.3f}{'' if p['exact'] else '*'}"
                          for p in pts)
        print(f"len {int(L):>2}  {cells}")


if __name__ == "__main__":
    build()

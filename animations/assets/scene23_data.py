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
  • TAIL (exact=False) — for lengths whose top solved budget has p_win < 1 (3–7), past
    that budget each point is the MAX survival P(misses <= k) of TWO achievable strategies:
    (a) the top-budget winprob tree with its abandoned 'lost' branches greedy-completed,
    and (b) the OPTIMAL strategy (min avg misses vs best_opener, greedy-completed where
    unconverged). Both are real strategies, so each survival is a lower bound on the true
    budget-k optimum, and the max is the best of the two. It is monotone by construction —
    the max of two monotone-in-k survivals is monotone, and (a) starts at the seam value
    p_win(top) so the tail never dips below the exact part (no clamp/flat needed). We stop
    the tail as soon as EITHER strategy reaches 100%. These are drawn crimson with a
    "*values not exact" note. Get exact tail values by solving higher winprob budgets:
    `python math/winprob.py <L> --weighted best_opener`.

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
RESOLVED_EPS = 1e-6          # p_win >= 1 - eps counts as "hit 100%" (CDF complete)


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


def _winprob_tail(np, sview, L):
    """Per-word (misses, weights): the TOP-budget winprob tree with its abandoned
    'lost' branches greedy-completed (relabel 'lost'->'capped' to reuse the standard
    capped-leaf finish). This strategy's survival CONTINUES the winprob curve smoothly
    from the seam (it starts at exactly p_win(top))."""
    sv = sview.make_strategy("winprob", L, weighting=WEIGHTING)   # None = top budget
    if not sv.available:
        return None, None

    def relabel(node):
        if "lost" in node:
            node["capped"] = node.pop("lost")
            return
        for child in node.get("branches", {}).values():
            relabel(child)

    relabel(sv.tree)
    sv._greedy_mask = np.zeros(sv.g.N, dtype=bool)
    sv.tree = sv._fill_capped(sv.tree, 0, np.arange(sv.g.N))
    sv._pw = None
    return sv.per_word_misses(), sv.word_freq()


def _optimal_tail(np, sview, L):
    """Per-word (misses, weights) for the OPTIMAL strategy (min avg misses vs
    best_opener), greedy-completed where the solve did not converge (fill_capped=True)."""
    sv = sview.make_strategy("optimal", L, weighting=WEIGHTING, fill_capped=True)
    if not sv.available:
        return None, None
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
        if top_p < 1 - RESOLVED_EPS:                 # unresolved -> stitch a tail
            wm, ww = _winprob_tail(np, sview, L)     # winprob-greedy continuation
            om, ow = _optimal_tail(np, sview, L)     # optimal strategy
            if wm is not None and om is not None:
                total = float(ww.sum())              # ww == ow (both best_opener weights)
                hi = int(max(np.nanmax(wm), np.nanmax(om)))
                for k in range(top_n + 1, hi + 1):
                    # each tail point = the BEST (max survival) of the two achievable
                    # strategies. Both are monotone in k and the winprob continuation
                    # starts at the seam value, so the max is monotone and never dips.
                    pk = max(float(ww[wm <= k].sum() / total),
                             float(ow[om <= k].sum() / total))
                    pts.append({"misses": k, "p_win": round(pk, 6), "exact": False})
                    if pk >= 1 - RESOLVED_EPS:        # stop when EITHER strategy hits 100%
                        break
        cdf[str(L)] = pts

    out = {"cdf": cdf}
    CACHE.write_text(json.dumps(out, indent=2))
    _report(out)
    return out


def _report(out):
    print(f"scene 23 data -> {CACHE.name}\n")
    print("SURVIVAL CDF  P(win within k misses)  winprob vs best_opener  "
          "(* = tail: max(winprob-cont, optimal), not exact)")
    for L, pts in out["cdf"].items():
        cells = " ".join(f"{p['misses']}:{p['p_win']:.3f}{'' if p['exact'] else '*'}"
                          for p in pts)
        print(f"len {int(L):>2}  {cells}")


if __name__ == "__main__":
    build()

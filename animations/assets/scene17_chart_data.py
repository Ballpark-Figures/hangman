"""Cached data for scene 17 beat d: the OPTIMAL strategy's average misses per word
length, under UNIFORM vs ZIPF (frequency) weighting — the double bar chart.

Per length, per weighting:
  - CONVERGED solve  -> the exact optimum = the CSV `capped_avg` (last row).
  - NOT converged    -> the average of the lower and upper bounds, per the script:
      lower = `capped_avg` (the capped tree truncates capped words, so <= optimum);
      upper = the same tree with its capped leaves GREEDY-finished (>= optimum),
              read as the frequency-weighted mean of `strategy_view`'s per-word misses
              (fill_capped=True) — the "cap N*+greedy" bound.

All SOURCED from the committed optimal solves (`math/data/shared/optimal/lenNN_*.csv`
+ the cap trees replayed by `strategy_view`); nothing invented. Render reads only the
cache. Regenerate with `python3 scene17_chart_data.py`.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
_OPT = _MATH / "data" / "shared" / "optimal"
CACHE = _ASSETS / "scene17_chart_cache.json"

WEIGHTINGS = ("uniform", "zipf")
LENGTHS = range(1, 21)


def get():
    return json.loads(CACHE.read_text())


def _csv_last(path):
    """(capped_avg, converged) from a solve CSV's last row, or None."""
    try:
        rows = [ln.split(",") for ln in path.read_text().splitlines()[1:] if ln.strip()]
    except OSError:
        return None
    if not rows:
        return None
    last = rows[-1]
    return float(last[1]), last[6].strip() == "1"


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import numpy as np
    import strategy_view as sview
    import wordlist

    out = {}
    for weighting in WEIGHTINGS:
        per_len = {}
        for L in LENGTHS:
            got = _csv_last(_OPT / f"len{L:02d}_{weighting}.csv")
            if got is None:
                continue
            lower, converged = got
            if converged:
                avg, upper = lower, lower                     # exact
            else:
                s = sview.make_strategy("optimal", L, weighting=weighting,
                                        fill_capped=True)      # cap*+greedy upper
                if not s.available:
                    continue
                pwm = s.per_word_misses()
                if weighting == "uniform":
                    w = np.ones(len(pwm))
                else:
                    fw = wordlist.freq_weights(min_len=L, max_len=L)
                    w = np.array([fw[word] for word in s.g.words])
                upper = float(np.average(pwm, weights=w))
                avg = (lower + upper) / 2.0
            per_len[str(L)] = {"avg": round(avg, 4), "lower": round(lower, 4),
                               "upper": round(upper, 4), "converged": converged}
        out[weighting] = per_len

    CACHE.write_text(json.dumps(out, indent=2))
    print(f"optimal avg misses by length -> {CACHE.name}")
    lens = sorted({int(k) for pl in out.values() for k in pl})
    print(f"{'L':>3} {'uniform':>18} {'zipf':>18}")
    for L in lens:
        cells = []
        for w in WEIGHTINGS:
            d = out[w].get(str(L))
            cells.append(f"{d['avg']:.3f}{'' if d['converged'] else '*'}" if d else "-")
        print(f"{L:>3} {cells[0]:>18} {cells[1]:>18}   (* = bound-avg)")
    return out


if __name__ == "__main__":
    build()

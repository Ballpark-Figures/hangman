"""Cached data for scene 19 (short_words). Two products, both SOURCED — nothing
invented; the render reads only the committed cache (`short_words_cache.json`).

1. `by_length` — the beat-a DOUBLE PLOT: the OPTIMAL strategy's average misses per
   word length under UNIFORM vs the adversarial BEST_OPENER weighting (same shape as
   scene 17's optimal-vs-zipf double bar). Per length, per weighting:
     - CONVERGED solve -> exact optimum = the CSV `capped_avg` (last row).
     - NOT converged   -> mean of lower/upper bounds (the scene-17 convention):
         lower = `capped_avg` (capped tree truncates capped words, <= optimum);
         upper = same tree, capped leaves GREEDY-finished (>= optimum), read as the
                 weighting-weighted mean of `strategy_view`'s per-word misses.
   Source: `math/data/shared/optimal/lenNN_{uniform,best_opener}.csv` (+ cap trees).

2. `tables` — the per-length TABLES from the multiplier-based adversarial frequency
   search tuned against the best-opener guesser (`FrequencySearch`, objective
   'best_opener'; NOT the per-word 'word' variant). Reconstructed from the committed
   search logs `math/data/freq_search/best_opener/lenNN.csv`:
     - patterns  <- `multipliers_df()`  (Pattern = underscore mask, uppercased;
                     Multiplier = the exact tuned weight, full decimal).
     - words     <- `frequencies_df()`  (Word uppercased; pct = frequency / total * 100).
   Row counts (per the script + user): len 2 -> top/bottom 5 for patterns AND words
   (only len 2 has a Least Common WORDS table, and it has no zero-frequency words);
   len 3 & 4 -> top 12 patterns + top 12 words, most-common only.

Regenerate with `python3 short_words_data.py`.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
_OPT = _MATH / "data" / "shared" / "optimal"
CACHE = _ASSETS / "short_words_cache.json"

WEIGHTINGS = ("uniform", "best_opener")
LENGTHS = range(1, 21)

# per-length table sizes: cap rows per table; `rare` = also emit the Rare tables
# (patterns with multiplier < 1, words with the lowest frequency). Only length 2
# has Rare tables per the script. Pattern tables EXCLUDE multiplier == 1 (unchanged):
# Common = boosted (mult > 1), Rare = reduced (mult < 1).
TABLE_SPEC = {
    2: {"cap": 5, "rare": True},
    3: {"cap": 12, "rare": False},
    4: {"cap": 12, "rare": False},
}


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


def _build_by_length(np, sview):
    out = {}
    for weighting in WEIGHTINGS:
        per_len = {}
        for L in LENGTHS:
            got = _csv_last(_OPT / f"len{L:02d}_{weighting}.csv")
            if got is None:
                continue
            lower, converged = got
            if converged:
                avg, upper = lower, lower                      # exact
            else:
                s = sview.make_strategy("optimal", L, weighting=weighting,
                                        fill_capped=True)       # cap*+greedy upper
                if not s.available:
                    continue
                pwm = s.per_word_misses()
                w = s.word_freq()                               # weighting-agnostic
                upper = float(np.average(pwm, weights=w))
                avg = (lower + upper) / 2.0
            per_len[str(L)] = {"avg": round(avg, 4), "lower": round(lower, 4),
                               "upper": round(upper, 4), "converged": converged}
        out[weighting] = per_len
    return out


def _pattern_rows(rows):
    return [{"pattern": r.pattern.upper(), "multiplier": float(r.multiplier)}
            for r in rows.itertuples(index=False)]


def _word_rows(rows, total):
    # pct kept at full precision here; the scene rounds it (2 significant figures).
    return [{"word": r.word.upper(), "pct": round(100.0 * r.frequency / total, 6)}
            for r in rows.itertuples(index=False)]


def _build_tables(freq_search):
    tables = {}
    for L, spec in TABLE_SPEC.items():
        csv = freq_search._default_log_path("best_opener", L)
        s = freq_search.FrequencySearch.reconstruct(L, csv, objective="best_opener")
        n = spec["cap"]

        mult_df = s.multipliers_df()                            # sorted multiplier desc
        freq_df = s.frequencies_df()                            # sorted frequency desc
        total = float(freq_df["frequency"].sum())

        above = mult_df[mult_df.multiplier > 1]                 # boosted (Common)
        below = mult_df[mult_df.multiplier < 1]                 # reduced (Rare)
        entry = {
            "common_patterns": _pattern_rows(above.head(n)),                  # highest first
            "common_words": _word_rows(freq_df.head(n), total),              # commonest first
        }
        if spec["rare"]:
            entry["rare_patterns"] = _pattern_rows(
                below.sort_values("multiplier").head(n))                      # lowest first
            entry["rare_words"] = _word_rows(
                freq_df.sort_values("frequency").head(n), total)             # rarest first
        tables[str(L)] = entry
    return tables


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import numpy as np
    import strategy_view as sview
    import freq_search

    out = {
        "by_length": _build_by_length(np, sview),
        "tables": _build_tables(freq_search),
    }
    CACHE.write_text(json.dumps(out, indent=2))
    _report(out)
    return out


def _report(out):
    print(f"scene 19 data -> {CACHE.name}\n")
    bl = out["by_length"]
    lens = sorted({int(k) for pl in bl.values() for k in pl})
    print("DOUBLE PLOT  optimal avg misses by length (* = bound-avg, unconverged)")
    print(f"{'L':>3} {'uniform':>16} {'best_opener':>16}")
    for L in lens:
        cells = []
        for w in WEIGHTINGS:
            d = bl[w].get(str(L))
            cells.append(f"{d['avg']:.3f}{'' if d['converged'] else '*'}" if d else "-")
        print(f"{L:>3} {cells[0]:>16} {cells[1]:>16}")
    print()
    for L, spec in TABLE_SPEC.items():
        t = out["tables"][str(L)]
        print(f"LEN {L}  common_patterns[{len(t['common_patterns'])}] "
              f"common_words[{len(t['common_words'])}]"
              + (f" rare_patterns[{len(t['rare_patterns'])}] "
                 f"rare_words[{len(t['rare_words'])}]" if spec["rare"] else ""))
        mp = t["common_patterns"][0]
        mw = t["common_words"][0]
        print(f"       top pattern {mp['pattern']!r} x{mp['multiplier']:g}   "
              f"top word {mw['word']!r} {mw['pct']:.2f}%")


if __name__ == "__main__":
    build()

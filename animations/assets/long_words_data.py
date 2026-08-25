"""Cached data for scene 20 (longer_words). SOURCED — nothing invented; the render reads
only the committed cache (`long_words_cache.json`).

`tables` — the per-length TABLES from the multiplier-based adversarial frequency search
tuned against the best-opener guesser (`FrequencySearch`, objective 'best_opener'; NOT the
per-word 'word' variant), for lengths 5, 6, 7, 8, 9, 10, 16. Reconstructed from the
committed search logs `math/data/freq_search/best_opener/lenNN.csv`:
  - common_patterns <- `multipliers_df()` boosted rows (multiplier > 1, uppercased),
                       highest first, capped at `pat_cap`.
  - words           <- `frequencies_df()`  (Word uppercased; pct = frequency / total * 100),
                       commonest first.

Word-list depth per length is `words`:
  - "all"  -> EVERY word the strategy uses (frequency > 0), ranked. Used for lengths 5/6/7,
              where scene 20 FILTERS by ending (remove Y / ED / ER / ES / ING and reflow) —
              the full list is needed so "only 2 left" / "nothing left" is truthful.
  - <int>  -> the top-N words only (lengths 8/9/10/16, shown as a static "full screen").

The scene applies the ending filters itself (deterministic string ops on the sourced
words); each word carries its own sourced `pct`. The 73% / 97% aggregates spoken in the
voiceover are NOT displayed (script column 2 doesn't ask for them), so they are not computed.

Regenerate with `python3 long_words_data.py`.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
CACHE = _ASSETS / "long_words_cache.json"

# per-length: how many boosted patterns to keep, and how deep the word list goes.
LONG_SPEC = {
    5:  {"pat_cap": 12, "words": "all"},
    6:  {"pat_cap": 12, "words": "all"},
    7:  {"pat_cap": 12, "words": "all"},
    8:  {"pat_cap": 12, "words": 12},
    9:  {"pat_cap": 12, "words": 12},
    16: {"pat_cap": 12, "words": 12},
}


def get():
    return json.loads(CACHE.read_text())


def _pattern_rows(rows):
    return [{"pattern": r.pattern.upper(), "multiplier": float(r.multiplier)}
            for r in rows.itertuples(index=False)]


def _word_rows(rows, total):
    # pct kept at full precision here; the scene rounds it (2 significant figures).
    return [{"word": r.word.upper(), "pct": round(100.0 * r.frequency / total, 6)}
            for r in rows.itertuples(index=False)]


def _build_tables(freq_search):
    tables = {}
    for L, spec in LONG_SPEC.items():
        csv = freq_search._default_log_path("best_opener", L)
        s = freq_search.FrequencySearch.reconstruct(L, csv, objective="best_opener")

        mult_df = s.multipliers_df()                            # sorted multiplier desc
        freq_df = s.frequencies_df()                            # sorted frequency desc
        total = float(freq_df["frequency"].sum())

        # Common (frequent) combos: boosted AND actually exhibited by at least one word
        # with nonzero final weight (a boosted combo whose carrying words all got zeroed
        # out by some other pattern is not shown — it appears in no real word).
        above = mult_df[(mult_df.multiplier > 1) & (mult_df.n_nonzero_words > 0)]
        nonzero = freq_df[freq_df.frequency > 0]                # every word the strategy uses
        words = nonzero if spec["words"] == "all" else nonzero.head(spec["words"])
        tables[str(L)] = {
            "common_patterns": _pattern_rows(above.head(spec["pat_cap"])),
            "words": _word_rows(words, total),
        }
    return tables


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import freq_search

    out = {"tables": _build_tables(freq_search)}
    CACHE.write_text(json.dumps(out, indent=2))
    _report(out)
    return out


def _report(out):
    print(f"scene 20 data -> {CACHE.name}\n")
    for L, spec in LONG_SPEC.items():
        t = out["tables"][str(L)]
        mw = t["words"][0] if t["words"] else {"word": "-", "pct": 0}
        mp = t["common_patterns"][0] if t["common_patterns"] else {"pattern": "-", "multiplier": 0}
        print(f"LEN {L:>2}  common_patterns[{len(t['common_patterns']):>2}] "
              f"words[{len(t['words']):>3}]  "
              f"top pattern {mp['pattern']!r} x{mp['multiplier']:g}   "
              f"top word {mw['word']!r} {mw['pct']:.2f}%")


if __name__ == "__main__":
    build()

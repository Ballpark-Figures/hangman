"""Cached data for scene 22 beats b/c: the GREEDY guesser's average misses per FORCED
opening letter at word length 5, under two word-choice strategies —
  - UNIFORM      (beat b, top half): every word equally likely,
  - BEST_OPENER  (beat c, bottom half): the adversarial choosing strategy from
                 freq_search (objective best_opener), US dictionary.

Each is the forced-opener sweep `misses_by_starting_letter()` on the length-5 greedy
view: for each first letter, force it as the opener then play greedy the rest of the
game, weighted-average misses over the weighting's word distribution. Stored SORTED
best (fewest misses) first, so the scene's bars rise left→right (the voiceover's
"E is the best starting letter … gradually takes more and more guesses"). `best` is
that leftmost letter (greedy's own best opener), highlighted in the scene.

All SOURCED from the live pipeline (`strategy_view.make_strategy('greedy', 5,
weighting=…).misses_by_starting_letter()`, US variant); nothing invented. Render reads
only the cache. Regenerate with `python3 scene22_data.py`.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
CACHE = _ASSETS / "scene22_cache.json"

LENGTH = 5
WEIGHTINGS = ("uniform", "best_opener")


def get():
    return json.loads(CACHE.read_text())


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import strategy_view as sview

    out = {}
    for weighting in WEIGHTINGS:
        s = sview.make_strategy("greedy", LENGTH, weighting=weighting)   # US variant
        if not s.available:
            raise SystemExit(f"greedy/{weighting} len {LENGTH} unavailable: {s.note}")
        by_letter = s.misses_by_starting_letter()                        # {L: avg}, best-first
        letters = [{"letter": ch.upper(), "misses": round(v, 4)}
                   for ch, v in by_letter.items()]
        out[weighting] = {"best": letters[0]["letter"], "letters": letters}

    CACHE.write_text(json.dumps(out, indent=2))
    print(f"greedy misses by forced opener, length {LENGTH} -> {CACHE.name}")
    for weighting in WEIGHTINGS:
        d = out[weighting]
        lo, hi = d["letters"][0]["misses"], d["letters"][-1]["misses"]
        print(f"  {weighting:>12}: best {d['best']} ({lo:.4f})  worst "
              f"{d['letters'][-1]['letter']} ({hi:.4f})  range [{lo:.2f}, {hi:.2f}]")
    return out


if __name__ == "__main__":
    build()

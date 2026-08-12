"""Cached data for scene 17 (re-weighting): the length-2 words + their frequency for
the "Word Frequency" bar graph (beats a/b), SORTED by descending frequency.

Frequency here is the wordlist's ZIPF value (the project's frequency measure; the
`word<TAB>zipf` master list) — a readable log scale. The solver's frequency WEIGHTING is
the linear `round(10**zipf)` rate; if the bars should show that raw rate instead, swap
`zipf` for `10**zipf` here (a few common words would then tower over the rest).

The three tier orderings the scene compares live in `assets/tier_list.py`
(TIER_LETTERS / FREQ_TIER_LETTERS / GB_TIER_LETTERS), also sourced from the notebook.

Regenerate with `python3 scene17_data.py`; the render reads only the committed cache.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
CACHE = _ASSETS / "scene17_cache.json"


def get():
    return json.loads(CACHE.read_text())


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import wordlist

    words = sorted(wordlist.load(min_len=2, max_len=2), key=lambda w: -w.zipf)  # A: desc freq
    data = {"len2": [{"word": w.text, "zipf": round(float(w.zipf), 3)} for w in words]}
    CACHE.write_text(json.dumps(data, indent=2))
    print(f"{len(words)} length-2 words (zipf {words[0].zipf:.2f}..{words[-1].zipf:.2f}) "
          f"-> {CACHE.name}")
    return data


if __name__ == "__main__":
    build()

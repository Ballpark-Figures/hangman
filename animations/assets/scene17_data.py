"""Cached data for scene 17 (re-weighting): the length-2 words + their frequency for
the "Word Frequency" bar graph (beats a/b), SORTED by descending frequency.

`freq` is the ACTUAL word frequency = `round(10**zipf)`, the per-billion occurrence rate
— exactly what `wordlist.freq_weights` / `resolve_weighting("zipf")` feeds the solver as
its frequency WEIGHTING. (`zipf` = log10 of that, kept for reference.) These frequencies
are heavily skewed (the commonest 2-letter words are ~10^4× the rarest), so the bars tower
then flatten — the honest picture of "more common words are more likely."

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
    data = {"len2": [{"word": w.text, "zipf": round(float(w.zipf), 3),
                      "freq": round(10.0 ** w.zipf)}                # the solver's weighting
                     for w in words]}
    CACHE.write_text(json.dumps(data, indent=2))
    print(f"{len(words)} length-2 words (freq {data['len2'][0]['freq']:,} .. "
          f"{data['len2'][-1]['freq']:,}) -> {CACHE.name}")
    return data


if __name__ == "__main__":
    build()

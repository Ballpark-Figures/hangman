"""Cached top n-grams (bigrams + trigrams) per letter for the letter view.

For every letter, the top-5 bigrams and top-5 trigrams that CONTAIN it, ranked by
how many words (any length) hold the n-gram — sourced from
`math/letter_patterns.top_ngrams` (which loads the curated wordlist). Committed to
`letter_ngram_cache.json` so the render needs no wordlist import; regenerate with
`build()` (or `python3 letter_ngram_data.py`). The render path only calls `get()`.
"""
from pathlib import Path
import json
import sys

SIZES = (2, 3)                                # bigrams, trigrams
TOP = 5
_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "letter_ngram_cache.json"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def build():
    """Compute every letter's top bigrams/trigrams, then write the cache.
    Sourced from letter_patterns.top_ngrams."""
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import letter_patterns
    import wordlist

    letters = {}
    for ch in ALPHABET:
        ng = letter_patterns.top_ngrams(ch, sizes=SIZES, top=TOP)   # [(gram, n), …]
        letters[ch] = [[g, n] for g, n in ng]
    data = {"sizes": list(SIZES), "top": TOP, "min_zipf": wordlist.DEFAULT_ZIPF,
            "letters": letters}
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


def get(letter):
    """[(gram, n_words), …] — the top-`TOP` combined n-grams for `letter`, read
    from the committed cache (already ranked: count desc, shorter-first tiebreak)."""
    return [(g, n) for g, n in _load()["letters"][letter.lower()]]


if __name__ == "__main__":
    data = build()
    print(f"wrote {CACHE.name}: {len(data['letters'])} letters, sizes {data['sizes']}, "
          f"top {data['top']} combined, min_zipf {data['min_zipf']}")
    for ch in ("e", "r", "k", "q"):
        ent = data["letters"][ch]
        print(f"  '{ch}': " + ", ".join(f"{g}({n})" for g, n in ent))

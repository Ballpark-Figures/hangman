"""Cached per-letter position-frequency data for the letter-view heatmaps.

For every letter and each word length 2..10, the fraction of length-k words with
that letter at each position — UNWEIGHTED (each word counts once) — sourced from
`math/letter_patterns.position_share` (which loads the curated wordlist via
`wordlist.load`, default cutoff `DEFAULT_ZIPF`). The per-letter MAX over all
lengths/positions is the red end of that letter's colour scale (white = 0).

House pattern: numbers are cached in the committed `letter_heat_cache.json` so a
render needs no wordlist import and the values sync between machines via git.
Regenerate with `build()` (or `python3 letter_heat_data.py`) whenever the
wordlist or the computation changes. The render path only calls `get()`.
"""
from pathlib import Path
import json
import sys

LENGTHS = list(range(2, 11))                 # word lengths 2..10
_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "letter_heat_cache.json"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


def build():
    """Compute every letter's per-(length, position) share and per-letter max,
    then write the cache. Sourced from letter_patterns.position_share."""
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import letter_patterns
    import wordlist

    rows = {ch: {} for ch in ALPHABET}
    for L in LENGTHS:
        shares, _n = letter_patterns.position_share(L)
        for ch in ALPHABET:
            rows[ch][str(L)] = [round(x, 4) for x in shares[ch]]

    letters = {
        ch: {"rows": rows[ch],
             "max": max((v for row in rows[ch].values() for v in row), default=0.0)}
        for ch in ALPHABET
    }
    data = {"weighting": "uniform", "min_zipf": wordlist.DEFAULT_ZIPF,
            "lengths": LENGTHS, "letters": letters}
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


def get(letter):
    """{'lengths': [...], 'rows': {length: [share, …]}, 'vmax': float} for
    `letter` — read straight from the committed cache (no computation)."""
    ent = _load()["letters"][letter.lower()]
    return {"lengths": LENGTHS,
            "rows": {int(k): v for k, v in ent["rows"].items()},
            "vmax": ent["max"]}


if __name__ == "__main__":
    data = build()
    print(f"wrote {CACHE.name}: {len(data['letters'])} letters, "
          f"lengths {data['lengths']}, weighting {data['weighting']}, "
          f"min_zipf {data['min_zipf']}")
    e = data["letters"]["e"]
    print(f"\nletter 'e' — max share {e['max']:.4f}")
    for L in data["lengths"]:
        print(f"  len {L:2d}: " + " ".join(f"{v:.3f}" for v in e["rows"][str(L)]))

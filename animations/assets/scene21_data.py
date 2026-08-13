"""Cached word data for scene 21 (ing_reduction). Everything SOURCED from the
curated frequency wordlist (`math/wordlist.py`, default cutoff zipf >= 2.5) — the
render reads only the committed cache (`scene21_cache.json`).

Three products:

1. `counts` — the three VO blanks (spoken only; NOT rendered on screen, per the
   "voiceover != on-screen" rule): total 4-letter words, total 7-letter words, and
   7-letter words ending in ING. These are `len(wordlist.load(...))` filtered by
   length / `endswith("ing")` — a plain data extraction, not an invented metric.

2. `words4` — the FIRST 100 4-letter words in ALPHABETICAL order (beat e, LEFT
   wall). A DISPLAY SAMPLE: the on-screen count (100) is a cap the script names,
   NOT the true total (that is `counts["len4"]`, said in the VO).

3. `words7` — the FIRST 500 7-letter words in ALPHABETICAL order (beat e, RIGHT
   wall). Same display-sample caveat: 500 is the script's display cap, `counts`
   holds the true totals. Beat f fades those NOT ending in "ing" (a render-time
   string filter, no computation).

The optimal-misses-per-length chart (beat b) is NOT sourced here — it reuses the
existing committed cache via `scene17_chart_data.get()["uniform"]`.

Regenerate with `python3 scene21_data.py`.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
CACHE = _ASSETS / "scene21_cache.json"

# display caps the SCRIPT names for beat e (first N, alphabetical) — a sample, not
# the true totals (those live in `counts`, and are spoken in the VO only).
DISPLAY_4 = 100
DISPLAY_7 = 500


def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return json.loads(CACHE.read_text())


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import wordlist

    four = sorted(w.text for w in wordlist.load(min_len=4, max_len=4))
    seven = sorted(w.text for w in wordlist.load(min_len=7, max_len=7))
    seven_ing = [w for w in seven if w.endswith("ing")]

    out = {
        "counts": {
            "len4": len(four),
            "len7": len(seven),
            "len7_ing": len(seven_ing),
        },
        "words4": four[:DISPLAY_4],
        "words7": seven[:DISPLAY_7],
    }
    CACHE.write_text(json.dumps(out, indent=1))
    _report(out)
    return out


def _report(out):
    c = out["counts"]
    print(f"scene 21 data -> {CACHE.name}\n")
    print("VO BLANKS (spoken only, NOT on screen):")
    print(f"  4-letter words total ........ {c['len4']}")
    print(f"  7-letter words total ........ {c['len7']}")
    print(f"  7-letter -ING words left .... {c['len7_ing']}")
    print()
    print(f"DISPLAY: {len(out['words4'])} 4-letter words (LEFT), "
          f"{len(out['words7'])} 7-letter words (RIGHT), alphabetical.")
    ing_in_display = sum(1 for w in out["words7"] if w.endswith("ing"))
    print(f"  of the {len(out['words7'])} displayed 7-letter words, "
          f"{ing_in_display} end in -ING (survive beat f).")


if __name__ == "__main__":
    build()

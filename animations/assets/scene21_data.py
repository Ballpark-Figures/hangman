"""Cached word data for scene 21 (ing_reduction). Everything SOURCED from the
curated frequency wordlist (`math/wordlist.py`, default cutoff zipf >= 2.5) — the
render reads only the committed cache (`scene21_cache.json`).

Three products:

1. `counts` — the three VO blanks (spoken only; NOT rendered on screen, per the
   "voiceover != on-screen" rule): total 4-letter words, total 7-letter words, and
   7-letter words ending in ING. These are `len(wordlist.load(...))` filtered by
   length / `endswith("ing")` — a plain data extraction, not an invented metric.

2. `words4` — the FIRST 99 4-letter words BY FREQUENCY (beat e, LEFT wall). A
   DISPLAY SAMPLE; the scene adds a "…" last cell (→ 100). True total = `counts["len4"]`.

3. `words7` — the FIRST 279 7-letter words BY FREQUENCY (beat e, RIGHT wall). The
   scene adds a "…" last cell (→ 280). Beat f fades those NOT ending in "ing" (a
   render-time string filter); the "…" cell is kept, to hint the -ING list runs on.

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

# display caps for beat e (first N BY FREQUENCY) — a sample, not the true totals
# (those live in `counts`, spoken in the VO only). The scene adds a "…" last cell,
# so the grids are 99+1 = 100 (5×20) and 279+1 = 280 (7×40).
CAP_4 = 99
CAP_7 = 279


def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return json.loads(CACHE.read_text())


def build():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import wordlist

    # BY FREQUENCY (load() returns most-common first) — a natural alphabet spread,
    # and common 7-letter words include far more -ING words than the A-heavy start
    # of the alphabet did.
    four = [w.text for w in wordlist.load(min_len=4, max_len=4)]
    seven = [w.text for w in wordlist.load(min_len=7, max_len=7)]
    seven_ing = [w for w in seven if w.endswith("ing")]

    out = {
        "counts": {
            "len4": len(four),
            "len7": len(seven),
            "len7_ing": len(seven_ing),
        },
        "words4": four[:CAP_4],
        "words7": seven[:CAP_7],
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
    print(f"DISPLAY (first N by frequency, + a '…' cell): {len(out['words4'])} "
          f"4-letter words (LEFT), {len(out['words7'])} 7-letter words (RIGHT).")
    ing_in_display = sum(1 for w in out["words7"] if w.endswith("ing"))
    print(f"  of the {len(out['words7'])} displayed 7-letter words, "
          f"{ing_in_display} end in -ING (survive beat f).")


if __name__ == "__main__":
    build()

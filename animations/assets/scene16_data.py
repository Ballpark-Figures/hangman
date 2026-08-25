"""Cached pipeline numbers for scene 16 (how to USE the tier list).

Every number scene 16 puts on screen is SOURCED here from the shared math
pipeline and persisted to the committed ``scene16_cache.json`` — the house
pattern (see ``greedy_data.py`` / ``letter_heat_data.py``): the data module
imports the solver/helpers, the scene reads only the cache, the render path never
touches ``math/``.

Two products, both sourced (nothing invented):

  1. The tier-fill plot (beats d–i): for each word length, the average FRACTION
     of the word already filled in at the moment the near-optimal strategy
     finishes each (cumulative) tier. This is ``set_before_outside`` from
     ``letter_analysis.ipynb`` ("Guess-order stats: set letters vs outside
     letters"), lifted into ``math/guess_order.py`` and called here with the
     "set" = a cumulative union of tiers. Strategy = optimal / uniform (matching
     scene 05's "optimal" and the notebook defaults STRATEGY/WEIGHTING).
       fraction filled when tier T finishes  =
           set_before_outside(tiers[0..T], length) / length
     A tier is "finished" the moment the strategy first guesses a letter from a
     LOWER tier (the notebook's own definition) — the method the user approved.

  2. The example game (beat j): the optimal/uniform strategy's guess sequence for
     the word BOARDS, via ``strategy_view.make_strategy("optimal", 6).trace``.

Regenerate with ``build()`` (or ``python3 scene16_data.py``) whenever the
wordlist, tiers, or a solve changes. The render path only calls ``get()``.
``provenance()`` prints where each number comes from.

FLAGS (values a human still owns):
  - ``EXAMPLE_WORD`` — the beat-j demo word (the animation column says BOARDS).
    Its optimal guess sequence falls out of the trace; the WORD is the choice.
  - ``DISPLAY_LENGTHS`` — which length rows the beat d–i plot draws: lengths
    2–10, matching the position-frequency heatmap views in the tier scenes
    (``letter_heat_data.LENGTHS``). The cache still stores every length 1–20
    (``PLOT_LENGTHS``) so the scene can pick.
  - Tiers shown as fill segments stop at LOW↑ (index 5): the script fills through
    "first bottom tier" only — "we'll usually finish the whole word without ever
    dipping into the last tier", so LOW↓ (XZJQ) gets no segment.

SYNC NOTE: ``TIER_LETTERS`` below MUST match ``tier_list.TIER_LETTERS`` (both
trace to ``letter_analysis.ipynb``'s ORDER cell). Mirrored here (not imported) so
this data build stays free of the manim/config import chain that tier_list pulls.
"""
from pathlib import Path
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "scene16_cache.json"

# ── config (mirrors the notebook: STRATEGY="optimal", WEIGHTING="uniform") ──────
STRATEGY = "optimal"
WEIGHTING = "uniform"
FILL_CAPPED = True          # finish cap-truncated optimal branches with greedy
PLOT_LENGTHS = list(range(1, 21))   # computed/cached for every length …
# … but the plot DISPLAYS only these rows, to match the position-frequency
# ("Position Frequencies") heatmap views in the tier scenes, which use
# letter_heat_data.LENGTHS = range(2, 11). So the plot shows lengths 2..10.
DISPLAY_LENGTHS = list(range(2, 11))

# ── FLAG: the beat-j example word ───────────────────────────────────────────────
# Chosen for the tier-walk lesson: 6-8 letters, MULTIPLE misses, the optimal/uniform
# guess order descends the tiers WITHOUT skipping one (and backs up a tier a couple
# times). "players": E✓ S✓ T✗ R✓ A✓ L✓ B✗ P✓ Y✓ — TOP→H▲→H▼, back to H▲/TOP, then
# down to LOW▲; 2 misses (T, B). (The script's animation column said BOARDS, but the
# VO left the word open — "FIND EXAMPLE TO PUT HERE"; picked with the user.)
EXAMPLE_WORD = "players"
_MISS_BUDGET = 6            # a game is LOST once misses exceed the 6-part hangman

# SYNC with tier_list.TIER_LETTERS — top tier first, LOW↓ last.
TIER_LETTERS = ["EIA", "SR", "TNO", "LDC", "PUGMBH", "FYVWK", "XZJQ"]
NAME_LABELS = ["TOP", "HIGH_UP", "HIGH_DOWN", "MID_UP", "MID_DOWN", "LOW_UP", "LOW_DOWN"]
# The plot fills a segment per tier as it is "finished", through LOW↑ (index 5).
FILL_TIERS = list(range(6))   # 0..5 (TOP … LOW↑); LOW↓ (6) gets no segment.


def _imports():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import guess_order
    import strategy_view as sview
    return guess_order, sview


# ── product 1: per-length fraction filled when each cumulative tier finishes ────
def _tier_fill():
    guess_order, _sview = _imports()
    cum = ""
    tiers = []
    for idx in FILL_TIERS:
        cum += TIER_LETTERS[idx].lower()
        cum_sorted = "".join(sorted(set(cum)))
        before = guess_order.set_before_outside_by_length(
            cum, PLOT_LENGTHS, strategy=STRATEGY, weighting=WEIGHTING,
            fill_capped=FILL_CAPPED)
        frac = {L: min(before[L] / L, 1.0) for L in before}
        tiers.append({
            "idx": idx,
            "name": NAME_LABELS[idx],
            "letters": TIER_LETTERS[idx].lower(),
            "cum_letters": cum_sorted,
            # occurrences filled before the strategy drops below this cumulative set
            "before_by_len": {str(L): round(before[L], 4) for L in before},
            # that, as a fraction of the word's length (what the plot draws)
            "frac_by_len": {str(L): round(frac[L], 4) for L in frac},
        })
    return tiers


# ── product 2: the BOARDS example game (optimal / uniform) ──────────────────────
def _example_game():
    _guess_order, sview = _imports()
    word = EXAMPLE_WORD
    s = sview.make_strategy(STRATEGY, len(word), weighting=WEIGHTING,
                            fill_capped=FILL_CAPPED)
    if not s.available:
        raise RuntimeError(f"no committed {STRATEGY}/{WEIGHTING} solve at "
                           f"length {len(word)} for {word!r}")
    seq = s.trace(word)   # [(letter, hit?), …]; trailing forced hits appended
    n_misses = sum(1 for _, hit in seq if not hit)
    win = n_misses <= _MISS_BUDGET

    revealed = ["_"] * len(word)
    boards, shown_misses, miss_count = [], [], 0
    for ltr, hit in seq:
        if hit:
            for p, c in enumerate(word):
                if c == ltr:
                    revealed[p] = ltr
        else:
            miss_count += 1
            shown_misses.append(ltr)
        boards.append("".join(revealed))   # board AFTER this guess
    return {
        "word": word,
        "trace": [[ltr, bool(hit)] for ltr, hit in seq],
        "boards_after": boards,            # revealed board after each guess (parallel to trace)
        "n_misses": n_misses,
        "win": win,
        "misses": shown_misses,
        # NB: strategy_view.trace appends the post-determination tail ALPHABETICALLY
        # (a known display-order discrepancy, see hangman CLAUDE.md "Game / guess-order
        # convention"); miss counts are unaffected (the tail is all hits). Reorder the
        # tail by first-appearance in the scene if the played-out order should match it.
    }


def build():
    data = {
        "strategy": STRATEGY,
        "weighting": WEIGHTING,
        "fill_capped": FILL_CAPPED,
        "lengths": PLOT_LENGTHS,
        "display_lengths": DISPLAY_LENGTHS,
        "tier_letters": [t.lower() for t in TIER_LETTERS],
        "tiers": _tier_fill(),
        "example": _example_game(),
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def get():
    return json.loads(CACHE.read_text())


def provenance():
    d = build()
    print(f"scene16 numbers  |  strategy={d['strategy']} / {d['weighting']} "
          f"/ fill_capped={d['fill_capped']}")
    print("\ntier-fill plot (source: math/guess_order.set_before_outside_by_length,")
    print("                lifted from letter_analysis.ipynb 'set_before_outside'):")
    for t in d["tiers"]:
        f = t["frac_by_len"]
        samples = "  ".join(f"L{L}={f[str(L)]:.2f}" for L in (3, 6, 10, 15) if str(L) in f)
        print(f"  tier {t['idx']} {t['name']:<10} cum={t['cum_letters']:<22} {samples}")
    ex = d["example"]
    seq = "  ".join(f"{l}{'+' if h else '-'}" for l, h in ex["trace"])
    print(f"\nexample game (source: strategy_view.make_strategy('optimal', "
          f"{len(ex['word'])}).trace):")
    print(f"  {ex['word'].upper()}  win={ex['win']}  misses={ex['n_misses']} "
          f"({','.join(ex['misses']) or '—'})")
    print(f"  {seq}")


if __name__ == "__main__":
    provenance()

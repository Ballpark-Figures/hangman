"""Cached data for scene 11 (the intermission).

Two sourced pieces, both read at render from committed JSON (the render path never
imports ``math/``):

  1. The TIER-BACKBONE distribution (beats b/c/d pie) — the fraction of words that,
     after opening with the 8 top-3-tier letters, use only those letters / are pinned
     to one option / take 0,1,2,… additional misses under the optimal strategy. This is
     the heavy computation in ``math/tier_backbone.py``, which writes
     ``scene11_cache.json``. This module only READS it (run tier_backbone.py to make it).

  2. The FIGURES play-out (beat f) — the optimal strategy's guess sequence for the word
     ``figures`` (length 7), replayed from the committed L7 tree via ``strategy_view``.
     ``build()`` sources it and writes ``scene11_figures_cache.json``.

``get()`` merges both.

CAVEAT (L7 tree): the FIGURES trace comes from the committed ``len07_uniform`` tree,
which is one of the ~0.5 % suboptimal reconstructions (see
``math/optimal_discrepancy_report.md``). The play-out still WINS; regenerate this cache
(``python3 scene11_data.py``) once L7 is refreshed.
"""
from pathlib import Path
import json
import sys

_ASSETS = Path(__file__).resolve().parent
_MATH = _ASSETS.parents[1] / "math"
DIST_CACHE = _ASSETS / "scene11_cache.json"            # written by math/tier_backbone.py
FIG_CACHE = _ASSETS / "scene11_figures_cache.json"     # written by build() below

FIGURES_WORD = "figures"


def get():
    """Merged scene-11 data: ``{"dist": <tier-backbone>, "figures": <play-out>}``.
    Either value is ``None`` if its cache has not been generated yet (so the scene can
    flag a missing source instead of the render dying obscurely)."""
    dist = json.loads(DIST_CACHE.read_text()) if DIST_CACHE.exists() else None
    fig = json.loads(FIG_CACHE.read_text()) if FIG_CACHE.exists() else None
    return {"dist": dist, "figures": fig}


def build():
    """Source the FIGURES optimal play-out from the committed L7 tree and cache it,
    INCLUDING the candidate set after every guess (count + word list) — the scene shows
    "Words Remaining: N" ticking down, then writes out the remaining words and crosses
    them off. The narrowing is exact given the guess ORDER (each guess keeps only words
    whose pattern for that letter matches FIGURES's), which is what the optimal strategy
    observes. Cheap (mask filtering)."""
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import numpy as np
    import strategy
    import strategy_view as sview

    game = strategy.GreedyGame(len(FIGURES_WORD))       # every length-7 word
    i_fig = game._index[FIGURES_WORD]
    masks = game.masks
    s = sview.make_strategy("optimal", len(FIGURES_WORD), weighting="uniform")
    if not s.available:
        raise RuntimeError(f"no committed optimal L{len(FIGURES_WORD)} tree: {s.note}")
    seq = s.trace(FIGURES_WORD)                         # [(letter, hit_bool), ...]

    # candidate set narrows to words matching FIGURES's pattern for each guessed letter
    S = np.arange(game.N)
    steps = []
    for letter, hit in seq:
        c = ord(letter) - 97
        S = S[masks[S, c] == masks[i_fig, c]]
        steps.append({"letter": letter, "hit": bool(hit), "count": int(S.shape[0]),
                      "words": [game.words[int(w)] for w in S]})

    data = {
        "word": FIGURES_WORD,
        "total": int(game.N),                          # # of 7-letter words in the list
        "guesses": [{"letter": ch, "hit": bool(hit)} for ch, hit in seq],
        "n_misses": sum(1 for _, hit in seq if not hit),
        "steps": steps,                                # per-guess: count + remaining words
        "source": ("guess ORDER from strategy_view.make_strategy('optimal', 7, 'uniform')"
                   ".trace (committed len07_uniform tree — see L7 caveat); candidate sets"
                   " by exact mask filtering on the length-7 wordlist"),
    }
    FIG_CACHE.write_text(json.dumps(data, indent=2))
    print(f"figures play-out: {data['total']} 7-letter words, {data['n_misses']} misses "
          f"over {len(seq)} guesses -> {FIG_CACHE.name}")
    for st in steps:
        print(f"  {st['letter']}  {'HIT ' if st['hit'] else 'miss'}  -> {st['count']:4d} words remaining")
    return data


if __name__ == "__main__":
    build()

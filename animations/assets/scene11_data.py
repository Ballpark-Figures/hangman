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
    """Source the FIGURES optimal play-out from the committed L7 tree and cache it.
    Cheap (a single word replayed through one committed tree)."""
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import strategy_view as sview

    s = sview.make_strategy("optimal", len(FIGURES_WORD), weighting="uniform")
    if not s.available:
        raise RuntimeError(f"no committed optimal L{len(FIGURES_WORD)} tree: {s.note}")
    seq = s.trace(FIGURES_WORD)                         # [(letter, hit_bool), ...]
    data = {
        "word": FIGURES_WORD,
        "guesses": [{"letter": ch, "hit": bool(hit)} for ch, hit in seq],
        "n_misses": sum(1 for _, hit in seq if not hit),
        "source": ("strategy_view.make_strategy('optimal', 7, 'uniform').trace"
                   " — committed len07_uniform tree (see L7 caveat in module docstring)"),
    }
    FIG_CACHE.write_text(json.dumps(data, indent=2))
    print(f"figures play-out: {data['n_misses']} misses over {len(seq)} guesses "
          f"-> {FIG_CACHE.name}")
    for g in data["guesses"]:
        print(f"  {g['letter']}  {'HIT' if g['hit'] else 'miss'}")
    return data


if __name__ == "__main__":
    build()

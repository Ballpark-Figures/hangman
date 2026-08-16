"""Cached pipeline numbers for scene 18 (the choosing strategy).

House pattern (see ``greedy_data.py`` / ``tree2_data.py``): this module imports the
shared math pipeline, computes the handful of numbers each beat shows, and persists
them to the committed ``scene18_cache.json``. The SCENE reads only ``get()``; the
render path never touches ``math/``. Nothing here is invented — every value is
sourced from an existing solver/search helper.

Beat map (Script.md scene 18; subscene LETTER = the render/address key):
  a. "Words with Most Misses" table  -> OPTIMAL guessing strategy, per-word misses
     over the whole wordlist, global hardest words. Source:
     ``strategy_view.make_strategy("optimal", L, weighting="uniform")`` per length,
     its ``per_word_misses`` / ``per_word_status``. Where a length's exact solve has
     not converged we use the deepest committed cap greedy-completed (an UPPER bound
     on the true optimal misses) -- flagged per word via ``exact``.
  b. Optimal length-2 tree  -> already cached in ``tree2_data.py`` (the end state of
     scene 05); NOT re-cached here. See ``TREE_REF`` below.
  c. Final length-4 best-opener CHOOSING strategy: headline avg misses, the top words
     by frequency (left), the top letter-combos by adjustment factor / multiplier
     (right). Source: ``freq_search.FrequencySearch.reconstruct(4, best_opener/len04
     .csv, objective="best_opener")`` -> ``.frequencies_df()`` / ``.multipliers_df()``.
  d/e. Illustrative single steps: d boosts one combo from uniform so misses RISE (kept),
     e makes a DIFFERENT change that LOWERS misses (a failure -> undo -> reset). Both are
     chosen so a tracked WORD bar moves with the combo bar; numbers re-scored from the
     game (see _demo_keep / _demo_undo).
  f. The whole length-4 optimization replayed in N_BUCKETS steps: the tracked combo
     multipliers + word frequencies + avg misses at each checkpoint. Source: the same
     log, replayed with ``reconstruct(upto=k)`` at each bucket boundary.

Regenerate with ``build()`` (or ``python3 scene18_data.py``).

FLAGS (a human still owns these display choices):
  - ``TRACK_N`` -- how many combo bars / word bars beats c-f show (a layout choice,
    not a sourced fact). The SET of bars is "the top N by final value."
  - ``N_BUCKETS`` -- how many steps beat f splits the optimization into.
  - ``MOST_MISSES_ROWS`` -- how many rows the beat-a table lists (script: "top 10, or
    a few more to include ties"). Ties at the max-miss count are always kept whole.
  - beats d/e pick their change automatically (biggest RAISE / DROP that moves a
    tracked word); ``BEAT_DEMO_FACTORS`` is the probed factor set.
"""
from pathlib import Path
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "scene18_cache.json"

# ── length-2 best-opener choosing strategy (beats c-f) ─────────────────────────
BO_LENGTH = 2
OBJECTIVE = "best_opener"
TRACK_N = 30          # FLAG: # of combo bars + word bars shown (3 rows of 10)
# beat f uses ONE step per accepted change (len-2 has only ~15), not fixed buckets.

# ── beat 1 (most misses under optimal play) ───────────────────────────────────
MOST_MISSES_ROWS = 12   # FLAG: table rows to list (ties at the max are always kept)
BEAT1_WEIGHTING = "uniform"   # the scene-05 optimal strategy is on the uniform game
BEAT1_LENGTHS = range(1, 21)

# ── beats d/e (illustrative single steps) ─────────────────────────────────────
# PINNED demo combos (stable across display tweaks; both are forced into the shown
# grid). BOTH are RAISED (x2); d's raise RAISES misses (kept, green), e's raise LOWERS
# misses (a failure: green up, then crimson back down -> reset). Each moves a tracked
# WORD bar so the combo->word propagation is visible.
BEAT_D_PATTERN, BEAT_D_FACTOR = "_y", 2.0       # d: 'y' in slot 2 -> by/my   (RAISE, kept)
BEAT_E_PATTERN, BEAT_E_FACTOR = "_o", 2.0       # e: 'o' in slot 2 -> to/do/no (RAISE, fails)
DEMO_COMBOS = (BEAT_D_PATTERN, BEAT_E_PATTERN)

# beat b is the optimal length-2 tree = the end of scene 05, already cached in
# tree2_data.py; the scene imports that module directly. Nothing to cache here.
TREE_REF = {"source": "tree2_data.py", "length": 2, "weighting": "uniform"}


def _imports():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import freq_search
    import strategy_view
    import wordlist
    return freq_search, strategy_view, wordlist


# ── beat 1: hardest words under the optimal guessing strategy ──────────────────
def _most_misses(strategy_view):
    """Every word's misses under optimal play, across all lengths; the global
    hardest first. ``exact`` is False where the length's solve had not converged
    and the count is a greedy-completed UPPER bound."""
    rows = []
    per_length = {}
    for L in BEAT1_LENGTHS:
        view = strategy_view.make_strategy("optimal", L, weighting=BEAT1_WEIGHTING,
                                           fill_capped=True)
        if not getattr(view, "available", True):
            continue
        words = view.g.words
        misses = view.per_word_misses()
        status = view.per_word_status()          # 0 exact, 3 greedy-completed (upper bd)
        summ = view.summary()
        per_length[str(L)] = {
            "n_words": int(view.g.N),
            "converged": (summ.get("greedy_finished", 0) == 0),
            "greedy_finished": int(summ.get("greedy_finished", 0)),
            "max_misses": int(misses.max()) if len(misses) else 0,
        }
        for w, m, st in zip(words, misses, status):
            rows.append((w, int(L), int(m), bool(st == 0)))
    rows.sort(key=lambda r: (-r[2], r[1], r[0]))
    max_m = rows[0][2] if rows else 0
    # keep at least MOST_MISSES_ROWS, but never split a tie at the top count
    keep = max(MOST_MISSES_ROWS, sum(1 for r in rows if r[2] == max_m))
    table = [{"word": w, "length": L, "misses": m, "exact": ex}
             for (w, L, m, ex) in rows[:keep]]
    tied = [r["word"] for r in table if r["misses"] == max_m]
    return {
        "weighting": BEAT1_WEIGHTING,
        "max_misses": max_m,
        "tied_at_max": tied,
        "all_tied_exact": all(r["exact"] for r in table if r["misses"] == max_m),
        "table": table,
        "per_length": per_length,
    }


# ── beats 3-6: the length-4 best-opener choosing strategy ──────────────────────
def _log_path(freq_search):
    return freq_search._default_log_path(OBJECTIVE, BO_LENGTH)   # best_opener/len04.csv


def _reconstruct(freq_search, upto):
    return freq_search.FrequencySearch.reconstruct(
        BO_LENGTH, _log_path(freq_search), objective=OBJECTIVE, upto=upto)


def _score(s):
    return float(s.game.best_opener_misses(s.freq)[1])


def _tracked(s, patterns, words):
    """The tracked combo multipliers and word frequencies for state ``s``, in the
    fixed ``patterns`` / ``words`` order (parallel to the bars on screen)."""
    m = dict(zip(s.multipliers_df().pattern, s.multipliers_df().multiplier))
    f = dict(zip(s.frequencies_df().word, s.frequencies_df().frequency))
    return [float(m[p]) for p in patterns], [float(f[w]) for w in words]


def _set_mult(s, pattern, value):
    s.mult[s.pattern.index(pattern)] = value
    s._recompute_freq()


def _choosing_strategy(freq_search, wordlist):
    import pandas as pd

    csv_path = _log_path(freq_search)
    log = pd.read_csv(csv_path)
    n_changes = len(log)

    final = _reconstruct(freq_search, None)
    mult_df = final.multipliers_df()
    bo_letter, final_avg = final.game.best_opener_misses(final.freq)

    # The bars shown are chosen from the NATURAL wordlist, not the strategy's winners:
    #  - WORDS: the most common real 2-letter words, by zipf frequency.
    #  - COMBOS: the most common letter-combos in the (uniform) wordlist, by # of words
    #            (n_words). At length 2 every combo is single-position (no repeats).
    # (The bar HEIGHTS still track each word's strategy frequency / each combo's
    #  adjustment multiplier as the optimization runs.)
    words2 = wordlist.load(min_len=BO_LENGTH, max_len=BO_LENGTH)
    zipf = {w.text: float(w.zipf) for w in words2}
    game_words = set(final.game.words)
    word_list = [w.text for w in sorted(words2, key=lambda w: -w.zipf)
                 if w.text in game_words][:TRACK_N]
    by_count = mult_df.sort_values("n_words", ascending=False)
    common = [p for p in by_count.pattern if p not in DEMO_COMBOS]
    combo_patterns = (list(DEMO_COMBOS) + common)[:TRACK_N]   # demo combos lead, then commonest

    nwords = dict(zip(mult_df.pattern, mult_df.n_words))
    final_cm, final_wf = _tracked(final, combo_patterns, word_list)
    beat3 = {
        "length": BO_LENGTH, "objective": OBJECTIVE,
        "best_opener_letter": bo_letter, "avg_misses": float(final_avg),
        "n_changes": int(n_changes),
        "top_words": [{"word": w, "zipf": round(zipf[w], 3), "frequency": float(f)}
                      for w, f in zip(word_list, final_wf)],
        "top_combos": [{"pattern": p, "n_words": int(nwords[p]), "multiplier": float(m)}
                       for p, m in zip(combo_patterns, final_cm)],
    }

    # beat f: ONE snapshot per accepted change (upto = 0 uniform .. n_changes final).
    # Each snapshot carries the tracked bars, the avg, AND the best-opener greedy TREE
    # for that frequency state (the mini tree that updates alongside the avg).
    buckets = []
    for upto in range(n_changes + 1):
        s = _reconstruct(freq_search, upto)
        snap = _snapshot(s, combo_patterns, word_list)
        snap["upto"] = upto
        buckets.append(snap)
    beat6 = {"tracked_combos": combo_patterns, "tracked_words": word_list,
             "buckets": buckets}

    beat4 = _demo_keep(freq_search, combo_patterns, word_list)
    beat5 = _demo_undo(freq_search, combo_patterns, word_list, beat4)
    return beat3, beat6, beat4, beat5


def _greedy_tree(game, freq, opener):
    """The WHOLE best-opener greedy decision tree for this frequency state, as nested
    {leaf | (n, guess, kids=[{miss, sub}])}. Root guess is forced to ``opener`` (the best
    first letter), greedy below. Sourced from GreedyGame.state — the c/f mini trees render
    the SHAPE only (dots + hit/miss edges); ``guess`` is the letter guessed at each node
    (also sourced from the state), used by beat b's LETTERED build of the uniform tree."""
    empty = "_" * game.length

    def rec(board, missed):
        st = game.state(board, missed, freq, opener=opener)
        if st["determined"] or not st["guess"]:
            return {"leaf": True}
        return {"leaf": False, "n": int(st["n"]), "guess": st["guess"],
                "kids": [{"miss": (not oc["hit"]), "sub": rec(oc["board"], oc["missed"])}
                         for oc in st["outcomes"]]}
    return rec(empty, "")


def _snapshot(s, patterns, words):
    cm, wf = _tracked(s, patterns, words)
    opener, avg = s.game.best_opener_misses(s.freq)
    return {"combo_mult": cm, "word_freq": wf, "avg_misses": float(avg),
            "opener": opener, "tree": _greedy_tree(s.game, s.freq, opener)}


def _moved(a, b, words):
    return [w for w, x, y in zip(words, a["word_freq"], b["word_freq"]) if x != y]


def _demo_keep(freq_search, patterns, words):
    """Beat 4: the PINNED combo BEAT_D_PATTERN boosted from the uniform start (raises
    misses -> KEEP). before = uniform (all bars equal), after = that combo + its
    dependent word bars."""
    s = _reconstruct(freq_search, 0)
    before = _snapshot(s, patterns, words)
    _set_mult(s, BEAT_D_PATTERN, BEAT_D_FACTOR)
    after = _snapshot(s, patterns, words)
    return {"pattern": BEAT_D_PATTERN, "value": BEAT_D_FACTOR,
            "moved_words": _moved(before, after, words), "before": before, "after": after}


def _demo_undo(freq_search, patterns, words, keep):
    """Beat 5: the PINNED combo BEAT_E_PATTERN changed on top of the beat-4 state — a
    FAILED change (lowers misses). Then undo (back to the beat-4 state) and reset (back
    to the uniform start)."""
    s = _reconstruct(freq_search, 0)
    _set_mult(s, keep["pattern"], keep["value"])           # the beat-4 kept state
    base = _snapshot(s, patterns, words)
    _set_mult(s, BEAT_E_PATTERN, BEAT_E_FACTOR)
    worse = _snapshot(s, patterns, words)
    reset = _snapshot(_reconstruct(freq_search, 0), patterns, words)   # uniform
    return {"pattern": BEAT_E_PATTERN, "value": BEAT_E_FACTOR,
            "moved_words": _moved(base, worse, words),
            "base": base, "worse": worse, "reset": reset}


def build():
    freq_search, strategy_view, wordlist = _imports()

    most_misses = _most_misses(strategy_view)
    beat3, beat6, beat4, beat5 = _choosing_strategy(freq_search, wordlist)

    data = {
        "meta": {"min_zipf": wordlist.DEFAULT_ZIPF, "track_n": TRACK_N,
                 "length": BO_LENGTH},
        "most_misses": most_misses,      # beat a
        "tree_ref": TREE_REF,            # beat b (pointer to tree2_data.py)
        "choosing": beat3,               # beat c (final state)
        "example_keep": beat4,           # beat d
        "example_undo": beat5,           # beat e
        "optimization": beat6,           # beat f (one step per change)
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


# ── render-side accessor (reads the committed cache; no computation) ───────────
def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return _load()


if __name__ == "__main__":
    data = build()
    m = data["meta"]
    print(f"wrote {CACHE.name}  (min_zipf {m['min_zipf']}, track_n {m['track_n']})\n")

    mm = data["most_misses"]
    print(f"[a] hardest words under optimal ({mm['weighting']}): "
          f"{mm['max_misses']} misses each")
    exact_tag = "exact" if mm["all_tied_exact"] else "UPPER BOUND (unconverged length)"
    print(f"        tied at max ({exact_tag}): {', '.join(mm['tied_at_max'])}")
    print(f"        table (top {len(mm['table'])}):")
    for r in mm["table"]:
        star = "" if r["exact"] else "  (*)"
        print(f"          {r['word']:<10s} len {r['length']:>2d}  "
              f"{r['misses']} misses{star}")
    print("        (*) = greedy-completed upper bound, length not converged")

    ch = data["choosing"]
    print(f"\n[c] length-{ch['length']} best-opener choosing strategy: "
          f"avg misses {ch['avg_misses']:.2f} (opener {ch['best_opener_letter']!r}), "
          f"{ch['n_changes']} accepted changes")
    print(f"        top words:  " +
          ", ".join(f"{w['word']}({w['frequency']:g})" for w in ch["top_words"][:5]))
    print(f"        top combos: " +
          ", ".join(f"{c['pattern']}(x{c['multiplier']:g})" for c in ch["top_combos"][:5]))

    k = data["example_keep"]
    print(f"\n[d] keep: combo {k['pattern']!r} -> x{k['value']:g} from uniform, "
          f"avg {k['before']['avg_misses']:.4f} -> {k['after']['avg_misses']:.4f} (UP, kept)")
    print(f"        dependent words that move: {', '.join(k['moved_words']) or '(none)'}")
    u = data["example_undo"]
    print(f"[e] undo: combo {u['pattern']!r} -> x{u['value']:g}, "
          f"avg {u['base']['avg_misses']:.4f} -> {u['worse']['avg_misses']:.4f} (DOWN = failure), "
          f"then reset to uniform {u['reset']['avg_misses']:.4f}")
    print(f"        dependent words that move: {', '.join(u['moved_words']) or '(none)'}")

    opt = data["optimization"]

    def _tree_nodes(t):
        return 1 if t.get("leaf") else 1 + sum(_tree_nodes(k["sub"]) for k in t["kids"])

    print(f"\n[f] {len(opt['buckets'])} snapshots (one per change); avg + opener + tree size:")
    for b in opt["buckets"]:
        print(f"        upto {b['upto']:>2d}: avg {b['avg_misses']:.3f}  "
              f"opener {b['opener']!r}  tree {_tree_nodes(b['tree'])} nodes")

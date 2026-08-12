"""Cached pipeline numbers for scene 18 (the choosing strategy).

House pattern (see ``greedy_data.py`` / ``tree2_data.py``): this module imports the
shared math pipeline, computes the handful of numbers each beat shows, and persists
them to the committed ``scene18_cache.json``. The SCENE reads only ``get()``; the
render path never touches ``math/``. Nothing here is invented — every value is
sourced from an existing solver/search helper.

Beat map (Script.md scene 18):
  1. "Words with Most Misses" table  -> OPTIMAL guessing strategy, per-word misses
     over the whole wordlist, global hardest words. Source:
     ``strategy_view.make_strategy("optimal", L, weighting="uniform")`` per length,
     its ``per_word_misses`` / ``per_word_status``. Where a length's exact solve has
     not converged we use the deepest committed cap greedy-completed (an UPPER bound
     on the true optimal misses) -- flagged per word via ``exact``.
  2. Optimal length-2 tree  -> already cached in ``tree2_data.py`` (the end state of
     scene 05); NOT re-cached here. See ``BEAT2`` note below.
  3. Final length-4 best-opener CHOOSING strategy: headline avg misses, the top words
     by frequency (left), the top letter-combos by adjustment factor / multiplier
     (right). Source: ``freq_search.FrequencySearch.reconstruct(4, best_opener/len04
     .csv, objective="best_opener")`` -> ``.frequencies_df()`` / ``.multipliers_df()``.
  4/5. An illustrative accepted change (raises misses -> keep) and a perturbation off
     the converged optimum (lowers misses -> undo). Sourced from the log / re-scored.
  6. The whole length-4 optimization replayed in 10 equal buckets: the tracked combo
     multipliers + word frequencies + avg misses at each checkpoint. Source: the same
     log, replayed with ``reconstruct(upto=k)`` at each bucket boundary.

Regenerate with ``build()`` (or ``python3 scene18_data.py``).

FLAGS (a human still owns these display choices):
  - ``TRACK_N`` -- how many combo bars / word bars beats 3 and 6 show (a layout
    choice, not a sourced fact). The SET of bars is "the top N by final value."
  - ``MOST_MISSES_ROWS`` -- how many rows the beat-1 table lists (script: "top 10, or
    a few more to include ties"). Ties at the max-miss count are always kept whole.
  - beats 4/5 pick ONE change to showcase (``BEAT4_SEQ`` / ``BEAT5_PATTERN``) -- which
    one is a narrative choice; the numbers around it are sourced.
"""
from pathlib import Path
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "scene18_cache.json"

# ── length-4 best-opener choosing strategy (beats 3-6) ─────────────────────────
BO_LENGTH = 4
OBJECTIVE = "best_opener"
TRACK_N = 10          # FLAG: # of combo bars + word bars shown (layout choice)
N_BUCKETS = 10        # script: "10 equal sized buckets"

# ── beat 1 (most misses under optimal play) ───────────────────────────────────
MOST_MISSES_ROWS = 12   # FLAG: table rows to list (ties at the max are always kept)
BEAT1_WEIGHTING = "uniform"   # the scene-05 optimal strategy is on the uniform game
BEAT1_LENGTHS = range(1, 21)

# ── beats 4/5 (illustrative single changes) ───────────────────────────────────
BEAT4_SEQ = None        # FLAG: which accepted change to showcase (None -> biggest jump)
BEAT5_PATTERN = None    # FLAG: which combo to perturb off the optimum (None -> top combo)

# beat 2 is the optimal length-2 tree = the end of scene 05, already cached in
# tree2_data.py; the scene imports that module directly. Nothing to cache here.
BEAT2 = {"source": "tree2_data.py", "length": 2, "weighting": "uniform"}


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


def _choosing_strategy(freq_search):
    import pandas as pd

    csv_path = _log_path(freq_search)
    log = pd.read_csv(csv_path)
    n_changes = len(log)

    final = _reconstruct(freq_search, None)
    mult_df = final.multipliers_df()
    freq_df = final.frequencies_df()
    bo_letter, final_avg = final.game.best_opener_misses(final.freq)

    # the fixed sets of bars shown (beat 3) and animated (beat 6)
    top_combos = mult_df.head(TRACK_N)
    top_words = freq_df.head(TRACK_N)
    combo_patterns = list(top_combos.pattern)
    word_list = list(top_words.word)

    beat3 = {
        "length": BO_LENGTH,
        "objective": OBJECTIVE,
        "best_opener_letter": bo_letter,
        "avg_misses": float(final_avg),
        "n_changes": int(n_changes),
        "top_words": [{"word": w, "frequency": float(f)}
                      for w, f in zip(top_words.word, top_words.frequency)],
        "top_combos": [{"pattern": p, "letter": l, "multiplier": float(m),
                        "n_words": int(n)}
                       for p, l, m, n in zip(top_combos.pattern, top_combos.letter,
                                             top_combos.multiplier, top_combos.n_words)],
    }

    # beat 6: 10 buckets. Snapshot the tracked bars + avg at each boundary,
    # 0 (uniform start) .. N_BUCKETS (final).
    def _avg_at(upto):
        if upto <= 0:
            s0 = _reconstruct(freq_search, 0)          # all multipliers 1 -> uniform
            return float(s0.game.best_opener_misses(s0.freq)[1])
        return float(log.iloc[upto - 1]["avg_misses"])  # avg after applying change upto-1

    buckets = []
    for i in range(N_BUCKETS + 1):
        upto = round(i * n_changes / N_BUCKETS)
        s = _reconstruct(freq_search, upto)
        m_by_pat = dict(zip(s.multipliers_df().pattern, s.multipliers_df().multiplier))
        f_by_word = dict(zip(s.frequencies_df().word, s.frequencies_df().frequency))
        buckets.append({
            "bucket": i,
            "upto": int(upto),
            "avg_misses": _avg_at(upto),
            "combo_mult": [float(m_by_pat[p]) for p in combo_patterns],
            "word_freq": [float(f_by_word[w]) for w in word_list],
        })
    beat6 = {"tracked_combos": combo_patterns, "tracked_words": word_list,
             "buckets": buckets}

    # beats 4/5: an illustrative accepted change (raises misses) and a perturbation
    # off the converged optimum (lowers misses -> undo).
    beat4 = _example_accepted(log)
    beat5 = _example_perturbation(freq_search, final, mult_df)
    return beat3, beat6, beat4, beat5


def _example_accepted(log):
    """One accepted combo change from the log (raises misses -> keep). Default: the
    single change with the biggest avg jump (FLAG: BEAT4_SEQ to pin a specific one)."""
    prev = log["avg_misses"].shift(1)
    prev.iloc[0] = None                       # first row's "before" filled below
    jumps = (log["avg_misses"] - prev)
    seq = int(BEAT4_SEQ) if BEAT4_SEQ is not None else int(jumps.iloc[1:].idxmax())
    row = log.iloc[seq]
    before = float(log.iloc[seq - 1]["avg_misses"]) if seq > 0 else None
    return {"seq": seq, "pattern": row["pattern"], "letter": row["letter"],
            "move": row["move"], "multiplier": float(row["multiplier"]),
            "before_avg": before, "after_avg": float(row["avg_misses"])}


def _example_perturbation(freq_search, final, mult_df):
    """At the converged optimum ANY change lowers the adversary's misses. Show one:
    double a tracked combo's multiplier and re-score (FLAG: BEAT5_PATTERN)."""
    pat = BEAT5_PATTERN if BEAT5_PATTERN is not None else mult_df.iloc[0]["pattern"]
    k = final.pattern.index(pat)
    base_mult = float(final.mult[k])
    base_avg = float(final.game.best_opener_misses(final.freq)[1])
    final.mult[k] = base_mult * 2.0
    final._recompute_freq()
    worse_avg = float(final.game.best_opener_misses(final.freq)[1])
    final.mult[k] = base_mult                 # restore
    final._recompute_freq()
    return {"pattern": pat, "base_multiplier": base_mult,
            "perturbed_multiplier": base_mult * 2.0,
            "base_avg": base_avg, "worse_avg": worse_avg}


def build():
    freq_search, strategy_view, wordlist = _imports()

    most_misses = _most_misses(strategy_view)
    beat3, beat6, beat4, beat5 = _choosing_strategy(freq_search)

    data = {
        "meta": {"min_zipf": wordlist.DEFAULT_ZIPF, "track_n": TRACK_N,
                 "n_buckets": N_BUCKETS},
        "most_misses": most_misses,      # beat 1
        "beat2": BEAT2,                   # pointer to tree2_data.py
        "choosing": beat3,               # beat 3 (final state)
        "example_keep": beat4,           # beat 4
        "example_undo": beat5,           # beat 5
        "optimization": beat6,           # beat 6 (10 buckets)
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
    print(f"[beat1] hardest words under optimal ({mm['weighting']}): "
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
    print(f"\n[beat3] length-{ch['length']} best-opener choosing strategy: "
          f"avg misses {ch['avg_misses']:.2f} (opener {ch['best_opener_letter']!r}), "
          f"{ch['n_changes']} accepted changes")
    print(f"        top words:  " +
          ", ".join(f"{w['word']}({w['frequency']:g})" for w in ch["top_words"][:5]))
    print(f"        top combos: " +
          ", ".join(f"{c['pattern']}(x{c['multiplier']:g})" for c in ch["top_combos"][:5]))

    k = data["example_keep"]
    print(f"\n[beat4] keep: combo {k['pattern']!r} {k['move']} -> x{k['multiplier']:g}, "
          f"avg {k['before_avg']:.4f} -> {k['after_avg']:.4f} (up, kept)")
    u = data["example_undo"]
    print(f"[beat5] undo: combo {u['pattern']!r} x{u['base_multiplier']:g} -> "
          f"x{u['perturbed_multiplier']:g}, avg {u['base_avg']:.4f} -> "
          f"{u['worse_avg']:.4f} (down, undone)")

    opt = data["optimization"]
    print(f"\n[beat6] {len(opt['buckets'])} snapshots (0=uniform .. {m['n_buckets']}=final); "
          f"avg misses per bucket:")
    print("        " +
          "  ".join(f"{b['avg_misses']:.3f}" for b in opt["buckets"]))

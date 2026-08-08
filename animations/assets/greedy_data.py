"""Cached pipeline numbers for scene 04 (the greedy strategy).

Every number scene 04 puts on screen is SOURCED here from the shared math
pipeline and persisted to the committed ``greedy_cache.json`` — the house pattern
(see ``letter_heat_data.py``): the data module imports the solver/helpers, the
scene reads only the cache, and the render path never touches ``math/``.

Sources (all already in the pipeline — nothing is invented here):
  - greedy walk / per-node candidate sets + next guess : ``strategy.GreedyGame``
      (``.state(board, missed)`` for a node, ``.trace(word)`` for a full game,
       ``.average_misses()`` for the headline metric)
  - the per-node frequency "bar graph" = # of the node's remaining candidate
      words that contain each un-guessed letter (greedy's OWN selection metric,
      ``f[S] @ present[S]`` under uniform freq; recomputed here from the candidate
      strings so the cache is self-contained)
  - E position-patterns (beat q, "letter combinations involving E") :
      ``letter_patterns.pattern_frequencies``
  - the PIRATES insertion chain (beat p) : literal from the script; membership in
      the game list is checked against ``wordlist.load``
  - length-17 words + their i-positions (beats t/u) : ``wordlist.load``

Regenerate with ``build()`` (or ``python3 greedy_data.py``) whenever the wordlist
or a computation changes. The render path only calls ``get()``.

FLAGS (values a human still owns — see the module-level constants):
  - ``MONTAGE_WORDS`` — which 3-letter words the beat-a montage shows. A curated
    illustrative sample (must include some LOSSES to justify the red result); the
    greedy result of each is computed, but the SET is a content choice — swap it.
  - beat q's "letter combinations involving E" is read as E's distinct POSITION-
    patterns (where the E can sit), 3-letter vs 12-letter. If you meant adjacency
    n-grams instead, say so and this section changes.
"""
from pathlib import Path
from collections import Counter
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "greedy_cache.json"
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# word length whose greedy game is walked in detail (beats c–n)
WALK_LEN = 3
# lengths for the avg-misses-by-length chart (beat o)
CHART_LENS = list(range(1, 21))
# the two lengths compared for E's position-patterns (beat q)
E_COMBO_LENS = (3, 12)
# the 17-letter word played out in beat v
DEMO_WORD_17 = "constitutionality"

# ── FLAG: the beat-a montage words (a curated content choice — swap freely) ────
# A spread of common 3-letter words; their greedy win/loss falls out of the trace.
MONTAGE_WORDS = ["cat", "dog", "run", "you", "the", "ice", "fox", "jam"]

# the single-letter-insertion chain built in beat p (literal from the script)
PIRATES_CHAIN = ["a", "at", "rat", "rate", "irate", "pirate", "pirates"]

_MISS_BUDGET = 6   # a game is LOST once misses exceed the 6-part hangman


# ── build ─────────────────────────────────────────────────────────────────────
def _imports():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import strategy
    import letter_patterns
    import wordlist
    return strategy, letter_patterns, wordlist


def _node(g, board, missed):
    """One greedy-tree node's display data, sourced from ``g.state``.

    Returns board/missed, candidate count ``n``, greedy's next ``guess`` and the
    share of candidates it hits, plus ``bars`` = every un-guessed letter with the
    number of remaining candidate words that contain it (descending) — the
    frequency bar graph, which is exactly greedy's selection metric.
    """
    st = g.state(board, missed)
    cand = st["candidates"]
    n = st["n"]
    guessed = {c for c in board if c != "_"} | set(missed)
    counts = Counter()
    for w in cand:
        for ch in set(w):
            counts[ch] += 1
    bars = sorted(((ch, counts[ch]) for ch in ALPHABET
                   if ch not in guessed and counts[ch] > 0),
                  key=lambda x: (-x[1], x[0]))
    guess = st["guess"]
    pick_count = counts[guess] if guess else None
    return {
        "board": st["board"],
        "missed": list(st["missed"]),
        "n": int(n),
        "determined": bool(st["determined"]),
        "reachable": bool(st["reachable"]),
        "guess": guess,
        "pick_count": (int(pick_count) if pick_count is not None else None),
        "pick_frac": (pick_count / n if (guess and n) else None),
        "bars": [[ch, int(c)] for ch, c in bars],
        "candidates_sample": cand[:12],
    }


def _greedy_result(strategy_mod, g, word):
    """The finished greedy game for one word, as the montage DISPLAYS it (beat a).

    Greedy plays to the end (no cap), but a real game STOPS at the 6th miss, so
    the shown board depends on win/loss:
      win  (<=6 misses) : the full word, the drawn body parts = #misses, all misses
      loss ( >6 misses) : the word as revealed WHEN the 6th miss lands (partial),
                          a full 6-part hangman, and the 6 misses shown below.
    ``board`` is a length-``len(word)`` string with ``_`` for still-blank slots;
    ``n_parts``/``shown_misses`` are what the hangman + miss-row show."""
    seq = g.trace(word)
    n_misses = sum(1 for _, hit in seq if not hit)
    win = n_misses <= _MISS_BUDGET

    # replay the trace, revealing hit letters, stopping a loss at the 6th miss
    revealed = ["_"] * len(word)
    shown_misses, miss_count = [], 0
    for ltr, hit in seq:
        if hit:
            for p, c in enumerate(word):
                if c == ltr:
                    revealed[p] = ltr
        else:
            miss_count += 1
            shown_misses.append(ltr)
            if not win and miss_count == _MISS_BUDGET:
                break
    return {
        "word": word,
        "trace": [[ltr, bool(hit)] for ltr, hit in seq],
        "n_misses": n_misses,
        "win": win,
        "board": "".join(revealed),
        "n_parts": (n_misses if win else _MISS_BUDGET),
        "shown_misses": shown_misses,
    }


def build():
    strategy, letter_patterns, wordlist = _imports()

    g3 = strategy.GreedyGame(WALK_LEN)
    n_len = g3.N

    # beat a — the montage of finished greedy games
    montage = []
    idx3 = set(g3.words)
    for w in MONTAGE_WORDS:
        if w not in idx3:
            print(f"  [montage] skip {w!r}: not a length-{WALK_LEN} game word")
            continue
        montage.append(_greedy_result(strategy, g3, w))

    # beats c–n — the A-branch greedy walk (root + the followed nodes)
    root = _node(g3, "_" * WALK_LEN, "")
    root["outcomes"] = [
        {"letter": o["letter"], "hit": bool(o["hit"]),
         "board": o["board"], "n": int(o["n"])}
        for o in g3.state("_" * WALK_LEN, "")["outcomes"]
    ]

    # the hit branches shown one per beat (d–g) + the A-absent miss chain (h–n)
    walk = [
        _node(g3, "_aa", ""),                 # d : two A's -> BAA (determined -> B)
        _node(g3, "__a", ""),                 # e : ends in A -> E
        _node(g3, "a__", ""),                 # f : starts with A -> E
        _node(g3, "_a_", ""),                 # g : lone middle A -> P
        _node(g3, "___", "a"),                # h : A absent -> O
        _node(g3, "___", "ao"),               # i : O miss -> E
        _node(g3, "___", "aoe"),              # j : E miss -> I
        _node(g3, "___", "aoei"),             # k : I miss -> U
        _node(g3, "___", "aoeiu"),            # l : U miss -> Y
        _node(g3, "___", "aoeiuy"),           # m/n : Y miss -> determined (nth)
    ]

    # beat o — headline avg misses by length (greedy, uniform), no miss cap
    avg_by_len = {}
    for L in CHART_LENS:
        gL = strategy.GreedyGame(L)
        if gL.N == 0:
            continue
        avg_by_len[str(L)] = {"avg_misses": float(gL.average_misses()),
                              "n_words": int(gL.N)}

    # beat p — the PIRATES insertion chain (literal; check game-list membership)
    in_list = {w.text for w in wordlist.load()}
    pirates = [{"word": w, "in_list": (w in in_list)} for w in PIRATES_CHAIN]

    # beat q — E's distinct position-patterns, 3-letter vs 12-letter words
    e_combos = {}
    for L in E_COMBO_LENS:
        df = letter_patterns.pattern_frequencies(L)
        empty = "_" * L
        rows = df[(df.letter == "e") & (df.pattern != empty)]
        rows = rows.sort_values("count", ascending=False)
        e_combos[str(L)] = {
            "n_patterns": int(len(rows)),
            "n_words": int(df.attrs["n_words"]),
            "patterns": [[p, int(c)] for p, c in zip(rows.pattern, rows["count"])],
        }

    # beats t/u — every length-17 word + its i-positions
    w17 = [w.text for w in wordlist.load(min_len=17, max_len=17)]
    len17 = {
        "n": len(w17),
        "words": [{"word": w, "i_positions": [i for i, c in enumerate(w) if c == "i"]}
                  for w in w17],
        "all_have_i": all("i" in w for w in w17),
        "i_positions_distinct":
            len({tuple(i for i, c in enumerate(w) if c == "i") for w in w17}) == len(w17),
    }

    # beat v — the constitutionality game (guess I first, then greedy)
    g17 = strategy.GreedyGame(17)
    demo = {"word": DEMO_WORD_17, "in_list": DEMO_WORD_17 in set(g17.words)}
    if demo["in_list"]:
        seq = g17.trace(DEMO_WORD_17, opener="i")
        demo["trace"] = [[ltr, bool(hit)] for ltr, hit in seq]
        demo["i_positions"] = [i for i, c in enumerate(DEMO_WORD_17) if c == "i"]
        demo["misses_before_determined"] = sum(1 for ltr, hit in seq if not hit)

    data = {
        "meta": {"weighting": "uniform", "min_zipf": wordlist.DEFAULT_ZIPF,
                 "walk_len": WALK_LEN, "n_walk_words": int(n_len)},
        "montage": montage,
        "root": root,
        "walk": walk,
        "avg_misses_by_length": avg_by_len,
        "pirates_chain": pirates,
        "e_combos": e_combos,
        "len17": len17,
        "constitutionality": demo,
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


# ── render-side accessors (read the committed cache; no computation) ───────────
def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return _load()


if __name__ == "__main__":
    data = build()
    m = data["meta"]
    print(f"wrote {CACHE.name}: {m['n_walk_words']} length-{m['walk_len']} words, "
          f"weighting {m['weighting']}, min_zipf {m['min_zipf']}\n")

    # provenance: print where each headline number comes from
    r = data["root"]
    top = r["bars"][0]
    print(f"[root] guess {r['guess']!r}: {top[1]}/{r['n']} words "
          f"({r['pick_frac']*100:.1f}%)   <- GreedyGame(3).state('___')")
    print(f"[root] 5 outcomes: " +
          ", ".join(f"{o['board']}={o['n']}" for o in r["outcomes"]))
    labels = ["_AA->", "__A->", "A__->", "_A_->",
              "absent->", "O miss->", "E miss->", "I miss->", "U miss->", "Y miss->"]
    for lab, nd in zip(labels, data["walk"]):
        if nd["determined"]:
            print(f"[walk] {lab:9s} determined: {nd['candidates_sample']}")
        else:
            print(f"[walk] {lab:9s} guess {nd['guess']!r}  "
                  f"{nd['pick_count']}/{nd['n']} = {nd['pick_frac']*100:.1f}%")

    print("\n[chart] avg misses by length (greedy, uniform):")
    peak = max(data["avg_misses_by_length"].items(),
               key=lambda kv: kv[1]["avg_misses"])
    for L, v in data["avg_misses_by_length"].items():
        star = "  <- PEAK" if L == peak[0] else ""
        print(f"   len {int(L):2d}: {v['avg_misses']:.3f}  "
              f"({v['n_words']} words){star}")

    print("\n[montage] greedy results:")
    for r in data["montage"]:
        tag = "WIN " if r["win"] else "LOSS"
        print(f"   {r['word']}  {tag}  {r['n_misses']} misses  "
              f"board={r['board']}  shown_misses={''.join(r['shown_misses'])}")

    print("\n[pirates] " +
          " -> ".join(f"{p['word']}{'' if p['in_list'] else '(*)'}"
                      for p in data["pirates_chain"]) +
          "   (* = not in game list)")

    ec = data["e_combos"]
    for L in ("3", "12"):
        print(f"[e-combos] len {L}: {ec[L]['n_patterns']} distinct E-patterns "
              f"over {ec[L]['n_words']} words")

    l17 = data["len17"]
    print(f"\n[len17] {l17['n']} words; all have an i: {l17['all_have_i']}; "
          f"i-positions distinct across all: {l17['i_positions_distinct']}")

    d = data["constitutionality"]
    if d.get("in_list"):
        print(f"[len17] {d['word']}: i at {d['i_positions']}, "
              f"{d['misses_before_determined']} misses guessing i first")
    else:
        print(f"[len17] {d['word']!r} is NOT in the length-17 game list (*)")

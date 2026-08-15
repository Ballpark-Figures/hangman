"""Cached pipeline numbers for scene 03 (building the word list).

Every number scene 03 puts on screen is SOURCED here from the shared math
pipeline and persisted to the committed ``wordlist_cache.json`` — the house
pattern (see ``greedy_data.py``): the data module imports the pipeline, the scene
reads only the cache, and the render path never touches ``math/`` (so the render
needs no ``wordfreq``/``hunspell``).

Sources (nothing invented here):
  - the per-step COUNTER (post-cutoff / non-letter / hunspell / each removal
    category / add-backs / final 34,483) : ``math/wordlist_steps.compute`` — which
    reruns the real build pipeline (``wordfreq`` large → zipf≥2.5 cutoff →
    non-letter drop → hunspell → curated block/allow lists) and asserts the
    sequence reconciles to 34,483.
  - the top-N words + their %/rank (beats a/b/d) : raw ``wordfreq`` at the cutoff.
  - the words either side of the frequency cutoff (beat c) : raw ``wordfreq``
    around zipf 2.5, with a per-N ("1 in N") rate.
  - example "extras" (beat e) + the per-category example crossed off (beats f–q):
    picked from the pipeline (raw wordfreq / the category members), verified in
    scope — see EXAMPLES / the candidate lists below.
  - by-length distribution of the FINAL list (beat r) : ``wordlist.load``.

Regenerate with ``build()`` (or ``python3 wordlist_data.py``). The render path
only calls ``get()``.

FLAGS (content a human still owns — swap freely):
  - N_TOP — how many top words the beat-a columns show (~100 asked for).
  - EXAMPLES — the single example word shown for each removal category (beats
    e–q). Each is verified to be in that category / raw list; the CHOICE is
    illustrative. The profanity beat is a literal ``"$#@%"`` placeholder (the
    script wants random characters, not a real slur).
  - PROPER_CANDIDATES — the lowercased proper nouns tried for the "extras" proper
    noun (beat e) and the spellchecker non-word (beat g); the first two valid,
    distinct ones are used.
"""
from pathlib import Path
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "wordlist_cache.json"

# ── FLAGS (content choices) ───────────────────────────────────────────────────
# Every flag here is a CONTENT choice that must SERVE its beat's VOICEOVER (Script.md
# row 03, column 1), not just column 2's mechanic — each cites the clause it serves
# so a future edit can't drift from the point (see bpkfigures/CLAUDE.md "A CONTENT
# choice … is governed by the beat's VOICEOVER").

# beat a — VOICEOVER: "a list of words that roughly simulated a typical person's
# vocabulary." column 2: "Fill screen with columns of words sorted by zipf, starting
# with 'the'." So: the TOP words of the FINAL list, most-common first.
N_TOP = 80           # top FINAL-list words in the beat-a columns (5 cols × 16)

# beat c — a SELECTION of words tied EXACTLY at the frequency cutoff (all at zipf
# 2.50 are IN the list at one shared rank/freq; all at 2.49 are DROPPED at another).
# Every word is verified to sit at the right zipf at build. 6 per side (keeps the
# column clear of the board edges).
#   SCRIPT INTENT (Script.md row 03, column 1 / voiceover): "I tried to find a
#   frequency cutoff where I KNEW ABOUT HALF of the words near the cutoff." So this
#   SELECTION must read as ~HALF FAMILIAR, ~HALF OBSCURE — NOT all recognizable
#   (that silently breaks the beat's whole point). Current split is 3 familiar / 3
#   obscure per side; keep that balance when swapping words.
CUTOFF_ABOVE = ["abbess", "airmail", "defrost", "laminar", "phylogeny",
                "seahorse"]              # zipf 2.50, IN the list (3 familiar/3 obscure)
CUTOFF_BELOW = ["bijou", "cookout", "iguanas", "oriel", "semiotics",
                "warthog"]               # zipf 2.49, DROPPED (3 familiar/3 obscure)

# beats e–q — the ONE example word shown + crossed off per removal category. column
# 2 walks the categories ("Show bldg", "Show p", "Same for X"); the VOICEOVER lists
# them ("abbreviations … single letters … Initialisms … Roman numerals …"). SCRIPT
# INTENT: each example must be a CLEAR, RECOGNISABLE instance of its category so the
# audience instantly gets why it's junk (bldg/p/pi/styrofoam are script-named; the
# rest are illustrative but must still be obviously-that-category), verified in scope.
EXAMPLES = {
    "abbreviations": "bldg",     # script-named: "Playing BLDG in hangman…"
    "single letters": "p",       # script-named: "Show p"
    "initialisms": "mph",        # an obvious initialism
    "roman numerals": "xiv",     # an obvious roman numeral
    "interjections": "hmm",      # an obvious interjection
    "profanity": "#*%!",         # script: "a string of random characters", NOT a slur
    "greek letters": "phi",      # a greek-letter NAME that IS removed (pi is kept)
    "disagree_down": "morocco",  # proper noun HUNSPELL KEPT but we removed ("adding
                                 # and removing … where I disagreed with the spellchecker")
}
# beat e ("a proper noun") + beat g ("a non-word the spellchecker removes"): proper
# nouns HUNSPELL REJECTS. Must read as an OBVIOUS proper noun; first valid one used.
PROPER_CANDIDATES = ["chicago", "america", "john", "london", "france", "monday",
                     "google", "paris", "boston", "canada"]

# beat e ("a word with an apostrophe") + beat f (the non-letter cross-off): an
# apostrophe word wordfreq KEEPS but the non-letter drop REMOVES. Verified at build
# to be handled exactly like any apostrophe word (in wordfreq @ cutoff, has "'", not
# all-letters → dropped by the non-letter filter).
APOSTROPHE_EX = "don't"


def _imports():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import wordlist
    import wordlist_steps
    from wordfreq import get_frequency_dict, zipf_frequency
    return wordlist, wordlist_steps, get_frequency_dict, zipf_frequency


def build():
    wordlist, wordlist_steps, get_frequency_dict, zipf_frequency = _imports()
    from spylls.hunspell import Dictionary
    speller = Dictionary.from_files("en_US")

    steps = wordlist_steps.compute()
    cutoff = steps["cutoff"]
    zf = lambda w: zipf_frequency(w, "en", wordlist="large")
    pct = lambda z: 10.0 ** (z - 7.0)                 # % of all English text
    per_n = lambda z: round(10.0 ** (9.0 - z))        # ~1 appearance per N words

    # the PREPROCESSED list — raw wordfreq @ zipf>=cutoff, most-common first
    # (~53,572 words, = anchors["start"], BEFORE hunspell/curation). This is the
    # list the frequency cutoff is drawn on, so the cutoff-region RANKS (beats c/d)
    # are positions in HERE, not the final curated 34,483.
    freqs = get_frequency_dict("en", wordlist="large")
    ranked = sorted(((w, zf(w)) for w in freqs if zf(w) >= cutoff),
                    key=lambda wz: -wz[1])

    # beats a/b — the top-N words that ACTUALLY END UP in our list (the final,
    # curated list in frequency order), with their % of English text (full float
    # precision; the scene rounds to 2 significant figures).
    final = wordlist.load(min_zipf=cutoff)
    top_words = [{"word": w.text, "zipf": round(w.zipf, 2), "pct": pct(w.zipf),
                  "rank": i + 1}
                 for i, w in enumerate(final[:N_TOP])]

    # beat c/d — words tied EXACTLY at the frequency cutoff. wordfreq quantizes zipf
    # to 2 decimals, so ~hundreds tie at 2.50 (the lowest freq IN the list) and at
    # 2.49 (the highest DROPPED). Tied words share ONE rank + ONE frequency: the
    # in-list side gets the COMPETITION rank of that tie block (final − |tie| + 1),
    # the dropped side gets final + 1. All are verified to sit at the right zipf.
    zof = {w.text: w.zipf for w in wordlist._raw()}
    for w in CUTOFF_ABOVE:
        assert zof.get(w) == cutoff, f"{w!r} not at zipf {cutoff} (got {zof.get(w)})"
    for w in CUTOFF_BELOW:
        assert zof.get(w) == round(cutoff - 0.01, 2), \
            f"{w!r} not at zipf {cutoff - 0.01} (got {zof.get(w)})"
    # RANKS ARE ON THE ORIGINAL PREPROCESSED LIST — raw wordfreq @ zipf>=cutoff
    # (`ranked`, = anchors["start"] ≈ 53,572, BEFORE hunspell/curation) — NOT the
    # final curated 34,483, because the frequency cutoff is drawn on THAT list.
    # wordfreq quantises zipf to 2 dp, so words tie at 2.50 (least common still IN)
    # and 2.49 (first ones CUT). Competition ranking: a tie block shares the rank
    # just past everything strictly more common, so the 2.50 block sits at the very
    # bottom of the preprocessed list and the 2.49 block is the first one over the edge.
    below_cut = round(cutoff - 0.01, 2)
    n_pre = len(ranked)                                    # preprocessed list size
    assert n_pre == steps["anchors"]["start"], (n_pre, steps["anchors"]["start"])
    n_at_cut = sum(1 for _w, z in ranked if round(z, 2) == cutoff)
    n_below = sum(1 for w in freqs if round(zf(w), 2) == below_cut)
    above_rank = n_pre - n_at_cut + 1        # shared rank of the last tie block IN (kept)
    below_rank = n_pre + 1                    # shared rank of the first tie block OUT (cut)
    cutoff_region = {
        "list": "preprocessed", "n_list": n_pre,
        "n_at_cutoff": n_at_cut, "n_below_cutoff": n_below,
        "above": [{"word": w, "pct": pct(cutoff), "rank": above_rank}
                  for w in CUTOFF_ABOVE],
        "below": [{"word": w, "pct": pct(cutoff - 0.01), "rank": below_rank}
                  for w in CUTOFF_BELOW],
    }

    # beat e — example "extras" wordfreq wrongly includes
    valid_proper = [w for w in PROPER_CANDIDATES
                    if zf(w) >= cutoff and w.isalpha() and not speller.lookup(w)]
    assert len(valid_proper) >= 2, f"need 2 proper-noun examples, got {valid_proper}"
    # the apostrophe example must be handled EXACTLY like any apostrophe word: kept by
    # wordfreq at the cutoff, has a "'", and is NOT all-letters (so the non-letter drop
    # removes it). (wordfreq has no hyphenated tokens above the cutoff, so the script's
    # "word with a hyphen" example can't be sourced — the apostrophe covers non-letter.)
    assert (APOSTROPHE_EX in freqs and zf(APOSTROPHE_EX) >= cutoff
            and "'" in APOSTROPHE_EX
            and not (APOSTROPHE_EX.isascii() and APOSTROPHE_EX.isalpha())), \
        f"{APOSTROPHE_EX!r} is not an in-scope apostrophe word handled like the rest"
    extras = {
        "proper": valid_proper[0],
        "abbr": "etc",
        "roman": "xiv",
        "apostrophe": APOSTROPHE_EX,
    }
    assert all(extras.values()), f"missing an extras example: {extras}"

    # the per-step COUNTER, in the video's narrated order. Example words verified
    # to be in their category's members (single letters/greek/… come from compute).
    members = {c["name"]: set(c["members"]) for c in steps["categories"]}
    a = steps["anchors"]
    counter = [{"key": "start", "label": "wordfreq", "value": a["start"]}]
    n = a["start"]

    def add(key, label, delta, value, example, *, up=False):
        counter.append({"key": key, "label": label,
                        "delta": (delta if up else -delta), "value": value,
                        "example": example})

    apostrophe_word = extras["apostrophe"]
    spell_nonword = extras["proper"]     # the SAME proper noun previewed in beat e
    add("non_letter", "drop non-letter characters", steps["deltas"]["non_letter"],
        a["non_letter"], apostrophe_word)
    add("hunspell", "spellcheck", steps["deltas"]["hunspell"], a["hunspell"],
        spell_nonword)
    n = a["hunspell"]
    for c in steps["categories"]:
        ex = EXAMPLES[c["name"]]
        if c["name"] != "profanity":     # the profanity example is a placeholder
            assert ex in members[c["name"]], \
                f"example {ex!r} not in {c['name']} members"
        n -= c["count"]
        entry = {"key": c["name"].replace(" ", "_"), "label": c["name"],
                 "delta": -c["count"], "value": n, "example": ex}
        if c["name"] == "greek letters":
            # narrative: drop 1 FURTHER (as if pi were removed too), then pi ✓ +1
            entry["fake_extra"] = 1
            entry["pi_example"] = "pi"
        counter.append(entry)
    # final beat — "disagreed with the spellchecker": up (add-backs), then down
    assert "styrofoam" in steps["addbacks"]
    n += len(steps["addbacks"])
    counter.append({"key": "disagree_up", "label": "add-backs",
                    "delta": len(steps["addbacks"]), "value": n,
                    "example": "styrofoam",
                    "all_addbacks": steps["addbacks"]})
    down_ex = EXAMPLES["disagree_down"]
    assert down_ex in steps["proper_down"]["members"], \
        f"disagree_down {down_ex!r} is not a hunspell-kept, hand-removed word"
    n -= steps["proper_down"]["count"]
    counter.append({"key": "disagree_down", "label": "removals",
                    "delta": -steps["proper_down"]["count"], "value": n,
                    "example": down_ex})
    assert n == 34483, f"counter reconcile failed: {n}"

    # beat r — by-length distribution of the FINAL list
    final_words = wordlist.load(min_zipf=cutoff)
    from collections import Counter
    by_len_c = Counter(len(w.text) for w in final_words)
    by_length = [{"length": L, "count": by_len_c.get(L, 0)}
                 for L in range(1, max(by_len_c) + 1)]
    assert sum(b["count"] for b in by_length) == 34483

    data = {
        "meta": {"cutoff": cutoff, "n_top": N_TOP, "final": 34483,
                 "wordfreq_list": "large"},
        "anchors": a,
        "counter": counter,
        "top_words": top_words,
        "cutoff_region": cutoff_region,
        "extras": extras,
        "by_length": by_length,
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return _load()


if __name__ == "__main__":
    d = build()
    print(f"wrote {CACHE.name}\n")
    print("[counter] step -> value  (example crossed/added):")
    for s in d["counter"]:
        ex = f"   [{s.get('example')}]" if s.get("example") else ""
        dl = f"{s['delta']:+,}" if "delta" in s else "start"
        print(f"   {s['label']:<28} {dl:>8}  {s['value']:>7,}{ex}")
    print(f"\n[top {len(d['top_words'])}] first: "
          f"{', '.join(w['word'] for w in d['top_words'][:8])} …")
    t = d["top_words"][0]
    print(f"   #{t['rank']} {t['word']!r} = {t['pct']:.2f}% of English text")
    cr = d["cutoff_region"]
    print(f"[cutoff] {cr['n_at_cutoff']} tied IN @ rank {cr['above'][0]['rank']:,}; "
          f"{cr['n_below_cutoff']} tied OUT @ rank {cr['below'][0]['rank']:,}")
    print(f"   above: {', '.join(w['word'] for w in cr['above'])}")
    print(f"   below: {', '.join(w['word'] for w in cr['below'])}")
    print(f"[extras] {d['extras']}")
    bl = d["by_length"]
    peak = max(bl, key=lambda b: b["count"])
    print(f"[by_length] lengths 1..{bl[-1]['length']}, "
          f"peak len {peak['length']} = {peak['count']:,} words, "
          f"total {sum(b['count'] for b in bl):,}")

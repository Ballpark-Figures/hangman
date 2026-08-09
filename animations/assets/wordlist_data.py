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
N_TOP = 96           # top FINAL-list words in the beat-a columns (6 cols × 16)
N_CUTOFF = 7         # words shown on EACH side of the cutoff divider (beat c)

# per-category example word crossed off (beats e–q). bldg/p/pi/styrofoam are
# script-specified; the rest are illustrative picks, verified in scope at build.
EXAMPLES = {
    "abbreviations": "bldg",     # script: "Show bldg"
    "single letters": "p",       # script: "Show p"
    "initialisms": "mph",
    "roman numerals": "xiv",
    "interjections": "hmm",
    "profanity": "#*%!",         # script: random characters, NOT a real word
    "greek letters": "phi",      # a greek name that IS removed (pi is kept)
}
PROPER_CANDIDATES = ["america", "john", "london", "france", "monday", "google",
                     "paris", "chicago", "boston", "canada"]


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

    # raw wordfreq list at the cutoff, most-common first (rank = 1-based position);
    # used only to place the cutoff-region words on the ~54,000 boundary.
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

    # beat c/d — REAL words straddling the frequency cutoff (raw wordfreq near the
    # cutoff is mostly junk — emoji, numbers, proper nouns — so we show curated
    # master-list words the viewer can actually evaluate "do I know about half?").
    # Each carries its rank in the FULL raw wordfreq list (so the rank lands near
    # the ~53,572 boundary) and a "1 in N" rate. rank crosses ~54,000 at the line.
    full_rank = {w: i + 1 for i, (w, _z)
                 in enumerate(sorted(((w, zf(w)) for w in freqs), key=lambda wz: -wz[1]))}
    master = [(w.text, w.zipf) for w in wordlist._raw()]      # curated real words + zipf
    # An evenly-spaced alphabetical SAMPLE of the real words just above / just below
    # the cutoff (hundreds tie at zipf 2.50, so this reads as a varied cross-section
    # rather than a run of one letter). All are within a hair of the frequency line.
    def _spread(band, k):
        band = sorted(band)                       # alphabetical
        if len(band) <= k:
            return band
        return [band[round(i * (len(band) - 1) / (k - 1))] for i in range(k)]
    above_m = _spread([wz for wz in master if cutoff <= wz[1] < cutoff + 0.05], N_CUTOFF)
    below_m = _spread([wz for wz in master if cutoff - 0.05 <= wz[1] < cutoff], N_CUTOFF)
    cutoff_region = {
        "boundary_rank": len(ranked),           # ~53,572 -> "about 54,000"
        "above": [{"word": w, "per_n": per_n(z), "pct": pct(z), "rank": full_rank[w]}
                  for w, z in above_m],
        "below": [{"word": w, "per_n": per_n(z), "pct": pct(z), "rank": full_rank[w]}
                  for w, z in below_m],
    }

    # beat e — example "extras" wordfreq wrongly includes
    def _highest(pred):
        for w, _z in ranked:
            if pred(w):
                return w
        return None
    valid_proper = [w for w in PROPER_CANDIDATES
                    if zf(w) >= cutoff and w.isalpha() and not speller.lookup(w)]
    assert len(valid_proper) >= 2, f"need 2 proper-noun examples, got {valid_proper}"
    # NOTE: wordfreq has NO hyphenated tokens above the cutoff, so the script's
    # "word with a hyphen" example can't be sourced; the apostrophe example covers
    # the non-letter case, so the hyphen slot is simply dropped (per the user).
    extras = {
        "proper": valid_proper[0],
        "abbr": "etc",
        "roman": "xiv",
        "apostrophe": _highest(lambda w: "'" in w),
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
    down_ex = EXAMPLES.get("disagree_down", steps["proper_down"]["members"][0])
    down_ex = "panama" if "panama" in steps["proper_down"]["members"] else \
        steps["proper_down"]["members"][0]
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
    print(f"[cutoff] boundary rank {cr['boundary_rank']:,} (~54,000); "
          f"above: {', '.join(w['word'] for w in cr['above'][-4:])} | "
          f"below: {', '.join(w['word'] for w in cr['below'][:4])}")
    print(f"   near-cutoff rate ~1 in {cr['above'][-1]['per_n']:,}")
    print(f"[extras] {d['extras']}")
    bl = d["by_length"]
    peak = max(bl, key=lambda b: b["count"])
    print(f"[by_length] lengths 1..{bl[-1]['length']}, "
          f"peak len {peak['length']} = {peak['count']:,} words, "
          f"total {sum(b['count'] for b in bl):,}")

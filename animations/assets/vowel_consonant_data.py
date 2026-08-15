"""Cached vowel/consonant statistics for scene 08.

All UNWEIGHTED (each word counts once) over the curated wordlist at the default zipf
cutoff — the same wordlist / convention as the letter position-frequency heatmaps.
Vowels = A E I O U Y (Y ALWAYS a vowel, per the scene's script). Sourced from the
shared pipeline: aggregate + adjacency counts read `wordlist.load`; the red/blue
position grid reuses `letter_patterns.position_share` (summed over the vowels).

House pattern: numbers are cached in the committed `vowel_consonant_cache.json` so a
render needs no wordlist import. Regenerate with `build()` (or `python3
vowel_consonant_data.py`, which also PRINTS every number + its definition for review)
whenever the wordlist or the computation changes. The render path only calls `get()`.

Keys in the cache:
  pct_vowel_letters      vowel letter-instances / all letter-instances
  pct_start_consonant    words whose FIRST letter is a consonant / all words
  pct_end_consonant      words whose LAST letter is a consonant / all words
  pct_pos2_vowel         words (len>=2) with a vowel in position 2 / such words
  adjacency[cls][side]   for cls in {vowel, consonant}, side in {after, before}:
                         the {vowel, consonant} split of the NEXT (after) / PREVIOUS
                         (before) letter, given the current letter is `cls` and is not
                         at the corresponding word boundary. e.g.
                         adjacency.vowel.after.consonant = P(next is consonant | the
                         current letter is a vowel and not word-final).
  grid[L]                length L in 2..10: per-position fraction that is a VOWEL
                         (blue->red heatmap scale; consonant fraction = 1 - this)
  avg_vowels[L]          length L in 2..10: mean number of VOWELS per length-L word
                         (== sum of grid[L] by linearity of expectation)
  avg_consonants[L]      length L in 2..10: mean number of CONSONANTS = L - avg_vowels[L]
"""
from pathlib import Path
from collections import defaultdict
import json
import sys

VOWELS = "aeiouy"
GRID_LENGTHS = list(range(2, 11))                 # 2..10, like the letter heatmaps
_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "vowel_consonant_cache.json"


def _frac(a, b):
    return round(a / b, 4) if b else 0.0


def build():
    """Compute every statistic from the wordlist and write the cache."""
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import wordlist
    import letter_patterns

    vowels = set(VOWELS)
    words = [w.text for w in wordlist.load(min_zipf=wordlist.DEFAULT_ZIPF)]

    total_letters = vowel_letters = 0
    n_words = start_cons = end_cons = 0
    pos2_total = pos2_vowel = 0
    # per-length vowel-count totals -> mean vowels/consonants per word of that length
    len_words = defaultdict(int)
    len_vowel_sum = defaultdict(int)
    # adjacency counts: acc[cls][side] = {"v":…, "c":…} counts of the neighbour class
    acc = {c: {"after": {"v": 0, "c": 0}, "before": {"v": 0, "c": 0}}
           for c in ("v", "c")}

    for t in words:
        n_words += 1
        for ch in t:
            total_letters += 1
            if ch in vowels:
                vowel_letters += 1
        if t[0] not in vowels:
            start_cons += 1
        if t[-1] not in vowels:
            end_cons += 1
        if len(t) >= 2:
            pos2_total += 1
            if t[1] in vowels:
                pos2_vowel += 1
        L = len(t)
        if L in GRID_LENGTHS:
            len_words[L] += 1
            len_vowel_sum[L] += sum(1 for ch in t if ch in vowels)
        for i, ch in enumerate(t):
            cls = "v" if ch in vowels else "c"
            if i < L - 1:
                acc[cls]["after"]["v" if t[i + 1] in vowels else "c"] += 1
            if i > 0:
                acc[cls]["before"]["v" if t[i - 1] in vowels else "c"] += 1

    adjacency = {}
    for cls, name in (("v", "vowel"), ("c", "consonant")):
        adjacency[name] = {}
        for side in ("after", "before"):
            v, c = acc[cls][side]["v"], acc[cls][side]["c"]
            adjacency[name][side] = {"vowel": _frac(v, v + c),
                                     "consonant": _frac(c, v + c)}

    grid = {}
    avg_vowels, avg_consonants = {}, {}
    for Ln in GRID_LENGTHS:
        shares, _n = letter_patterns.position_share(Ln)
        grid[str(Ln)] = [round(sum(shares[v][p] for v in vowels), 4)
                         for p in range(Ln)]
        av = _frac(len_vowel_sum[Ln], len_words[Ln])   # mean vowels / length-Ln word
        avg_vowels[str(Ln)] = av
        avg_consonants[str(Ln)] = round(Ln - av, 4)

    data = {
        "weighting": "uniform",
        "min_zipf": wordlist.DEFAULT_ZIPF,
        "vowels": VOWELS,
        "grid_lengths": GRID_LENGTHS,
        "n_words": n_words,
        "pct_vowel_letters": _frac(vowel_letters, total_letters),
        "pct_start_consonant": _frac(start_cons, n_words),
        "pct_end_consonant": _frac(end_cons, n_words),
        "pct_pos2_vowel": _frac(pos2_vowel, pos2_total),
        "adjacency": adjacency,
        "grid": grid,
        "avg_vowels": avg_vowels,
        "avg_consonants": avg_consonants,
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def get():
    """The whole cached stats dict (grid keys coerced back to int)."""
    d = json.loads(CACHE.read_text())
    d["grid"] = {int(k): v for k, v in d["grid"].items()}
    d["avg_vowels"] = {int(k): v for k, v in d["avg_vowels"].items()}
    d["avg_consonants"] = {int(k): v for k, v in d["avg_consonants"].items()}
    return d


if __name__ == "__main__":
    d = build()
    pct = lambda x: f"{100 * x:.1f}%"
    print(f"wrote {CACHE.name}: {d['n_words']} words, weighting {d['weighting']}, "
          f"min_zipf {d['min_zipf']}, vowels '{d['vowels']}'\n")
    print(f"  letters that are vowels        {pct(d['pct_vowel_letters'])}")
    print(f"  words starting with consonant  {pct(d['pct_start_consonant'])}")
    print(f"  words ending with consonant    {pct(d['pct_end_consonant'])}")
    print(f"  position 2 is a vowel          {pct(d['pct_pos2_vowel'])}")
    for name in ("vowel", "consonant"):
        for side in ("after", "before"):
            a = d["adjacency"][name][side]
            print(f"  {side:6s} a {name:9s}: vowel {pct(a['vowel'])}  "
                  f"consonant {pct(a['consonant'])}")
    print("\n  vowel-fraction grid (blue 0 -> red 1), by length:")
    for L in d["grid_lengths"]:
        print(f"    len {L:2d}: " + " ".join(f"{v:.2f}" for v in d["grid"][str(L)]))
    print("\n  mean vowels / consonants per word, by length "
          "(avg_vowels == sum of grid row):")
    for L in d["grid_lengths"]:
        av, ac = d["avg_vowels"][str(L)], d["avg_consonants"][str(L)]
        gsum = sum(d["grid"][str(L)])
        print(f"    len {L:2d}: vowels {av:.2f} (grid sum {gsum:.2f})  "
              f"consonants {ac:.2f}")

"""Generate the curated master hangman wordlist from the `wordfreq` package.

Run once (regenerate only if you want to change the floor or filters):

    .venv/bin/python math/build_wordlist.py

Writes ``data/wordlist_master.txt`` -- lines of ``word<TAB>zipf`` sorted by
descending frequency. ``zipf`` is wordfreq's Zipf scale: log10(occurrences per
billion words), so 3.0 == ~1 per million, 4.0 == ~10 per million. Higher =
more common. The Zipf value is kept in the file so the loader can apply the
"words players know" cutoff without regenerating (see wordlist.py).

Why wordfreq instead of raw Norvig: it's a curated multi-corpus list that
excludes most web junk (proper nouns, initialisms, code tokens, misspellings)
while KEEPING inflected forms (plurals, conjugations) -- exactly what we want.

wordfreq alone still leaks proper nouns/initialisms, because it lowercases
everything (so "Ares"/"Amtrak"/"ATC" become candidate words). We remove those
with a HUNSPELL spellcheck (the `spylls` pure-Python implementation, en_US
dictionary): a token is kept only if hunspell accepts it as-is. Because
hunspell dictionaries store case, a lowercase proper noun ("amtrak" vs the
stored "Amtrak") is rejected, as are abbreviations and misspellings ("qr",
"wierd"). Hunspell's affix rules accept regular inflections (plurals,
conjugations) by construction, so we keep those. Measured on this data the
filter leaves ~1% junk while cutting ~0.7% genuine words (British spellings,
days/demonyms, a few real words like "albedo").

Filters applied here:
  - lowercase ASCII a-z only (drops punctuation, digits, accents, "don't")
  - zipf >= FLOOR (a small buffer below the game cutoff, so the loader's
    cutoff can be loosened later without a rebuild)
  - accepted by hunspell (proper-noun / abbreviation / misspelling rejection)
"""

from __future__ import annotations

from pathlib import Path

from spylls.hunspell import Dictionary
from wordfreq import get_frequency_dict, zipf_frequency

# Store everything down to a buffer below the intended game cutoff, so the
# loader can tune the cutoff in either direction without regenerating.
FLOOR = 2.0
WORDLIST = "large"  # wordfreq's large English list (deeper tail than "small")

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT = DATA_DIR / "wordlist_master.txt"


def build() -> list[tuple[str, float]]:
    speller = Dictionary.from_files("en_US")
    freqs = get_frequency_dict("en", wordlist=WORDLIST)
    rows: list[tuple[str, float]] = []
    for word in freqs:
        if not (word.isascii() and word.isalpha() and word.islower()):
            continue
        if not speller.lookup(word):
            continue
        z = zipf_frequency(word, "en", wordlist=WORDLIST)
        if z < FLOOR:
            continue
        rows.append((word, z))
    # Descending frequency; alphabetical for equal-Zipf ties (stable, readable).
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


def main() -> None:
    rows = build()
    with OUT.open("w", encoding="utf-8") as fh:
        for word, z in rows:
            fh.write(f"{word}\t{z:.2f}\n")
    print(f"wrote {len(rows):,} words to {OUT}")
    # Provenance: how many survive at each candidate game cutoff.
    for cut in (4.0, 3.5, 3.0, 2.8, 2.5, 2.2, 2.0):
        n = sum(1 for _, z in rows if z >= cut)
        print(f"  zipf >= {cut}: {n:,} words")


if __name__ == "__main__":
    main()

"""Generate the curated master hangman wordlist from the `wordfreq` package.

Run once (regenerate only if you want to change the floor or the curated lists):

    .venv/bin/python math/build_wordlist.py

Writes ``data/wordlist_master.txt`` -- lines of ``word<TAB>zipf`` sorted by
descending frequency. ``zipf`` is wordfreq's Zipf scale: log10(occurrences per
billion words), so 3.0 == ~1 per million, 4.0 == ~10 per million. Higher =
more common. The Zipf value is kept in the file so the loader can apply the
"words players know" cutoff without regenerating (see wordlist.py).

Pipeline: wordfreq (frequency + inflections) -> Zipf floor -> a HUNSPELL
spellcheck (the `spylls` pure-Python implementation, en_US dictionary) -> two
hand-curated override lists:

  - data/blocklist.txt : junk hunspell WRONGLY keeps -- abbreviations, unit
    symbols, initialisms, roman numerals, and the single letters hunspell
    accepts (e.g. bbl, mph, kg, xiv, plus b..z). Removed.
  - data/allowlist.txt : real words hunspell WRONGLY drops (British spellings
    and a few genuine words like albedo/tsar). Force-kept.

A word is kept iff  (hunspell accepts it OR it's in the allowlist)  AND  it's
not in the blocklist. Hunspell does the bulk proper-noun removal; the curated
lists fix its specific failures (chiefly the junk-heavy short-length buckets).
"""

from __future__ import annotations

import sys
from pathlib import Path

from spylls.hunspell import Dictionary
from wordfreq import get_frequency_dict, zipf_frequency

# Store everything down to a buffer below the intended game cutoff, so the
# loader can tune the cutoff in either direction without regenerating.
FLOOR = 2.0
WORDLIST = "large"  # wordfreq's large English list (deeper tail than "small")

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT = DATA_DIR / "wordlist_master.txt"
BLOCKLIST_FILE = DATA_DIR / "blocklist.txt"
ALLOWLIST_FILE = DATA_DIR / "allowlist.txt"

# Dictionary VARIANTS. "us" is the original (en_US -> wordlist_master.txt). Others
# swap ONLY the hunspell dictionary + the output path, and reuse the SAME curated
# block/allow lists, so adding one never touches the US list. `dict` is passed to
# spylls' Dictionary.from_files -- a bundled name ("en_US") or a path prefix to a
# committed <prefix>.aff/.dic. Run e.g. `python build_wordlist.py --variant gb`.
VARIANTS = {
    "us": {"dict": "en_US",
           "out": OUT},
    "gb": {"dict": str(DATA_DIR / "hunspell" / "gb" / "en_GB"),
           "out": DATA_DIR / "gb" / "wordlist_master.txt"},
}


def load_wordset(path: Path) -> set[str]:
    """Read a curated word list: one word per line; blank lines / #comments skipped."""
    if not path.exists():
        return set()
    words = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            words.add(line)
    return words


def build(variant: str = "us") -> list[tuple[str, float]]:
    speller = Dictionary.from_files(VARIANTS[variant]["dict"])
    blocklist = load_wordset(BLOCKLIST_FILE)
    allowlist = load_wordset(ALLOWLIST_FILE)
    freqs = get_frequency_dict("en", wordlist=WORDLIST)
    rows: list[tuple[str, float]] = []
    for word in freqs:
        if not (word.isascii() and word.isalpha() and word.islower()):
            continue
        if word in blocklist:
            continue
        if not (speller.lookup(word) or word in allowlist):
            continue
        z = zipf_frequency(word, "en", wordlist=WORDLIST)
        if z < FLOOR:
            continue
        rows.append((word, z))
    # Descending frequency; alphabetical for equal-Zipf ties (stable, readable).
    rows.sort(key=lambda r: (-r[1], r[0]))
    return rows


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    variant = "us"
    it = iter(argv)
    for a in it:
        if a == "--variant":
            variant = next(it, "us")
        elif a.startswith("--variant="):
            variant = a.split("=", 1)[1]
        else:
            raise SystemExit(f"unknown arg {a!r} (only --variant is supported)")
    if variant not in VARIANTS:
        raise SystemExit(f"unknown variant {variant!r}; choose one of {list(VARIANTS)}")
    out = VARIANTS[variant]["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = build(variant)
    with out.open("w", encoding="utf-8") as fh:
        for word, z in rows:
            fh.write(f"{word}\t{z:.2f}\n")
    print(f"wrote {len(rows):,} words to {out}  "
          f"(variant {variant!r}, dict {VARIANTS[variant]['dict']!r})")
    # Provenance: how many survive at each candidate game cutoff.
    for cut in (4.0, 3.5, 3.0, 2.8, 2.5, 2.2, 2.0):
        n = sum(1 for _, z in rows if z >= cut)
        print(f"  zipf >= {cut}: {n:,} words")


if __name__ == "__main__":
    main()

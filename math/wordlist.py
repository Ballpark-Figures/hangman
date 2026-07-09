"""Curated frequency-ranked English wordlist for hangman.

The single master list for all of this video's math. Built by
``build_wordlist.py`` from the ``wordfreq`` package intersected with a real
dictionary; see that file for provenance. Lives at ``data/wordlist_master.txt``
as ``word<TAB>zipf`` lines, sorted most-common first.

``zipf`` is wordfreq's Zipf frequency scale = log10(occurrences per billion
words). Higher = more common. Useful anchors:

    zipf 4.0  ~10 per million   core everyday vocabulary
    zipf 3.0  ~ 1 per million   "essentially every adult knows this word"
    zipf 2.5  the game cutoff   familiar-to-about-half; starts to feel obscure
    zipf 2.0  the file's floor  distinctly obscure/technical

DEFAULT_ZIPF (2.5) is the chosen "familiar to about half" game cutoff. The file
is stored down to zipf 2.0 so you can loosen the cutoff without rebuilding; to
go below 2.0, lower FLOOR in build_wordlist.py and regenerate.

The list KEEPS inflected forms (plurals, conjugations) as their own entries --
e.g. ``running`` (zipf 5.23), ``runs`` (4.84), ``ran`` (4.87), ``cats`` (4.46).

Stdlib-only. Typical use::

    from wordlist import load, tier

    words = load(min_len=5, max_len=8)   # default cutoff, frequency order
    answer = words[0].text

    easy = tier("easy")
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "wordlist_master.txt"

# The chosen game cutoff -- words familiar to about half of players.
DEFAULT_ZIPF = 2.5


@dataclass(frozen=True)
class Word:
    """One entry from the master list."""

    text: str
    zipf: float  # wordfreq Zipf frequency; higher = more common
    rank: int    # 0-based frequency rank in the full file (0 == most common)


@lru_cache(maxsize=1)
def _raw() -> tuple[Word, ...]:
    """Parse the master file once (cached). Preserves frequency order."""
    words: list[Word] = []
    with DATA_FILE.open(encoding="utf-8") as fh:
        for rank, line in enumerate(fh):
            text, _, zipf = line.partition("\t")
            words.append(Word(text, float(zipf), rank))
    return tuple(words)


def load(
    *,
    min_len: int = 1,
    max_len: int | None = None,
    min_zipf: float = DEFAULT_ZIPF,
    max_zipf: float | None = None,
) -> list[Word]:
    """Return master-list words in frequency order, filtered.

    Args:
        min_len:  minimum word length (inclusive).
        max_len:  maximum word length (inclusive); ``None`` = no cap.
        min_zipf: keep only words at least this common. Defaults to
                  :data:`DEFAULT_ZIPF` (3.0), the "players know it" cutoff.
                  Raise it for an easier game, lower it (down to the file's
                  2.5 floor) for a harder one.
        max_zipf: optional upper bound -- e.g. pass ``min_zipf=3.0,
                  max_zipf=4.0`` to get the "known but not trivially common"
                  band for a harder tier.

    Returns:
        A list of :class:`Word`, most-common first.
    """
    out = []
    for w in _raw():
        if w.zipf < min_zipf:
            continue
        if max_zipf is not None and w.zipf > max_zipf:
            continue
        if len(w.text) < min_len:
            continue
        if max_len is not None and len(w.text) > max_len:
            continue
        out.append(w)
    return out


# Difficulty presets: (zipf band, length range). "easy" = short + very common,
# "hard" = longer + down to the known-word cutoff. Starting points -- playtest
# and adjust.
TIERS = {
    "easy":   dict(min_zipf=4.3, min_len=4, max_len=6),
    "medium": dict(min_zipf=3.5, min_len=5, max_len=8),
    "hard":   dict(min_zipf=2.5, min_len=7, max_len=12),
}


def tier(name: str) -> list[Word]:
    """Return the word pool for a named difficulty (see :data:`TIERS`)."""
    return load(**TIERS[name])


if __name__ == "__main__":
    full = _raw()
    print(f"master list: {len(full):,} words, {DATA_FILE}")
    print(f"  zipf range {full[-1].zipf:.2f}..{full[0].zipf:.2f}")
    known = load()
    print(f"  at default cutoff (zipf >= {DEFAULT_ZIPF}): {len(known):,} words")
    for name in TIERS:
        pool = tier(name)
        sample = ", ".join(w.text for w in pool[:8])
        print(f"  {name:<7} {len(pool):>6,} words  e.g. {sample}")

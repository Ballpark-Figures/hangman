"""Letter position-pattern frequencies for hangman analysis.

For a fixed word length and each letter, tabulate every SUBSET of positions the
letter occupies across the wordlist. E.g. length 3, letter 'e':

    ___  e__  _e_  __e  ee_  e_e  _ee  eee

where '_' is any other letter. The first (`___`) is "e absent"; the rest are
the position-subsets where e actually appears. Every word maps each letter to
exactly ONE such pattern, so for a given letter the patterns partition the whole
list (counts sum to the number of words; shares/probs sum to 1).

`pattern_frequencies(length)` returns a pandas DataFrame with, per (letter,
pattern):
  - count : number of words showing that pattern (UNWEIGHTED)
  - share : count / (#words of this length) -- unweighted fraction
  - freq  : summed linear word frequency (10**(zipf-9) per word) -- usage weight
  - prob  : freq normalized per letter -- usage-weighted probability

`count`/`share` treat every word equally; `freq`/`prob` weight by how common
each word is. Words come from the curated list via `wordlist.load()` (default
cutoff `wordlist.DEFAULT_ZIPF`). Only patterns that actually occur are listed.
"""

from __future__ import annotations

import string
from collections import Counter

import wordlist

ALPHABET = string.ascii_lowercase


def position_share(length: int, *, min_zipf: float | None = None):
    """Per-position letter share at `length`, UNWEIGHTED (each word counts once).

    Returns ``(shares, n_words)`` where ``shares[letter]`` is a list of `length`
    floats and ``shares[letter][i]`` = fraction of length-`length` words whose
    character at position ``i`` is ``letter``. One pass over the length-`length`
    pool from ``wordlist.load`` (default cutoff ``DEFAULT_ZIPF``). This is the
    per-position marginal of `pattern_frequencies`' ``share`` column, computed
    directly. Stdlib-only (no pandas) so it's cheap to call from a render cache.
    """
    if min_zipf is None:
        min_zipf = wordlist.DEFAULT_ZIPF
    words = wordlist.load(min_len=length, max_len=length, min_zipf=min_zipf)
    n = len(words)
    counts = {ch: [0] * length for ch in ALPHABET}
    for w in words:
        for i, ch in enumerate(w.text):
            if ch in counts:
                counts[ch][i] += 1
    shares = {ch: [(c / n if n else 0.0) for c in counts[ch]] for ch in ALPHABET}
    return shares, n


def top_ngrams(letter, *, sizes=(2, 3), top=5, min_zipf: float | None = None):
    """Most common adjacent n-grams (each size in `sizes`) that CONTAIN `letter`,
    ranked by the number of words (ANY length) that contain the n-gram — a word
    holding it more than once counts ONCE. This is the word-count ranking behind
    the notebook's `letter_ngram_table` `pct_words` column. Returns
    ``{size: [(gram, n_words), …]}`` with the `top` most common per size.
    Stdlib-only; sourced from ``wordlist.load`` (default cutoff DEFAULT_ZIPF)."""
    if min_zipf is None:
        min_zipf = wordlist.DEFAULT_ZIPF
    letter = letter.lower()
    words = wordlist.load(min_zipf=min_zipf)          # all lengths
    counts = {k: Counter() for k in sizes}
    for w in words:
        t = w.text
        for k in sizes:
            grams = {t[j:j + k] for j in range(len(t) - k + 1)
                     if letter in t[j:j + k]}
            for gram in grams:
                counts[k][gram] += 1
    return {k: counts[k].most_common(top) for k in sizes}


def _pattern(length: int, letter: str, positions) -> str:
    chars = ["_"] * length
    for i in positions:
        chars[i] = letter
    return "".join(chars)


def pattern_frequencies(length: int, *, min_zipf: float | None = None,
                        include_absent: bool = True) -> pd.DataFrame:
    """Frequencies of every letter position-pattern for a given word length.

    Args:
        length:         the word length to analyze.
        min_zipf:       frequency cutoff for the pool (default: the loader's
                        DEFAULT_ZIPF).
        include_absent: include the all-underscore "letter absent" pattern for
                        each letter (default True; set False to keep only the
                        patterns where the letter appears).

    Returns:
        DataFrame [letter, pattern, n_positions, count, share, freq, prob],
        sorted by letter then descending count. `df.attrs['n_words']` and
        `df.attrs['total_freq']` hold the per-letter totals.
    """
    import pandas as pd   # lazy: keeps the module stdlib-only for position_share
    if min_zipf is None:
        min_zipf = wordlist.DEFAULT_ZIPF
    words = wordlist.load(min_len=length, max_len=length, min_zipf=min_zipf)

    count: Counter = Counter()   # (letter, pattern) -> word count
    freq: Counter = Counter()    # (letter, pattern) -> summed linear frequency
    total_freq = 0.0
    empty = "_" * length

    for w in words:
        lin = 10 ** (w.zipf - 9)   # per-word usage weight (fraction of tokens)
        total_freq += lin
        positions: dict[str, list[int]] = {}
        for i, ch in enumerate(w.text):
            positions.setdefault(ch, []).append(i)
        for ch, idxs in positions.items():
            key = (ch, _pattern(length, ch, idxs))
            count[key] += 1
            freq[key] += lin
        if include_absent:
            for ch in ALPHABET:
                if ch not in positions:
                    count[(ch, empty)] += 1
                    freq[(ch, empty)] += lin

    n_words = len(words)
    rows = [
        {
            "letter": ch,
            "pattern": pat,
            "n_positions": length - pat.count("_"),
            "count": c,
            "share": (c / n_words) if n_words else 0.0,
            "freq": freq[(ch, pat)],
            "prob": (freq[(ch, pat)] / total_freq) if total_freq else 0.0,
        }
        for (ch, pat), c in count.items()
    ]
    df = pd.DataFrame(
        rows,
        columns=["letter", "pattern", "n_positions", "count", "share", "freq", "prob"],
    )
    df = df.sort_values(["letter", "count"], ascending=[True, False]).reset_index(drop=True)
    df.attrs["n_words"] = n_words
    df.attrs["total_freq"] = total_freq
    return df


if __name__ == "__main__":
    df = pattern_frequencies(3)
    print(f"length 3: {df.attrs['n_words']:,} words, {len(df):,} (letter, pattern) rows")
    print("\nletter 'e':")
    print(df[df.letter == "e"].to_string(index=False))

"""Greedy hangman strategy: average wrong guesses for a word length.

Model. For a fixed word length we treat every word of that length (from the
curated list, ``wordlist.load``) as a candidate, each with a non-normalized
FREQUENCY (default 1, but pluggable). A player guesses letters; a guess is a
MISS if the letter is absent from the hidden word. The greedy strategy, at every
state, guesses the un-guessed letter with the highest COMBINED FREQUENCY = the
summed frequency of candidate words that CONTAIN it (presence-based: a hit
reveals all of the letter's positions at once). Guessing a letter partitions the
candidate set by that letter's position-pattern (which slots it fills; the empty
pattern = letter absent = one miss). We recurse until a single candidate remains
(the word is then determined; any further guesses are hits, so miss-counting
stops). There is NO cap on misses.

Two questions this answers, for a chosen length:
  - average_misses(freq)            -- Mode A: frequency-weighted average misses
                                       of the greedy strategy over all words.
  - misses_by_starting_letter(freq) -- Mode B: for each possible FIRST letter,
                                       the weighted-average misses if that letter
                                       is forced first and greedy is played after.

Speed. The frequency-INDEPENDENT structure (per-word letter position bitmasks) is
precomputed once in ``GreedyGame(length)``; each solve is a light numpy recursion
(cost ~ Σ candidate-set sizes over the tree). So the intended workflow --
"tweak the frequencies, re-run" -- pays only the solve, not the setup. Build one
``GreedyGame`` per length, then call the methods with different ``freq`` vectors.

Pure numpy + stdlib (no pandas in the hot loop). Run ``python math/strategy.py``
for a demo + timing.
"""

from __future__ import annotations

import numpy as np

import wordlist
from wordlist import DEFAULT_ZIPF

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

try:
    from numba import njit
    _HAVE_NUMBA = True
except Exception:            # numba absent (e.g. the trimmed render venv)
    _HAVE_NUMBA = False


if _HAVE_NUMBA:

    @njit(cache=True)
    def _solve_numba(masks, f, misses, S, guessed_bits):
        """Native version of GreedyGame._solve: accumulate per-word misses.

        Identical results to the numpy path when f is integer-valued (our case),
        since letter_freq is then an exact integer sum.
        """
        n = S.shape[0]
        if n <= 1:
            return
        letter_freq = np.zeros(26)
        for j in range(n):
            i = S[j]
            fi = f[i]
            for c in range(26):
                if masks[i, c] != 0:
                    letter_freq[c] += fi
        for c in range(26):                          # exclude already-guessed letters
            if (guessed_bits >> c) & 1:
                letter_freq[c] = -1.0
        best_c = 0
        best_v = letter_freq[0]
        for c in range(1, 26):                       # argmax, ties -> lowest index
            if letter_freq[c] > best_v:
                best_v = letter_freq[c]
                best_c = c
        c = best_c
        pats = np.empty(n, dtype=np.uint32)
        for j in range(n):
            pats[j] = masks[S[j], c]
        order = np.argsort(pats)                     # group by pattern (contiguous runs)
        nxt = guessed_bits | (np.int64(1) << np.int64(c))
        start = 0
        while start < n:
            pv = pats[order[start]]
            end = start + 1
            while end < n and pats[order[end]] == pv:
                end += 1
            m = end - start
            group = np.empty(m, dtype=S.dtype)
            for t in range(m):
                group[t] = S[order[start + t]]
            if pv == 0:                              # letter absent -> one wrong guess
                for t in range(m):
                    misses[group[t]] += 1.0
            _solve_numba(masks, f, misses, group, nxt)
            start = end


class GreedyGame:
    """Greedy-strategy evaluator for all words of one length.

    Build once (precomputes the letter-position structure), then call
    ``average_misses`` / ``misses_by_starting_letter`` repeatedly with different
    frequency vectors.
    """

    def __init__(self, length: int, *, min_zipf: float = DEFAULT_ZIPF,
                 words: list[str] | None = None):
        if words is None:
            words = [w.text for w in wordlist.load(
                min_len=length, max_len=length, min_zipf=min_zipf)]
        self.length = length
        self.words: list[str] = list(words)
        self.N = len(self.words)
        self._index = {w: i for i, w in enumerate(self.words)}

        # masks[i, c] = bitmask of the positions letter c occupies in word i (0 if
        # absent). present[i, c] = 1.0 if letter c is in word i (for the argmax).
        self.masks = np.zeros((self.N, 26), dtype=np.uint32)
        for i, w in enumerate(self.words):
            for pos, ch in enumerate(w):
                self.masks[i, ord(ch) - 97] |= np.uint32(1) << np.uint32(pos)
        self.present = (self.masks > 0).astype(np.float64)

    # ---- frequency handling ------------------------------------------------
    def ones(self) -> np.ndarray:
        """Default frequency vector: 1 for every word."""
        return np.ones(self.N, dtype=np.float64)

    def _coerce_freq(self, freq) -> np.ndarray:
        if freq is None:
            return self.ones()
        if callable(freq):
            return np.array([float(freq(w)) for w in self.words], dtype=np.float64)
        if isinstance(freq, dict):
            return np.array([float(freq.get(w, 1.0)) for w in self.words],
                            dtype=np.float64)
        arr = np.asarray(freq, dtype=np.float64)
        if arr.shape != (self.N,):
            raise ValueError(f"freq must have shape ({self.N},), got {arr.shape}")
        return arr

    # ---- core traversal ----------------------------------------------------
    def _solve(self, S: np.ndarray, guessed_bits: int, f: np.ndarray,
               misses: np.ndarray) -> None:
        """Play greedy on candidate indices S; accumulate wrong guesses into misses."""
        if S.shape[0] <= 1:
            return  # word determined -> no more misses
        letter_freq = f[S] @ self.present[S]        # (26,) combined freq per letter
        g = guessed_bits
        while g:                                     # exclude already-guessed letters
            c = (g & -g).bit_length() - 1
            letter_freq[c] = -1.0
            g &= g - 1
        c = int(letter_freq.argmax())                # ties -> lowest index (a..z)
        pats = self.masks[S, c]
        nxt = guessed_bits | (1 << c)
        for pat in np.unique(pats):
            group = S[pats == pat]
            if pat == 0:                             # letter absent -> one wrong guess
                misses[group] += 1
            self._solve(group, nxt, f, misses)

    def _run(self, S: np.ndarray, guessed_bits: int, f: np.ndarray,
             misses: np.ndarray) -> None:
        """Dispatch to the numba kernel if available, else the numpy recursion."""
        if _HAVE_NUMBA:
            _solve_numba(self.masks, f, misses, np.ascontiguousarray(S), guessed_bits)
        else:
            self._solve(S, guessed_bits, f, misses)

    def per_word_misses(self, freq=None) -> np.ndarray:
        """Wrong guesses the greedy strategy makes for each word (aligned to words)."""
        f = self._coerce_freq(freq)
        misses = np.zeros(self.N, dtype=np.float64)
        self._run(np.arange(self.N), 0, f, misses)
        return misses

    # ---- Mode A ------------------------------------------------------------
    def average_misses(self, freq=None) -> float:
        """Frequency-weighted average wrong guesses over all words (Mode A)."""
        f = self._coerce_freq(freq)
        misses = np.zeros(self.N, dtype=np.float64)
        self._run(np.arange(self.N), 0, f, misses)
        return float((f * misses).sum() / f.sum())

    def greedy_first_letter(self, freq=None) -> str:
        """The letter the greedy strategy opens with."""
        f = self._coerce_freq(freq)
        return ALPHABET[int((f @ self.present).argmax())]

    # ---- Mode B ------------------------------------------------------------
    def _opener_misses(self, c: int, f: np.ndarray, total: float) -> float:
        """Weighted-average misses if letter ``c`` is forced first and greedy is
        played after (``f`` already coerced, ``total = f.sum()``)."""
        misses = np.zeros(self.N, dtype=np.float64)
        pats = self.masks[:, c]
        nxt = 1 << c
        for pat in np.unique(pats):
            group = np.flatnonzero(pats == pat)
            if pat == 0:                              # absent -> a wrong opening guess
                misses[group] += 1
            self._run(group, nxt, f, misses)
        return float((f * misses).sum() / total)

    def misses_by_starting_letter(self, freq=None) -> dict[str, float]:
        """For each first letter, weighted-average misses if forced first (Mode B).

        Returns ``{letter: avg_misses}`` sorted best (fewest) first.
        """
        f = self._coerce_freq(freq)
        total = f.sum()
        out = {ALPHABET[c]: self._opener_misses(c, f, total) for c in range(26)}
        return dict(sorted(out.items(), key=lambda kv: kv[1]))

    def best_opener_misses(self, freq=None, *, prune_below: float | None = None
                           ) -> tuple[str, float]:
        """Fewest weighted-average misses over all forced openers -- the guesser
        who picks the best first letter, then plays greedy. Returns
        ``(letter, avg_misses)``; always <= ``average_misses`` (greedy's own opener
        is one of the options).

        Openers are tried in descending current root letter frequency
        (``f @ present`` -- the order greedy itself prefers), which surfaces
        low-miss openers early. If ``prune_below`` is given, the scan stops as soon
        as the running best is ``<= prune_below`` and returns that partial best:
        a running minimum only decreases, so once it is <= the threshold the true
        minimum is too -- the caller can reject without the remaining solves. With
        ``prune_below=None`` it is a full 26-opener scan (the honest objective).
        """
        f = self._coerce_freq(freq)
        total = f.sum()
        order = np.argsort(f @ self.present)[::-1]    # descending root frequency
        best_c, best_v = -1, np.inf
        for c in order:
            c = int(c)
            v = self._opener_misses(c, f, total)
            if v < best_v:
                best_c, best_v = c, v
            if prune_below is not None and best_v <= prune_below:
                break
        return ALPHABET[best_c], best_v

    # ---- illustration / debugging -----------------------------------------
    def trace(self, word: str, freq=None) -> list[tuple[str, bool]]:
        """The greedy guess sequence for one word, played until the word is fully
        revealed: [(letter, hit?), ...].

        The main loop counts misses until the word is uniquely *determined* (the
        candidate set narrows to one). At that point the remaining un-guessed
        letters of the word are guaranteed hits, so we append them (never misses)
        to finish the word for display -- the miss count is unchanged.
        """
        f = self._coerce_freq(freq)
        i = self._index[word]
        S = np.arange(self.N)
        guessed_bits = 0
        seq: list[tuple[str, bool]] = []
        while S.shape[0] > 1:
            letter_freq = f[S] @ self.present[S]
            g = guessed_bits
            while g:
                c0 = (g & -g).bit_length() - 1
                letter_freq[c0] = -1.0
                g &= g - 1
            c = int(letter_freq.argmax())
            hit = bool(self.masks[i, c])
            seq.append((ALPHABET[c], hit))
            S = S[self.masks[S, c] == self.masks[i, c]]
            guessed_bits |= 1 << c
        # word determined -- fill in its remaining letters (all hits) to finish it
        for c in range(26):
            if self.masks[i, c] and not (guessed_bits >> c) & 1:
                seq.append((ALPHABET[c], True))
                guessed_bits |= 1 << c
        return seq


def _demo(length: int = 5) -> None:
    import time
    t0 = time.perf_counter()
    g = GreedyGame(length)
    t_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    avg = g.average_misses()
    t_a = time.perf_counter() - t0

    t0 = time.perf_counter()
    by_letter = g.misses_by_starting_letter()
    t_b = time.perf_counter() - t0

    print(f"length {length}: {g.N:,} words  (build {t_build*1e3:.0f} ms)")
    print(f"greedy opens with '{g.greedy_first_letter()}'")
    print(f"Mode A  average misses = {avg:.4f}   ({t_a*1e3:.0f} ms)")
    print(f"Mode B  misses by starting letter   ({t_b*1e3:.0f} ms)")
    best = list(by_letter.items())
    print("  best openers: " + ", ".join(f"{l}={v:.3f}" for l, v in best[:6]))
    print("  worst openers: " + ", ".join(f"{l}={v:.3f}" for l, v in best[-6:]))


if __name__ == "__main__":
    _demo(5)

"""Adversarial frequency hill-climb over per-(letter, pattern) multipliers.

Frequency model. For a fixed word length, every distinct (letter, nonempty
position-pattern) that occurs has a real-valued MULTIPLIER (start 1). A word's
frequency is the PRODUCT of the multipliers for the patterns it exhibits (one per
distinct letter it contains). All-ones multipliers -> all frequencies 1.

Search. Coordinate pattern-search that MAXIMIZES the greedy strategy's average
misses (an adversarial word-setter vs. the greedy guesser), in phases:
  1. DOUBLING -- repeatedly try m*2 for every multiplier, keep it if the average
     strictly increases; loop until no multiplier benefits. Reaches large scales
     in log-many steps (so a runaway multiplier doesn't crawl up additively).
  2. +/- POWERS OF 2 -- additive steps of powers of two from the largest scale
     reached (>= max multiplier) down to 1; try both m+s and m-s (never below 0).
  3. +/- FINE -- additive steps FINE_STEPS = 0.5, 0.2, 0.1.
Each phase loops in a fixed order (sequential / Gauss-Seidel), keeping whichever
move most increases the average, until a full pass makes no change; then the next
phase/step begins. Each accepted change prints `<pattern> ->x<mult> (<phase>)
avg=<new>` and is appended to a CSV log; each loop prints its change count.

Every accepted change is logged (data/freq_search/len<LL>.csv) so the frequency
state can be reconstructed later -- see ``reconstruct``.

Builds on ``strategy.GreedyGame`` (numba-accelerated solve). Frequencies are
products of the multipliers, recomputed vectorized via ``np.multiply.reduceat``.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from strategy import GreedyGame, ALPHABET
from wordlist import DEFAULT_ZIPF

DATA_DIR = Path(__file__).resolve().parent / "data" / "freq_search"
EPS = 1e-9
FINE_STEPS = [0.5, 0.2, 0.1]


def _pattern_string(length: int, letter_idx: int, mask: int) -> str:
    """e.g. length 3, letter 'e', mask {0,2} -> 'e_e'."""
    return "".join(ALPHABET[letter_idx] if (mask >> p) & 1 else "_" for p in range(length))


class FrequencySearch:
    """Hill-climb per-(letter, pattern) multipliers to maximize greedy misses."""

    def __init__(self, length: int, *, min_zipf: float = DEFAULT_ZIPF,
                 game: GreedyGame | None = None):
        self.game = game if game is not None else GreedyGame(length, min_zipf=min_zipf)
        g = self.game
        self.length = g.length

        # Enumerate (letter, mask) keys and the keys each word uses.
        keymap: dict[tuple[int, int], int] = {}
        key_letter: list[int] = []
        key_mask: list[int] = []
        word_keys: list[list[int]] = [[] for _ in range(g.N)]
        for i in range(g.N):
            for c in range(26):
                m = int(g.masks[i, c])
                if m:
                    k = keymap.get((c, m))
                    if k is None:
                        k = len(key_letter)
                        keymap[(c, m)] = k
                        key_letter.append(c)
                        key_mask.append(m)
                    word_keys[i].append(k)
        self.M = len(key_letter)
        self.key_letter = np.array(key_letter, dtype=np.int64)
        self.key_mask = np.array(key_mask, dtype=np.int64)
        self._keyidx = keymap
        self.pattern = [_pattern_string(self.length, key_letter[k], key_mask[k])
                        for k in range(self.M)]

        # Flat CSR (word -> keys) for a fast exact freq recompute via reduceat.
        counts = np.array([len(ks) for ks in word_keys], dtype=np.int64)
        self.word_ptr = np.zeros(g.N, dtype=np.int64)
        self.word_ptr[1:] = np.cumsum(counts)[:-1]
        self.flat_keys = np.array([k for ks in word_keys for k in ks], dtype=np.int64)

        self.mult = np.ones(self.M, dtype=np.float64)
        self.freq = np.ones(g.N, dtype=np.float64)
        # Deterministic order: by letter, then mask.
        self.order = sorted(range(self.M),
                            key=lambda k: (int(self.key_letter[k]), int(self.key_mask[k])))
        self.records: list[dict] = []

    # ---- frequency from multipliers ----------------------------------------
    def _recompute_freq(self) -> None:
        self.freq = np.multiply.reduceat(
            self.mult[self.flat_keys].astype(np.float64), self.word_ptr)

    def freq_from_multipliers(self, mult: np.ndarray) -> np.ndarray:
        return np.multiply.reduceat(mult[self.flat_keys].astype(np.float64), self.word_ptr)

    # ---- the search --------------------------------------------------------
    def _phase(self, cand_fn, label, avg, *, max_loops, verbose, writer, fh, cols):
        """Loop one phase (candidate values from cand_fn) until a pass makes no change."""
        g = self.game
        if verbose:
            print(f"--- {label} ---")
        loop = 0
        while max_loops is None or loop < max_loops:
            changes = 0
            for k in self.order:
                base = float(self.mult[k])
                best_val, best_avg = base, avg
                for cand in cand_fn(base):
                    if cand < 0.0:                     # never go below 0
                        continue
                    self.mult[k] = cand
                    self._recompute_freq()
                    a = g.average_misses(self.freq)
                    if math.isfinite(a) and a > best_avg + EPS:
                        best_avg, best_val = a, cand
                self.mult[k] = best_val
                self._recompute_freq()
                if best_val != base:
                    avg = best_avg
                    rec = {"phase": label, "loop": loop, "seq": len(self.records),
                           "letter": ALPHABET[int(self.key_letter[k])],
                           "pattern": self.pattern[k], "mask": int(self.key_mask[k]),
                           "multiplier": best_val, "avg_misses": avg}
                    self.records.append(rec)
                    changes += 1
                    if verbose:
                        print(f"  {self.pattern[k]}  ->x{best_val:g}  ({label})  avg={avg:.4f}")
                    if writer:
                        writer.writerow([rec[c] for c in cols])
                        fh.flush()
            if verbose:
                print(f"  loop {loop}: {changes} changes")
            if changes == 0:
                break
            loop += 1
        return avg

    def run(self, *, fine_steps=None, max_loops: int | None = None, log_path=None,
            verbose: bool = True) -> list[dict]:
        fine_steps = list(FINE_STEPS if fine_steps is None else fine_steps)
        g = self.game
        self.mult[:] = 1.0
        self._recompute_freq()
        avg = g.average_misses(self.freq)   # also warms the JIT
        self.records = []

        fh = writer = None
        cols = ("phase", "loop", "seq", "letter", "pattern", "mask",
                "multiplier", "avg_misses")
        if log_path is not None:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            fh = log_path.open("w", newline="")
            writer = csv.writer(fh)
            writer.writerow(cols)

        if verbose:
            print(f"length {self.length}: {g.N} words, {self.M} patterns; "
                  f"start avg = {avg:.4f}")

        kw = dict(max_loops=max_loops, verbose=verbose, writer=writer, fh=fh, cols=cols)

        # Phase 1: doubling -- reach the right scale in log-many steps.
        avg = self._phase(lambda b: (b * 2.0,), "x2", avg, **kw)

        # Phase 2: +/- powers of 2, from the largest scale reached down to 1.
        p = 1
        top = int(self.mult.max())
        while p * 2 <= top:
            p *= 2
        while p >= 1:
            s = float(p)
            avg = self._phase(lambda b, s=s: (b + s, b - s), f"+/-{s:g}", avg, **kw)
            p //= 2

        # Phase 3: fine additive steps.
        for s in fine_steps:
            avg = self._phase(lambda b, s=s: (b + s, b - s), f"+/-{s:g}", avg, **kw)

        if fh:
            fh.close()
        if verbose:
            print(f"done: {len(self.records)} changes, final avg = {avg:.4f}")
        return self.records

    # ---- reconstruction ----------------------------------------------------
    def multipliers_from_records(self, records, upto: int | None = None) -> np.ndarray:
        """Replay accepted changes into a multiplier vector (upto = # rows to apply)."""
        mult = np.ones(self.M, dtype=np.float64)
        rows = records if upto is None else records[:upto]
        for r in rows:
            letter = r["letter"] if isinstance(r, dict) else r.letter
            mask = int(r["mask"] if isinstance(r, dict) else r.mask)
            multiplier = float(r["multiplier"] if isinstance(r, dict) else r.multiplier)
            mult[self._keyidx[(ord(letter) - 97, mask)]] = multiplier
        return mult

    @classmethod
    def reconstruct(cls, length: int, csv_path, *, min_zipf: float = DEFAULT_ZIPF,
                    upto: int | None = None) -> "FrequencySearch":
        """Rebuild a search with mult/freq set from a saved CSV log."""
        import pandas as pd
        df = pd.read_csv(csv_path)
        self = cls(length, min_zipf=min_zipf)
        self.mult = self.multipliers_from_records(list(df.itertuples(index=False)), upto=upto)
        self._recompute_freq()
        return self


def sweep(lengths, *, min_zipf: float = DEFAULT_ZIPF, max_loops: int | None = None,
          verbose: bool = True) -> dict[int, FrequencySearch]:
    """Run the hill-climb for each length, logging to data/freq_search/lenLL.csv."""
    out: dict[int, FrequencySearch] = {}
    for L in lengths:
        print(f"\n===== length {L} =====")
        s = FrequencySearch(L, min_zipf=min_zipf)
        s.run(max_loops=max_loops, log_path=DATA_DIR / f"len{L:02d}.csv", verbose=verbose)
        out[L] = s
    return out


if __name__ == "__main__":
    import sys
    lengths = [int(a) for a in sys.argv[1:]] or [5]
    sweep(lengths)

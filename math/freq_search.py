"""Adversarial frequency hill-climb.

Two knob parameterizations (same search, `--word` selects the second):
  - MULTIPLIER (default, `FrequencySearch`): every distinct (letter, nonempty
    position-pattern) has a real-valued MULTIPLIER (start 1); a word's frequency
    is the PRODUCT of the multipliers for the patterns it exhibits.
  - PER-WORD (`WordFrequencySearch`): every WORD has its own un-normalized
    frequency knob (start 1), adjusted directly -- no multipliers/product.
Both run the identical phased coordinate search (`_phase`/`run`); only the knob
vector, the log columns, and the iteration order differ.

Frequency model (multiplier mode). For a fixed word length, every distinct
(letter, nonempty position-pattern) that occurs has a real-valued MULTIPLIER
(start 1). A word's frequency is the PRODUCT of the multipliers for the patterns
it exhibits (one per distinct letter it contains). All-ones -> all frequencies 1.

Objective. Two guesser models are supported (``objective=``):
  - ``"greedy"``      -- pure greedy; score = ``average_misses`` (the default).
  - ``"best_opener"`` -- the guesser picks the BEST first letter, then plays
    greedy; score = ``best_opener_misses`` (min over forced openers). This hardens
    the adversary against a smarter guesser (pure greedy often opens with a
    far-from-optimal letter). Scoring the min is pruned: openers are tried in
    descending root frequency and the scan aborts once one lands at/under the
    value being beaten (the change is then rejected) -- an exact speedup.

Search. Coordinate pattern-search that MAXIMIZES the chosen objective (an
adversarial word-setter vs. the guesser), in phases:
  1. DOUBLE/HALVE -- for every multiplier try x2 or /2 (down to a floor of 0.125;
     0.125 can drop to 0, and 0 can come back to 0.125), keeping whichever raises
     the average (loop until none benefit).
  2. +/- POWERS OF 2 -- additive steps of powers of two from the largest scale
     reached (>= max multiplier) down to 1; try both m+s and m-s (never below 0).
  3. +/- FINE -- additive steps FINE_STEPS = 0.5, 0.25, 0.125.
Each phase loops in a fixed order (sequential / Gauss-Seidel), keeping whichever
move most increases the average, until a full pass makes no change; then the next
phase/step begins. Each accepted change prints `<pattern> ->x<mult> (<move>)
avg=<new>`, where <move> is x2, /2, +s or -s; each loop prints its change count.

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
FINE_STEPS = [0.5, 0.25, 0.125]
OBJECTIVES = ("greedy", "best_opener")


def _default_log_path(objective: str, length: int, mode: str = "mult") -> Path:
    """Per-length CSV log path; best_opener runs go in their own subdir so the
    greedy runs' files are untouched, and the per-word ("word") search gets its
    own subdir so it doesn't clobber the multiplier runs."""
    base = DATA_DIR if objective == "greedy" else DATA_DIR / objective
    if mode == "word":
        base = base / "word"
    return base / f"len{length:02d}.csv"


def _double_candidates(b):
    """Double/halve-phase moves for a multiplier b: x2, /2 (floor 0.125),
    0.125 -> 0, and 0 -> 0.125 (revive)."""
    if b == 0.0:
        return (0.125,)                 # revive: 0 -> 0.125
    if b <= 0.125:                       # 0.125 is the smallest positive rung
        return (b * 2.0, 0.0)           # x2, or drop to 0
    return (b * 2.0, b / 2.0)           # x2 or /2


def _pattern_string(length: int, letter_idx: int, mask: int) -> str:
    """e.g. length 3, letter 'e', mask {0,2} -> 'e_e'."""
    return "".join(ALPHABET[letter_idx] if (mask >> p) & 1 else "_" for p in range(length))


class FrequencySearch:
    """Hill-climb per-(letter, pattern) multipliers to maximize greedy misses."""

    def __init__(self, length: int, *, objective: str = "greedy",
                 min_zipf: float = DEFAULT_ZIPF, game: GreedyGame | None = None):
        if objective not in OBJECTIVES:
            raise ValueError(f"objective must be one of {OBJECTIVES}, got {objective!r}")
        self.objective = objective
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
        self._var = self.mult          # the knob vector the search adjusts
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

    # ---- per-mode hooks (this class = multiplier mode; WordFrequencySearch
    #      overrides them to adjust per-word frequencies instead) -------------
    _cols = ("move", "loop", "seq", "letter", "pattern", "mask",
             "multiplier", "avg_misses")

    def _make_record(self, k, val, move, loop, avg) -> dict:
        return {"move": move, "loop": loop, "seq": len(self.records),
                "letter": ALPHABET[int(self.key_letter[k])],
                "pattern": self.pattern[k], "mask": int(self.key_mask[k]),
                "multiplier": val, "avg_misses": avg}

    def _change_str(self, k, val) -> str:
        return f"{self.pattern[k]}  ->x{val:g}"

    # ---- objective ---------------------------------------------------------
    def _score(self, threshold) -> float:
        """The scalar to maximize for the current ``self.freq``. For best_opener,
        ``threshold`` (the current best-so-far) prunes the opener scan: a return
        value <= threshold means "does not beat" and is rejected by the caller."""
        if self.objective == "best_opener":
            return self.game.best_opener_misses(self.freq, prune_below=threshold)[1]
        return self.game.average_misses(self.freq)

    # ---- results as DataFrames ---------------------------------------------
    def multipliers_df(self):
        """Every (letter, pattern) multiplier for this length, highest first."""
        import pandas as pd
        n_words = np.bincount(self.flat_keys, minlength=self.M)
        return pd.DataFrame({
            "letter": [ALPHABET[int(c)] for c in self.key_letter],
            "pattern": self.pattern,
            "mask": [int(m) for m in self.key_mask],
            "multiplier": self.mult,
            "n_words": n_words,          # how many words carry this pattern
        }).sort_values("multiplier", ascending=False).reset_index(drop=True)

    def frequencies_df(self):
        """Every word's frequency for this length, heaviest first."""
        import pandas as pd
        return pd.DataFrame({
            "word": self.game.words,
            "frequency": self.freq,
        }).sort_values("frequency", ascending=False).reset_index(drop=True)

    # ---- the search --------------------------------------------------------
    def _phase(self, cand_fn, header, move_label, avg, *, max_loops, verbose, writer, fh, cols):
        """Loop one phase (candidate values from cand_fn) until a pass makes no change.

        move_label(base, new) -> the per-change label (e.g. 'x2', '/2', '+8', '-8').
        Adjusts self._var (multipliers here; per-word freqs in WordFrequencySearch)
        one knob at a time in self.order -- the sequence is identical either way.
        """
        if verbose:
            print(f"--- {header} ---")
        loop = 0
        while max_loops is None or loop < max_loops:
            changes = 0
            for k in self.order:
                base = float(self._var[k])
                best_val, best_avg = base, avg
                for cand in cand_fn(base):
                    if cand < 0.0:                     # never go below 0
                        continue
                    self._var[k] = cand
                    self._recompute_freq()
                    a = self._score(best_avg)
                    if math.isfinite(a) and a > best_avg:
                        best_avg, best_val = a, cand
                self._var[k] = best_val
                self._recompute_freq()
                if best_val != base:
                    avg = best_avg
                    move = move_label(base, best_val)
                    rec = self._make_record(k, best_val, move, loop, avg)
                    self.records.append(rec)
                    changes += 1
                    if verbose:
                        print(f"  {self._change_str(k, best_val)}  ({move})  avg={avg:.4f}")
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
        self._var[:] = 1.0
        self._recompute_freq()
        avg = self._score(None)             # full scan; also warms the JIT
        start_avg = avg
        self.records = []

        fh = writer = None
        cols = self._cols
        if log_path is not None:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            fh = log_path.open("w", newline="")
            writer = csv.writer(fh)
            writer.writerow(cols)

        if verbose:
            print(f"length {self.length} [{self.objective}]: {g.N} words, "
                  f"{len(self.order)} knobs; start avg = {avg:.4f}")

        kw = dict(max_loops=max_loops, verbose=verbose,
                  writer=writer, fh=fh, cols=cols)

        # Phase 1: double / halve (x2, /2, floor 0.125, 0.125 <-> 0).
        avg = self._phase(_double_candidates, "double/halve",
                          lambda base, new: "x2" if new > base else "/2", avg, **kw)

        # Phase 2: +/- powers of 2, from the largest scale reached down to 1.
        p = 1
        top = int(self._var.max())
        while p * 2 <= top:
            p *= 2
        while p >= 1:
            s = float(p)
            avg = self._phase(lambda b, s=s: (b + s, b - s), f"step {s:g}",
                              lambda base, new, s=s: f"+{s:g}" if new > base else f"-{s:g}",
                              avg, **kw)
            p //= 2

        # Phase 3: fine additive steps.
        for s in fine_steps:
            avg = self._phase(lambda b, s=s: (b + s, b - s), f"step {s:g}",
                              lambda base, new, s=s: f"+{s:g}" if new > base else f"-{s:g}",
                              avg, **kw)

        if fh:
            fh.close()
        if verbose:
            print(f"done: {len(self.records)} changes, "
                  f"initial avg = {start_avg:.4f}, final avg = {avg:.4f}")
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
    def reconstruct(cls, length: int, csv_path, *, objective: str = "greedy",
                    min_zipf: float = DEFAULT_ZIPF,
                    upto: int | None = None) -> "FrequencySearch":
        """Rebuild a search with mult/freq set from a saved CSV log. The replay is
        objective-independent; ``objective`` only tags the returned object so its
        ``_score`` matches the run that produced the log."""
        import pandas as pd
        df = pd.read_csv(csv_path)
        self = cls(length, objective=objective, min_zipf=min_zipf)
        self.mult = self.multipliers_from_records(list(df.itertuples(index=False)), upto=upto)
        self._var = self.mult
        self._recompute_freq()
        return self


class WordFrequencySearch(FrequencySearch):
    """Same adversarial hill-climb, but the knobs are per-WORD (un-normalized)
    frequencies directly -- NOT per-(letter, pattern) multipliers. Each word's
    frequency is its own variable (start 1); the double/halve, +/- powers-of-2,
    and fine phases run in the exact same sequence (shared `_phase`/`run`),
    iterating words in alphabetical order. Log columns are word, frequency."""

    _cols = ("move", "loop", "seq", "word", "frequency", "avg_misses")

    def __init__(self, length: int, *, objective: str = "greedy",
                 min_zipf: float = DEFAULT_ZIPF, game: GreedyGame | None = None):
        if objective not in OBJECTIVES:
            raise ValueError(f"objective must be one of {OBJECTIVES}, got {objective!r}")
        self.objective = objective
        self.game = game if game is not None else GreedyGame(length, min_zipf=min_zipf)
        g = self.game
        self.length = g.length
        self.freq = np.ones(g.N, dtype=np.float64)
        self._var = self.freq          # the knob IS each word's frequency
        self.order = sorted(range(g.N), key=lambda i: g.words[i])   # alphabetical, deterministic
        self.records: list[dict] = []

    def _recompute_freq(self) -> None:
        pass                            # self.freq is self._var already

    def _make_record(self, k, val, move, loop, avg) -> dict:
        return {"move": move, "loop": loop, "seq": len(self.records),
                "word": self.game.words[k], "frequency": val, "avg_misses": avg}

    def _change_str(self, k, val) -> str:
        return f"{self.game.words[k]}  ->{val:g}"

    def freq_from_records(self, records, upto: int | None = None) -> np.ndarray:
        """Replay accepted per-word changes into a freq vector."""
        freq = np.ones(self.game.N, dtype=np.float64)
        idx = {w: i for i, w in enumerate(self.game.words)}
        rows = records if upto is None else records[:upto]
        for r in rows:
            word = r["word"] if isinstance(r, dict) else r.word
            frequency = float(r["frequency"] if isinstance(r, dict) else r.frequency)
            freq[idx[word]] = frequency
        return freq

    @classmethod
    def reconstruct(cls, length: int, csv_path, *, objective: str = "greedy",
                    min_zipf: float = DEFAULT_ZIPF,
                    upto: int | None = None) -> "WordFrequencySearch":
        import pandas as pd
        # keep_default_na=False: real words like "null"/"nan"/"na" must stay
        # strings, not be coerced to NaN (they'd miss the word index otherwise).
        df = pd.read_csv(csv_path, keep_default_na=False, na_values=[])
        self = cls(length, objective=objective, min_zipf=min_zipf)
        self.freq = self.freq_from_records(list(df.itertuples(index=False)), upto=upto)
        self._var = self.freq
        return self


def sweep(lengths, *, objective: str = "greedy", mode: str = "mult",
          min_zipf: float = DEFAULT_ZIPF, max_loops: int | None = None,
          verbose: bool = True) -> dict[int, FrequencySearch]:
    """Run the hill-climb for each length, logging to the objective's CSV dir.
    mode "mult" = per-(letter,pattern) multipliers; "word" = per-word frequencies
    (its own `word/` subdir so it doesn't clobber the multiplier runs)."""
    cls = WordFrequencySearch if mode == "word" else FrequencySearch
    out: dict[int, FrequencySearch] = {}
    for L in lengths:
        print(f"\n===== length {L} ({objective}, {mode}) =====")
        s = cls(L, objective=objective, min_zipf=min_zipf)
        s.run(max_loops=max_loops, log_path=_default_log_path(objective, L, mode),
              verbose=verbose)
        out[L] = s
    return out


if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    objective = "best_opener" if "--best-opener" in argv else "greedy"
    mode = "word" if "--word" in argv else "mult"
    lengths = [int(a) for a in argv if not a.startswith("-")] or [5]
    sweep(lengths, objective=objective, mode=mode)

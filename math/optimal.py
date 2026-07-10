"""Exact optimal hangman solver (prototype) -- how far is greedy from optimal?

Model (same as ``strategy.py``). For a fixed word length, every word is a
candidate with a non-normalized FREQUENCY. A guess is a MISS if the letter is
absent from the hidden word. Guessing a letter partitions the candidate set by
that letter's position-pattern (empty pattern = absent = one miss per word in it).
We recurse until a single candidate remains. The OPTIMAL strategy is the decision
tree minimizing the frequency-weighted average misses.

State + recursion. Already-guessed letters are constant across the candidate set
S, so S (plus, under a cap, the misses still allowed) is a sufficient state. With
``r`` = misses remaining before the cap (``None`` = uncapped),

    V(S, r) = 0                                          if |S| <= 1  or  r == 0
    V(S, r) = min over letters L that SPLIT S of
                  [ W_absent(S, L) + V(absent_group, r-1)
                                   + sum over hit groups g of V(g, r) ]

W_absent = total freq of words in S lacking L (one miss each; only the absent
branch spends a miss and drops r by one). Optimal average = V(root, cap)/sum(f).
Crucially V(S, r) does NOT depend on the cap value itself, so the memo carries
across increasing caps -- each larger cap only adds the new deepest states.

Miss cap (iterative deepening -- ``deepen``). A low cap makes the tree shallow
(depth <= word length + cap) so it finishes fast; capping a word at C means once
its path spends C misses it is decided and we stop recursing. Raise the cap by one
and repeat; when the optimal tree's MAX misses is < cap, the cap never bound, so
the capped optimum equals the true uncapped optimum -- done.

Branch-and-bound (still EXACT). Letters tried greedy-first (highest presence) so a
tight incumbent is found early; each node seeds ``best`` with a cheap valid upper
bound (capped: r * weight(S); uncapped: greedy's own value at shallow depth); a
budget is threaded into children so subtrees that can't beat the incumbent are
never expanded; sets solved under budget are cached exact (value + optimal letter
= the tree), sets cut off early are cached as lower bounds. Per-node work is
vectorized (split detection via column min/max, absent weight via one matmul).
Two-word sets are separated directly and not memoized.

Run ``python math/optimal.py <length> [--weighted greedy|best_opener] [--uncapped]``.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from strategy import GreedyGame, ALPHABET
from wordlist import DEFAULT_ZIPF

try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except Exception:                       # pragma: no cover - tqdm is a listed dep
    _HAVE_TQDM = False

INF = float("inf")
DATA_DIR = Path(__file__).resolve().parent / "data" / "optimal"


def _emit(msg: str) -> None:
    (tqdm.write if _HAVE_TQDM else print)(msg)


class OptimalSolver:
    """Exact minimizer of frequency-weighted average misses for one word length."""

    def __init__(self, game: GreedyGame | None = None, *, length: int | None = None,
                 min_zipf: float = DEFAULT_ZIPF):
        if game is None:
            if length is None:
                raise ValueError("pass either a GreedyGame or a length")
            game = GreedyGame(length, min_zipf=min_zipf)
        self.game = game
        self.masks = game.masks                 # (N, 26) uint32 position bitmasks
        self.N = game.N
        self.words = game.words
        self._index = game._index

        self.freq: np.ndarray | None = None
        self.memo: dict = {}                    # (S.tobytes(), r) -> (exact value, best letter)
        self.lb: dict = {}                      # (S.tobytes(), r) -> proven lower bound
        self._ubbuf = np.zeros(self.N, dtype=np.float64)
        self._solve_cap = None

    # ---- upper bound: greedy's own (capped) value on S ---------------------
    def _greedy_ub(self, S: np.ndarray, r=None) -> float:
        """A valid upper bound on V(S, r): greedy's cost on S, each word's misses
        capped at the remaining budget r. Reuses greedy's per-word misses from one
        solve, so it is <= both plain greedy and the loose r*weight(S) bound."""
        buf = self._ubbuf
        self.game._run(S, 0, self.freq, buf)
        bufS = buf[S] if r is None else np.minimum(buf[S], r)
        ub = float(self.freq[S] @ bufS)
        buf[S] = 0.0
        return ub

    def _opener_ub(self, S, r, MS, splits, w_abs_all, order) -> tuple[float, int]:
        """1-ply best-opener upper bound: min over first letters of
        W_absent(c) + capped-greedy on each resulting group. Returns (value, the
        achieving first letter). Tighter than plain capped-greedy (~26x the solves),
        so only used at shallow depth where the nodes are few and a tight bound
        prunes the huge subtrees below."""
        best, best_c = INF, -1
        for oi in range(order.shape[0]):
            c = int(order[oi])
            if not splits[c]:
                continue
            pats = MS[:, c]
            cost = float(w_abs_all[c])
            for pv in np.unique(pats):
                grp = S[pats == pv]
                rr = r - 1 if (r is not None and pv == 0) else r
                cost += self._greedy_ub(grp, rr)
                if cost >= best:
                    break
            if cost < best:
                best, best_c = cost, c
        return best, best_c

    def _sep_two(self, a: int, b: int) -> tuple[float, int]:
        """Exact cost + separating letter for a two-word set {a, b}."""
        f = self.freq
        fa, fb = f[a], f[b]
        ma, mb = self.masks[a], self.masks[b]
        best, letter = INF, -1
        for c in range(26):
            if ma[c] != mb[c]:
                cost = (fa if ma[c] == 0 else 0.0) + (fb if mb[c] == 0 else 0.0)
                if cost < best:
                    best, letter = cost, c
                    if best == 0.0:
                        break
        return float(best), letter

    # ---- the recursion -----------------------------------------------------
    def _V(self, S: np.ndarray, r, bound: float, depth: int) -> float:
        """Exact V(S, r) if it is < bound, else a valid lower bound >= bound.
        ``r`` is misses remaining before the cap, or None for uncapped."""
        self._calls += 1
        if (self._calls & 0x3FFF) == 0:
            self._maybe_beat()

        n = S.shape[0]
        if n <= 1 or r == 0:
            return 0.0
        f = self.freq
        if n == 2:
            return self._sep_two(int(S[0]), int(S[1]))[0]

        key = (S.tobytes(), r)
        e = self.memo.get(key)
        if e is not None:
            return e[0]
        lbv = self.lb.get(key)
        if lbv is not None and lbv >= bound:
            return lbv

        MS = self.masks[S]
        fS = f[S]
        splits = MS.min(0) != MS.max(0)                  # (26,) which letters split S
        w_abs_all = fS @ (MS == 0)                        # (26,) absent weight per letter
        order = np.argsort(fS @ (MS > 0))[::-1]           # presence order (greedy-first)

        # greedy's first splitting letter -- a safe default move / achiever of the
        # greedy upper bound.
        gletter = next((int(c) for c in order if splits[int(c)]), -1)

        if depth <= self._opener_ub_depth:                # tightest: 1-ply best-opener (few nodes)
            ub, ub_letter = self._opener_ub(S, r, MS, splits, w_abs_all, order)
        elif depth <= self._ub_depth:                     # tight: greedy's (capped) value
            ub, ub_letter = self._greedy_ub(S, r), gletter
        elif r is not None:                               # deep + capped: cheap loose bound
            ub, ub_letter = r * float(fS.sum()), -1
        else:
            ub, ub_letter = INF, -1

        # ``achievable`` = best is the cost of a real strategy (the UB, or a letter we
        # fully solved) -> it is then the EXACT V(S, r), and best_letter is an optimal
        # move. If best stays == bound (nothing achievable beat it), it is only a lower
        # bound. This is what makes the stored move reliable, so the tree is a pure walk.
        best = bound
        best_letter = gletter
        achievable = ub < bound
        if achievable:
            best = ub
            if ub_letter >= 0:
                best_letter = ub_letter

        if depth > self._deep_d:                          # true deepest frontier this beat
            self._deep_d, self._deep_n = depth, n

        for oi in range(order.shape[0]):
            c = int(order[oi])
            if not splits[c]:
                continue
            w_abs = float(w_abs_all[c])
            if w_abs >= best:                             # immediate cost already too big
                continue
            pats = MS[:, c]
            uniq = np.unique(pats)
            cost = w_abs
            broke = False
            for gi in range(uniq.shape[0]):
                pv = uniq[gi]
                group = S[pats == pv]
                rr = r - 1 if (r is not None and pv == 0) else r
                if depth <= self._track_depth:
                    self._path[depth] = (n, c, oi, gi, uniq.shape[0])
                cost += self._V(group, rr, best - cost, depth + 1)
                if cost >= best:                          # a child was only a lower bound
                    broke = True
                    break
            if not broke and cost < best:                 # fully solved and strictly better
                best, best_letter, achievable = cost, c, True

        if achievable:
            self.memo[key] = (best, best_letter)          # exact value + optimal move
            return best
        self.lb[key] = best if lbv is None else max(lbv, best)
        return best

    # ---- root (opener-by-opener, for progress) -----------------------------
    def _solve_root(self, cap) -> tuple[float, int]:
        f, root = self.freq, np.arange(self.N, dtype=np.int32)
        MS = self.masks[root]
        fR = f[root]
        splits = MS.min(0) != MS.max(0)
        w_abs_all = fR @ (MS == 0)
        order_arr = np.argsort(fR @ (MS > 0))[::-1]
        order = [int(c) for c in order_arr if splits[int(c)]]

        best, best_letter = self._opener_ub(root, cap, MS, splits, w_abs_all, order_arr)
        if best_letter < 0:
            best_letter = order[0]
        bar = tqdm(order, desc=f"cap {cap} openers" if cap is not None else "openers",
                   unit="opener", disable=not (self._verbose and _HAVE_TQDM))
        c = order[0]
        try:
            for k, c in enumerate(bar):
                pats = MS[:, c]
                uniq = np.unique(pats)
                self._op = (ALPHABET[c], k + 1, len(order))
                self._l2_total, self._l2_done, self._l2_words = uniq.shape[0], 0, 0
                w_abs = float(w_abs_all[c])
                if w_abs >= best:
                    continue
                cost = w_abs
                broke = False
                for gi in range(uniq.shape[0]):
                    pv = uniq[gi]
                    group = root[pats == pv]
                    rr = cap - 1 if (cap is not None and pv == 0) else cap
                    self._path[1] = (self.N, c, k, gi, uniq.shape[0])
                    cost += self._V(group, rr, best - cost, 2)
                    self._l2_done += 1
                    self._l2_words += group.shape[0]
                    if cost >= best:
                        broke = True
                        break
                if not broke and cost < best:
                    best, best_letter = cost, c
                if _HAVE_TQDM and self._verbose:
                    bar.set_postfix(best=f"{best / self._total:.4f}", states=len(self.memo))
        except KeyboardInterrupt:
            el = time.perf_counter() - self._t0
            done = order.index(c) + 1 if c in order else 0
            _emit(f"\ninterrupted after {el:.1f}s: {done}/{len(order)} openers, "
                  f"{len(self.memo):,} states; best avg so far = {best / self._total:.4f}")
            raise
        finally:
            if _HAVE_TQDM and self._verbose:
                bar.close()

        self.memo[(root.tobytes(), cap)] = (best, best_letter)
        return best, best_letter

    # ---- progress ----------------------------------------------------------
    def _reset_progress(self) -> None:
        self._path = {}
        self._track_depth = 4
        self._deep_d = self._deep_n = 0
        self._op = ("-", 0, 0)
        self._l2_total = self._l2_done = self._l2_words = 0

    def _maybe_beat(self) -> None:
        if not self._verbose:
            return
        now = time.perf_counter()
        if now - self._last_beat < self._heartbeat:
            return
        self._last_beat = now
        el = now - self._t0
        ch, ok, on = self._op
        l2pct = 100.0 * self._l2_words / self.N if self.N else 0.0
        p2 = self._path.get(2)
        l3 = (f"grp(size {p2[0]}) cand '{ALPHABET[p2[1]]}' #{p2[2] + 1}, subgrp {p2[3] + 1}/{p2[4]}"
              if p2 else "--")
        _emit(f"cap {self._cap} | opener '{ch}' {ok}/{on} | "
              f"L2 {self._l2_done}/{self._l2_total} grp, {self._l2_words}/{self.N} words ({l2pct:.0f}%) | "
              f"L3 {l3} | deepest depth {self._deep_d} |S|={self._deep_n} | "
              f"{len(self.memo):,} states, {el:.0f}s")
        self._deep_d = self._deep_n = 0

    # ---- optimal tree (moves are now reliably cached by the search) --------
    def _move(self, S: np.ndarray, r) -> int:
        """Optimal first letter for (S, r): the move stored by the search (now
        always optimal for cached nodes). A node that was left as a lower bound
        (never fully solved) is solved once here with an INF budget, which caches
        it exact -- rare, and cheap since its children are already memoized."""
        if S.shape[0] == 2:
            return self._sep_two(int(S[0]), int(S[1]))[1]
        key = (S.tobytes(), r)
        e = self.memo.get(key)
        if e is None:
            self._V(S, r, INF, 99)
            e = self.memo.get(key)
        return e[1] if e is not None else -1

    # ---- public API --------------------------------------------------------
    def solve(self, freq=None, *, max_misses=None, verbose: bool = True,
              heartbeat: float = 1.0, ub_depth: int = 8, opener_ub_depth: int = 2) -> float:
        """Optimal (capped) average misses for a single cap (``max_misses=None`` =
        uncapped). Resets the memo and fills it with the optimal tree."""
        self.freq = self.game._coerce_freq(freq)
        self.memo, self.lb = {}, {}
        self._ubbuf = np.zeros(self.N, dtype=np.float64)
        self._verbose, self._heartbeat, self._ub_depth = verbose, heartbeat, ub_depth
        self._opener_ub_depth = opener_ub_depth
        self._total = float(self.freq.sum())
        self._cap = max_misses
        self._solve_cap = max_misses
        self._reset_progress()
        self._calls = 0
        self._t0 = self._last_beat = time.perf_counter()
        if self.N <= 1:
            return 0.0
        if verbose:
            print(f"length {self.game.length}: {self.N:,} words  "
                  f"(greedy avg {self.game.average_misses(self.freq):.4f}); "
                  f"cap = {max_misses}", flush=True)
        best, _ = self._solve_root(max_misses)
        avg = best / self._total
        if verbose:
            el = time.perf_counter() - self._t0
            print(f"length {self.game.length}: OPTIMAL avg = {avg:.4f} "
                  f"(vs greedy {self.game.average_misses(self.freq):.4f}); "
                  f"{len(self.memo):,} states in {el:.1f}s", flush=True)
        return avg

    def deepen(self, freq=None, *, verbose: bool = True, heartbeat: float = 1.0,
               ub_depth: int = 8, opener_ub_depth: int = 2, max_cap: int = 64,
               log_path=None, save_trees: bool = False) -> tuple:
        """Iterative deepening on the miss cap: solve cap = 1, 2, 3, ... reusing the
        memo, stopping when the optimal tree's max misses < cap (cap non-binding =
        the true uncapped optimum). Writes one CSV row per completed cap to
        ``log_path`` (flushed immediately, so a killed run keeps its curve).
        Returns (avg, converged_cap, results)."""
        self.freq = self.game._coerce_freq(freq)
        self.memo, self.lb = {}, {}
        self._ubbuf = np.zeros(self.N, dtype=np.float64)
        self._verbose, self._heartbeat, self._ub_depth = verbose, heartbeat, ub_depth
        self._opener_ub_depth = opener_ub_depth
        self._total = float(self.freq.sum())
        self._reset_progress()
        root = np.arange(self.N, dtype=np.int32)

        g = self.game
        greedy_avg = g.average_misses(self.freq)
        greedy_max = int(g.per_word_misses(self.freq).max())
        if verbose:
            print(f"length {g.length}: {self.N:,} words  (greedy avg {greedy_avg:.4f}, "
                  f"greedy max misses {greedy_max})", flush=True)

        fh = None
        if log_path is not None:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            fh = log_path.open("w")
            fh.write("cap,capped_avg,delta,states,seconds,greedy_avg,converged\n")
            fh.flush()

        results, prev_avg = [], None
        try:
            for cap in range(1, max_cap + 1):
                self._cap = cap
                self._solve_cap = cap
                self._calls = 0
                self._deep_d = self._deep_n = 0
                self._t0 = self._last_beat = time.perf_counter()
                best, _ = self._solve_root(cap)
                avg = best / self._total
                el = time.perf_counter() - self._t0
                # V(root, cap) is non-decreasing in cap; it stops rising exactly when
                # the cap stops binding -> that's the uncapped optimum (no tree walk).
                delta = 0.0 if prev_avg is None else avg - prev_avg
                converged = prev_avg is not None and delta < 1e-9
                print(f"cap {cap:2d}: capped optimal avg = {avg:.4f}  |  +{delta:.4f} vs prev cap"
                      f"  |  {len(self.memo):,} states, {el:.1f}s", flush=True)
                results.append((cap, avg))
                if fh:
                    fh.write(f"{cap},{avg:.6f},{delta:.6f},{len(self.memo)},{el:.2f},"
                             f"{greedy_avg:.6f},{int(converged)}\n")
                    fh.flush()
                if save_trees and log_path is not None:   # optimal tree for this cap
                    tp = log_path.with_name(f"{log_path.stem}_cap{cap:02d}.json")
                    self._verbose = False                 # no heartbeats during the walk
                    t = time.perf_counter()
                    self.save_tree(tp)
                    self._verbose = verbose
                    if verbose:
                        print(f"        saved tree -> {tp.name} ({time.perf_counter() - t:.1f}s)",
                              flush=True)
                if converged:                             # cap stopped binding -> true optimum
                    print(f"CONVERGED at cap {cap - 1} (max misses = {cap - 1}): uncapped "
                          f"OPTIMAL avg = {avg:.4f}  (vs greedy {greedy_avg:.4f})", flush=True)
                    return avg, cap - 1, results
                prev_avg = avg
            print(f"stopped at max_cap={max_cap} (cap still binding)", flush=True)
            return results[-1][1], max_cap, results
        finally:
            if fh:
                fh.close()

    def optimal_first_letter(self) -> str:
        return ALPHABET[self._move(np.arange(self.N, dtype=np.int32), self._solve_cap)]

    def trace(self, word: str) -> list[tuple[str, bool]]:
        """OPTIMAL guess sequence for one word (walk the stored tree). Needs a prior
        ``solve``/``deepen`` (uses that run's cap)."""
        if self.freq is None:
            raise RuntimeError("call solve()/deepen() first")
        i = self._index[word]
        S = np.arange(self.N, dtype=np.int32)
        r = self._solve_cap
        seq, guessed = [], 0
        while S.shape[0] > 1 and r != 0:
            c = self._move(S, r)
            if c < 0:
                break
            miss = self.masks[i, c] == 0
            seq.append((ALPHABET[c], not miss))
            if miss and r is not None:
                r -= 1
            S = S[self.masks[S, c] == self.masks[i, c]]
            guessed |= 1 << c
        for c in range(26):                              # finish (remaining hits)
            if self.masks[i, c] and not (guessed >> c) & 1:
                seq.append((ALPHABET[c], True))
                guessed |= 1 << c
        return seq

    # ---- the optimal decision tree (serializable) --------------------------
    def _pattern_str(self, c: int, mask: int) -> str:
        """e.g. letter 'e', length 4, mask {0,2} -> 'e_e_'; mask 0 -> '____' (absent)."""
        return "".join(ALPHABET[c] if (mask >> p) & 1 else "_"
                       for p in range(self.game.length))

    def _build_tree(self, S: np.ndarray, r) -> dict:
        n = S.shape[0]
        if n <= 1:
            return {"word": self.words[int(S[0])]} if n == 1 else {}
        if r == 0:                                        # capped out: these words are lost
            return {"capped": [self.words[int(i)] for i in S]}
        c = self._move(S, r)
        pats = self.masks[S, c]
        branches = {self._pattern_str(c, int(pv)):
                    self._build_tree(S[pats == pv], r - 1 if (r is not None and pv == 0) else r)
                    for pv in np.unique(pats)}
        return {"guess": ALPHABET[c], "n": n, "branches": branches}

    def optimal_tree(self) -> dict:
        """The optimal decision tree for the last solved cap: nested
        {guess, branches:{pattern: subtree}}; leaves are {word} or {capped:[...]}."""
        if self.freq is None:
            raise RuntimeError("call solve()/deepen() first")
        return self._build_tree(np.arange(self.N, dtype=np.int32), self._solve_cap)

    def save_tree(self, path) -> None:
        Path(path).write_text(json.dumps(self.optimal_tree()))


# ---- brute-force references (tiny synthetic instances only) --------------------
def optimal_bruteforce(game: GreedyGame, freq=None, *, cap=None) -> float:
    """Unpruned/unmemoized optimal (capped) average -- an oracle for a handful of
    words. Use a small synthetic ``GreedyGame(length, words=[...])``."""
    f = game._coerce_freq(freq)

    def V(S, r):
        if S.shape[0] <= 1 or r == 0:
            return 0.0
        best = INF
        for c in range(26):
            pats = game.masks[S, c]
            uniq = np.unique(pats)
            if uniq.shape[0] == 1:
                continue
            cost = 0.0
            for pv in uniq:
                grp = S[pats == pv]
                if pv == 0:
                    cost += float(f[grp].sum()) + V(grp, r - 1 if r is not None else None)
                else:
                    cost += V(grp, r)
            best = min(best, cost)
        return best

    return V(np.arange(game.N, dtype=np.int32), cap) / float(f.sum())


def _main(argv) -> None:
    lengths, weighted, uncapped, trees = [], None, False, True
    it = iter(argv)
    for a in it:
        if a == "--weighted":
            weighted = next(it, "greedy")
        elif a.startswith("--weighted="):
            weighted = a.split("=", 1)[1]
        elif a == "--uncapped":
            uncapped = True
        elif a == "--no-trees":
            trees = False
        elif not a.startswith("-"):
            lengths.append(int(a))
    lengths = lengths or [3]

    import freq_search
    for L in lengths:
        print(f"\n===== length {L} =====")
        game = GreedyGame(L)
        solver = OptimalSolver(game)
        pm = game.per_word_misses(None)
        print(f"greedy: avg {game.average_misses():.4f}, max misses {int(pm.max())}, "
              f"max guesses {max(len(game.trace(w)) for w in game.words)}")

        print("-- uniform --")
        if uncapped:
            solver.solve(None)
        else:
            solver.deepen(None, log_path=DATA_DIR / f"len{L:02d}_uniform.csv", save_trees=trees)

        if weighted:
            csv = freq_search._default_log_path(weighted, L)
            if not csv.exists():
                print(f"-- {weighted}: no run at {csv.parent.name}/{csv.name}, skipping --")
                continue
            s = freq_search.FrequencySearch.reconstruct(L, csv, objective=weighted)
            print(f"-- weighted ({weighted}) --")
            if uncapped:
                solver.solve(s.freq)
            else:
                solver.deepen(s.freq, log_path=DATA_DIR / f"len{L:02d}_{weighted}.csv",
                              save_trees=trees)


if __name__ == "__main__":
    _main(sys.argv[1:])

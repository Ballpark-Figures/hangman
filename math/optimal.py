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

Memory. The memo (exact values) and lb (lower bounds) are LRU caches with byte/
entry budgets defaulting to ~60% of system RAM -- sized for ONE solver at a time.
Nothing is evicted until a budget is actually reached; past that the coldest
entries are dropped and recomputed on demand, so results stay EXACT (the deep
caps just run slower rather than getting OOM-killed). Each completed cap is
checkpointed to ``lenNN_*.ckpt``, and a re-run resumes from it automatically.

Run ``python math/optimal.py <length> [max_cap] [--weighted greedy|best_opener]
[--uncapped] [--memo-bytes 14G] [--lb-cap N] [--fresh] [--no-trees]``  (--memo-bytes 0
and --lb-cap 0 opt out of the caps; --fresh ignores an existing checkpoint).
The optional 2nd positional (like winprob's) is the stop cap: deepen through that
cap then stop, leaving a checkpoint so a later run without --fresh resumes at the
next cap.  ``--max-cap N`` does the same and overrides the positional if both given.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np

from strategy import GreedyGame, ALPHABET
from tree_complete import complete_tree
from wordlist import DEFAULT_ZIPF, resolve_weighting, load as wl_load

try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except Exception:                       # pragma: no cover - tqdm is a listed dep
    _HAVE_TQDM = False

INF = float("inf")
# data split: committed results (csv logs + trees) vs machine-local resume files.
SHARED_DIR = Path(__file__).resolve().parent / "data" / "shared" / "optimal"   # committed
LOCAL_DIR = Path(__file__).resolve().parent / "data" / "local" / "optimal"     # gitignored (.ckpt)


def _emit(msg: str) -> None:
    (tqdm.write if _HAVE_TQDM else print)(msg)


class _LRUlb:
    """The lb (lower-bound) cache with an LRU size cap. lb only ever stores
    *bounds* used to prune re-visits; evicting one just forces a recompute that
    re-derives an equal-or-better bound, so the search stays EXACT -- the cap
    only trades some recompute for a hard ceiling on lb's memory. Module-level so
    it pickles into checkpoints. (The uncapped default stays a plain dict, which
    avoids the per-hit move_to_end cost on the hot path.)"""

    def __init__(self, cap: int):
        self.cap = cap
        self._d: OrderedDict = OrderedDict()

    def get(self, key, default=None):
        d = self._d
        v = d.get(key, default)
        if v is not default:
            d.move_to_end(key)                # mark most-recently-used
        return v

    def __setitem__(self, key, value):
        d = self._d
        if key in d:
            d[key] = value
            d.move_to_end(key)
        else:
            d[key] = value
            if len(d) > self.cap:
                d.popitem(last=False)         # evict least-recently-used

    def pop(self, key, default=None):
        return self._d.pop(key, default)

    def __contains__(self, key):
        return key in self._d

    def __len__(self):
        return len(self._d)


def _coerce_lb(lb_cap, existing=None):
    """Build the lb cache for the requested policy, carrying over ``existing``
    entries (a dict or _LRUlb from a checkpoint) if given. lb_cap None -> plain
    dict (uncapped); otherwise an LRU-capped cache."""
    items = None
    if existing is not None:
        items = existing._d if isinstance(existing, _LRUlb) else existing
    if lb_cap is None:
        return dict(items) if items is not None else {}
    lru = _LRUlb(lb_cap)
    if items is not None:
        for k, v in items.items():            # insertion order = LRU order; keeps last cap
            lru[k] = v
    return lru


def _converged_csv_results(path: Path):
    """If a deepen CSV already proves convergence (any row with ``converged==1``),
    return its ``[(cap, capped_avg), ...]``; else ``None``. A converged result is
    the true uncapped optimum, so it's a completion marker just like a finished
    checkpoint -- a rerun can treat it as done and skip recomputation. Parsed by
    hand (no csv import) and defensively: a malformed/short file returns None."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    if len(lines) < 2:
        return None
    header = lines[0].split(",")
    try:
        capi, avgi, convi = (header.index("cap"), header.index("capped_avg"),
                             header.index("converged"))
    except ValueError:
        return None
    rows, converged = [], False
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) <= convi:
            continue
        try:
            rows.append((int(parts[capi]), float(parts[avgi])))
        except ValueError:
            continue
        if parts[convi].strip() == "1":
            converged = True
    return rows if (converged and rows) else None


# Calibrated real RSS cost of one memo entry: this fixed overhead (Python bytes
# key object + value tuple + dict slot + correlated lb growth) PLUS the key's
# length. Measured ~520 B/entry marginal on len3 (key averages ~160 B), i.e.
# ~360 B fixed + key. A memo byte budget is charged with this so it maps to real
# gigabytes; leave headroom below it for transient recursion memory.
MEMO_ENTRY_OVERHEAD = 360
LB_ENTRY_BYTES = 450                    # same, for an lb entry (float value, no tuple)

# Default memory policy. The caches (memo + lb) are held to this share of system
# RAM; the rest MUST cover transient recursion memory and heap fragmentation from
# the LRU churn -- which GROW WITH CAP DEPTH. Measured on this 28 GB box: at 0.45
# the deep short-word lengths (3/4/5, max misses 12-14) pushed RSS to ~22 GB and
# started swapping to disk, which is far slower than the in-RAM recompute the cap
# is meant to trade for. 0.30 keeps the memo near ~7 GB so caches + transient +
# frag fit with headroom even at the deepest caps. Shallower lengths only ever
# used a fraction of this, so nothing is lost there. ASSUMES ONE SOLVER AT A TIME.
# The deeper the length, the lower this wants to be -- drop to 0.25 (or pass
# --memo-bytes) if the very deepest caps still swap.
DEFAULT_BUDGET_FRACTION = 0.30
LB_BUDGET_SHARE = 0.20                  # of the cache budget; the memo gets the rest


def _system_ram_bytes():
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return None


def _auto_budgets():
    """(memo_bytes, lb_cap) sized off system RAM. (None, None) if RAM is unknown,
    which just falls back to the old uncapped behaviour."""
    ram = _system_ram_bytes()
    if not ram:
        return None, None
    budget = int(ram * DEFAULT_BUDGET_FRACTION)
    lb_bytes = int(budget * LB_BUDGET_SHARE)
    return budget - lb_bytes, max(1, lb_bytes // LB_ENTRY_BYTES)


class _LRUmemo:
    """The memo (exact-value DP table) under an LRU byte budget. Each entry costs
    MEMO_ENTRY_OVERHEAD + len(key) bytes (calibrated to real RSS). Evicting a
    value only forces its recompute -> still EXACT, just slower. Module-level so
    it pickles into checkpoints. The uncapped default stays a plain dict."""

    def __init__(self, budget: int):
        self.budget = budget                  # bytes
        self.bytes = 0
        self._d: OrderedDict = OrderedDict()

    @staticmethod
    def _charge(key) -> int:
        return MEMO_ENTRY_OVERHEAD + len(key[0])

    def get(self, key, default=None):
        d = self._d
        v = d.get(key, default)
        if v is not default:
            d.move_to_end(key)
        return v

    def __setitem__(self, key, value):
        d = self._d
        if key in d:
            d[key] = value
            d.move_to_end(key)
            return
        d[key] = value
        self.bytes += self._charge(key)
        while self.bytes > self.budget and len(d) > 1:      # keep at least the newest
            k, _ = d.popitem(last=False)                    # evict least-recently-used
            self.bytes -= self._charge(k)

    def pop(self, key, default=None):
        if key in self._d:
            self.bytes -= self._charge(key)
        return self._d.pop(key, default)

    def __contains__(self, key):
        return key in self._d

    def __len__(self):
        return len(self._d)


def _coerce_memo(memo_bytes, existing=None):
    """Build the memo for the requested policy, carrying over ``existing`` entries
    (a dict or _LRUmemo from a checkpoint). memo_bytes None -> plain dict; else an
    LRU byte-budgeted memo (which may immediately evict down to the budget)."""
    items = None
    if existing is not None:
        items = existing._d if isinstance(existing, _LRUmemo) else existing
    if memo_bytes is None:
        return dict(items) if items is not None else {}
    m = _LRUmemo(memo_bytes)
    if items is not None:
        for k, v in items.items():
            m[k] = v
    return m


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
        # Word indices are the memo key bytes; use the narrowest int that holds
        # them (uint16 for any realistic wordlist) to halve key size. Truncation
        # would silently corrupt keys, so widen if N ever exceeds uint16.
        self._idt = np.uint16 if self.N <= np.iinfo(np.uint16).max else np.int32
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
            self._maybe_checkpoint()                      # mid-cap save (time-gated)

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
            self.lb.pop(key, None)                         # exact now -> drop stale lower bound
            return best
        self.lb[key] = best if lbv is None else max(lbv, best)
        return best

    # ---- root (opener-by-opener, for progress) -----------------------------
    def _solve_root(self, cap) -> tuple[float, int]:
        f, root = self.freq, np.arange(self.N, dtype=self._idt)
        MS = self.masks[root]
        fR = f[root]
        splits = MS.min(0) != MS.max(0)
        w_abs_all = fR @ (MS == 0)
        order_arr = np.argsort(fR @ (MS > 0))[::-1]
        order = [int(c) for c in order_arr if splits[int(c)]]

        if not order:                                     # no letter distinguishes the set,
            self.memo[(root.tobytes(), cap)] = (0.0, -1)  # i.e. N <= 1: word already known
            return 0.0, -1

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
        # periodic (mid-cap) checkpointing -- off unless deepen() arms it
        self._ckpt_path = None
        self._ckpt_interval = 0.0
        self._ckpt_last = 0.0
        self._ckpt_state = None                          # (last_completed_cap, prev_avg, results)

    def _maybe_checkpoint(self) -> None:
        """Mid-cap checkpoint, so a kill during a multi-hour cap loses at most one
        interval instead of the whole cap. We record the last COMPLETED cap but
        ship the current (warmer) memo: its V(S, r) values are exact regardless of
        which cap was in flight, so resuming re-runs that cap with most of its work
        already cached."""
        if self._ckpt_path is None or self._ckpt_interval <= 0:
            return
        now = time.perf_counter()
        if now - self._ckpt_last < self._ckpt_interval:
            return
        self._ckpt_last = now                            # set first: a slow dump must not re-trigger
        cap_done, prev_avg, results = self._ckpt_state
        t = time.perf_counter()
        self._save_checkpoint(self._ckpt_path, cap_done, prev_avg, results)
        if self._verbose:
            _emit(f"        [periodic] checkpoint -> {self._ckpt_path.name} "
                  f"({len(self.memo):,} states, {time.perf_counter() - t:.1f}s)")
        self._ckpt_last = time.perf_counter()            # don't count the dump against the interval

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
              heartbeat: float = 60.0, ub_depth: int = 8, opener_ub_depth: int = 2) -> float:
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

    # ---- checkpoint / resume ----------------------------------------------
    def _signature(self) -> str:
        """Identifies the exact problem (length + word set + frequencies). A
        checkpoint is only reused when this matches, so a stale file from a
        different wordlist or weighting is never silently applied."""
        h = hashlib.sha256()
        h.update(str(self.game.length).encode())
        h.update(np.ascontiguousarray(self.freq, dtype=np.float64).tobytes())
        return h.hexdigest()

    def _save_checkpoint(self, path: Path, cap: int, prev_avg, results) -> None:
        """Atomically dump the reusable search state after completing ``cap``.
        The memo holds exact V(S, r) values that stay valid across caps, so a
        reload can continue from cap+1 without redoing finished caps. Written to
        a temp file then renamed, so a kill mid-write can't corrupt the resume
        point. ``prev_avg`` is this cap's avg (the baseline for the next delta)."""
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("wb") as fh:
            pickle.dump({"signature": self._signature(), "cap": cap,
                         "prev_avg": prev_avg, "results": results,
                         "memo": self.memo, "lb": self.lb}, fh,
                        protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)                                 # atomic on same filesystem

    def _load_checkpoint(self, path: Path):
        """Return the saved state if it matches this problem, else None (a
        mismatch or unreadable file just means we start fresh)."""
        try:
            with path.open("rb") as fh:
                data = pickle.load(fh)
        except Exception:
            return None
        return data if data.get("signature") == self._signature() else None

    def deepen(self, freq=None, *, verbose: bool = True, heartbeat: float = 60.0,
               ub_depth: int = 8, opener_ub_depth: int = 2, max_cap: int = 64,
               log_path=None, save_trees: bool = False,
               checkpoint=None, resume: bool = True, lb_cap="auto",
               memo_bytes="auto", checkpoint_interval: float = 3600.0) -> tuple:
        """Iterative deepening on the miss cap: solve cap = 1, 2, 3, ... reusing the
        memo, stopping the FIRST cap whose optimal tree leaves no word capped --
        that proves nothing was truncated, so its value is the true uncapped
        optimum and the next cap is provably unneeded (skips the last, largest
        cap when the deepest word resolves on a miss rather than a later hit). An
        avg-plateau check is kept as a defensive fallback. Writes one CSV row per
        completed cap to ``log_path`` (flushed immediately, so a killed run keeps
        its curve). Returns (avg, max_misses, results)."""
        self.freq = self.game._coerce_freq(freq)
        self._ubbuf = np.zeros(self.N, dtype=np.float64)
        self._verbose, self._heartbeat, self._ub_depth = verbose, heartbeat, ub_depth
        self._opener_ub_depth = opener_ub_depth
        self._total = float(self.freq.sum())
        self._reset_progress()

        # "auto" -> size the caches off system RAM; None -> explicitly uncapped.
        if memo_bytes == "auto" or lb_cap == "auto":
            auto_memo, auto_lb = _auto_budgets()
            if memo_bytes == "auto":
                memo_bytes = auto_memo
            if lb_cap == "auto":
                lb_cap = auto_lb

        g = self.game
        greedy_avg = g.average_misses(self.freq)
        greedy_max = int(g.per_word_misses(self.freq).max())

        # A converged CSV is itself a completion marker: a prior run already proved
        # the true uncapped optimum for this (length, weighting), so no cap -- however
        # large -- can change it. Treat it like a finished checkpoint and skip, unless
        # resume is off (--fresh). Checked before the log file is (re)opened below so
        # a converged result is never truncated by a rerun.
        if resume and log_path is not None:
            done = _converged_csv_results(Path(log_path))
            if done is not None:
                cap, avg = done[-1]
                if verbose:
                    print(f"length {g.length}: {Path(log_path).name} already converged "
                          f"(cap {cap}, optimal avg {avg:.4f}) -- nothing to do "
                          f"(pass --fresh to recompute)", flush=True)
                return avg, None, done

        # Resume from a matching checkpoint if one exists, else start clean. The
        # memo's exact V(S, r) values stay valid across caps, so we pick up at the
        # first cap not yet completed.
        ckpt = Path(checkpoint) if checkpoint is not None else None
        results, prev_avg, start_cap, resumed = [], None, 1, False
        if ckpt is not None and resume and ckpt.exists():
            data = self._load_checkpoint(ckpt)
            if data is not None:
                self.memo = _coerce_memo(memo_bytes, data["memo"])   # re-apply cap policies
                self.lb = _coerce_lb(lb_cap, data["lb"])
                results, prev_avg = data["results"], data["prev_avg"]
                start_cap, resumed = data["cap"] + 1, True
                if verbose:
                    done = (f"caps 1..{data['cap']} done" if data["cap"] >= 1
                            else "no cap finished yet")
                    print(f"resuming from {ckpt.name}: {done} "
                          f"({len(self.memo):,} states cached); continuing at cap "
                          f"{start_cap}", flush=True)
            elif verbose:
                print(f"ignoring {ckpt.name}: signature does not match this "
                      f"wordlist/length; starting fresh", flush=True)
        if not resumed:
            self.memo, self.lb = _coerce_memo(memo_bytes), _coerce_lb(lb_cap)

        if verbose:
            print(f"length {g.length}: {self.N:,} words  (greedy avg {greedy_avg:.4f}, "
                  f"greedy max misses {greedy_max})", flush=True)
            if memo_bytes is None and lb_cap is None:
                print("caches UNCAPPED (may OOM on deep caps)", flush=True)
            else:
                ram = _system_ram_bytes()
                ramtxt = f" of {ram/1e9:.0f} GB RAM" if ram else ""
                mtxt = f"{memo_bytes/1e9:.1f} GB" if memo_bytes is not None else "uncapped"
                ltxt = (f"{lb_cap:,} entries (~{lb_cap*LB_ENTRY_BYTES/1e9:.1f} GB)"
                        if lb_cap is not None else "uncapped")
                print(f"memory caps{ramtxt}: memo {mtxt}, lb {ltxt} -- LRU, exact "
                      f"(evicts only at the budget; evicted values are recomputed)",
                      flush=True)

        fh = None
        if log_path is not None:
            log_path = Path(log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Append when resuming onto existing rows; otherwise (fresh, or a resume
            # from a mid-cap save taken before cap 1 finished) start the file.
            has_rows = resumed and log_path.exists() and log_path.stat().st_size > 0
            fh = log_path.open("a" if has_rows else "w")
            if not has_rows:
                fh.write("cap,capped_avg,delta,states,seconds,greedy_avg,converged\n")
                fh.flush()

        # arm the mid-cap checkpointer (it re-saves the live memo on a timer)
        self._ckpt_path = ckpt
        self._ckpt_interval = float(checkpoint_interval or 0)
        if ckpt is not None and self._ckpt_interval > 0 and verbose:
            iv = self._ckpt_interval
            ivtxt = f"{iv/60:.0f} min" if iv >= 60 else f"{iv:.0f}s"
            print(f"periodic checkpoint every {ivtxt} (mid-cap; a kill loses at most "
                  f"that much, not the whole cap)", flush=True)

        try:
            for cap in range(start_cap, max_cap + 1):
                self._cap = cap
                self._solve_cap = cap
                self._calls = 0
                self._deep_d = self._deep_n = 0
                self._t0 = self._last_beat = time.perf_counter()
                # A mid-cap save records the last COMPLETED cap (this one is in
                # flight) but carries the live memo, so a resume redoes only what
                # this cap had not yet cached.
                self._ckpt_state = (cap - 1, prev_avg, list(results))
                self._ckpt_last = time.perf_counter()
                best, _ = self._solve_root(cap)
                avg = best / self._total
                el = time.perf_counter() - self._t0
                delta = 0.0 if prev_avg is None else avg - prev_avg
                # Convergence proof: if this cap's optimal tree leaves NO word
                # capped, nothing was truncated, so its value IS the uncapped
                # optimum -- the next cap is provably unneeded (skips the last,
                # largest cap). ``max_miss`` is then the true max misses. The
                # avg-plateau is kept only as a defensive fallback; it can never
                # fire before zero-capped does.
                root = np.arange(self.N, dtype=self._idt)
                capped, max_miss = self._tree_stats(root, cap, cap)
                # Upper bound on the true optimum: finish the capped groups greedily
                # (capped-optimal tree above the cap, greedy below). Equals ``avg``
                # when nothing is capped, so the two brackets the optimum and meet
                # at convergence.
                upper = avg + self._capped_greedy_cost(root, cap) / self._total
                plateau = prev_avg is not None and delta < 1e-9
                converged = capped == 0 or plateau
                conv_misses = max_miss if capped == 0 else cap - 1
                print(f"cap {cap:2d}: capped optimal avg = {avg:.4f}  |  greedy-completed upper "
                      f"= {upper:.4f}  |  +{delta:.4f} vs prev cap  |  {capped:,} capped, "
                      f"{len(self.memo):,} states, {el:.1f}s", flush=True)
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
                if converged:                             # cap fully resolves -> true optimum
                    if ckpt is not None:
                        ckpt.unlink(missing_ok=True)      # run complete -> no resume needed
                    # a cap is actually saved only when zero-capped fires while the
                    # average is still rising (the old plateau check would have needed
                    # one more cap to see it flatten)
                    saved = " (skipped the confirmation cap)" if (capped == 0 and not plateau) else ""
                    print(f"CONVERGED at cap {cap} (max misses = {conv_misses}): uncapped "
                          f"OPTIMAL avg = {avg:.4f}  (vs greedy {greedy_avg:.4f}){saved}",
                          flush=True)
                    return avg, conv_misses, results
                if ckpt is not None:                      # resume point for cap+1
                    t = time.perf_counter()
                    self._save_checkpoint(ckpt, cap, avg, results)
                    if verbose:
                        print(f"        checkpoint -> {ckpt.name} "
                              f"({time.perf_counter() - t:.1f}s)", flush=True)
                prev_avg = avg
            print(f"stopped at max_cap={max_cap} (cap still binding)", flush=True)
            return results[-1][1], max_cap, results
        finally:
            if fh:
                fh.close()

    def optimal_first_letter(self) -> str:
        return ALPHABET[self._move(np.arange(self.N, dtype=self._idt), self._solve_cap)]

    def trace(self, word: str) -> list[tuple[str, bool]]:
        """OPTIMAL guess sequence for one word (walk the stored tree). Needs a prior
        ``solve``/``deepen`` (uses that run's cap)."""
        if self.freq is None:
            raise RuntimeError("call solve()/deepen() first")
        i = self._index[word]
        S = np.arange(self.N, dtype=self._idt)
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

    def _tree_stats(self, S: np.ndarray, r, cap) -> tuple[int, int]:
        """(capped words, max miss-depth) of the cap-``r`` optimal tree, walked
        like _build_tree but without constructing it. ``capped`` counts words the
        tree leaves tied at r == 0; ``max miss-depth`` is the deepest actual miss
        count (cap - r) to any leaf. ZERO capped PROVES the capped value equals
        the uncapped optimum -- nothing was truncated -- so the next cap is
        provably unnecessary (deepen's early stop). The tree has only ~one path
        per word, so this walk is cheap next to the solve."""
        n = S.shape[0]
        if n <= 1:                                        # resolved: misses spent = cap - r
            return 0, cap - r
        if r == 0:                                        # tied, budget spent -> capped
            return n, cap
        c = self._move(S, r)
        pats = self.masks[S, c]
        capped, depth = 0, 0
        for pv in np.unique(pats):
            cc, dd = self._tree_stats(S[pats == pv], r - 1 if pv == 0 else r, cap)
            capped += cc
            depth = max(depth, dd)
        return capped, depth

    def _capped_greedy_cost(self, S: np.ndarray, r) -> float:
        """Frequency-weighted misses to FINISH every capped group of the cap-``r``
        optimal tree with greedy. Added to the capped optimal value it gives a
        valid UPPER bound on the true (uncapped) optimum: "capped-optimal tree
        above the cap, greedy below it" is a real strategy, so its average can only
        exceed the optimum. Reaching a capped node spends exactly ``cap`` misses on
        the path (already in the capped value), so each capped group contributes
        just its greedy completion, ``_greedy_ub(group)``. Same cheap
        one-path-per-word walk as _tree_stats; zero capped -> 0.0."""
        n = S.shape[0]
        if n <= 1:
            return 0.0
        if r == 0:                                        # capped group -> finish greedily
            return self._greedy_ub(S, None)
        c = self._move(S, r)
        pats = self.masks[S, c]
        cost = 0.0
        for pv in np.unique(pats):
            cost += self._capped_greedy_cost(S[pats == pv], r - 1 if pv == 0 else r)
        return cost

    def optimal_tree(self) -> dict:
        """The optimal decision tree for the last solved cap: nested
        {guess, branches:{pattern: subtree}}; leaves are {word} or {capped:[...]}.

        Determined leaves are extended to word COMPLETION (single-branch tails of
        guaranteed hits) via ``complete_tree`` -- the game continues guessing until
        the word is fully revealed, not just until it is uniquely determined. Those
        tail guesses are all hits, so the optimal value is unchanged."""
        if self.freq is None:
            raise RuntimeError("call solve()/deepen() first")
        return complete_tree(
            self._build_tree(np.arange(self.N, dtype=self._idt), self._solve_cap))

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
    def _parse_bytes(s):                                 # "14G" / "512M" / "2000000000"
        s = s.strip().upper()
        mult = {"K": 10**3, "M": 10**6, "G": 10**9, "T": 10**12}
        if s and s[-1] in mult:
            return int(float(s[:-1]) * mult[s[-1]])
        return int(s)

    # lb_cap / memo_bytes default to "auto" (sized off system RAM); pass 0 to opt out.
    pos, weighted, uncapped, trees, fresh = [], None, False, True, False
    lb_cap = memo_bytes = "auto"
    save_every = 3600.0                                  # seconds between mid-cap saves (1 hour)
    max_cap = None                                       # None -> from 2nd positional, else default 64
    variant = "us"                                       # dictionary variant (us default; e.g. gb)
    it = iter(argv)
    for a in it:
        if a == "--weighted":
            weighted = next(it, "greedy")
        elif a.startswith("--weighted="):
            weighted = a.split("=", 1)[1]
        elif a == "--variant":
            variant = next(it, "us")
        elif a.startswith("--variant="):
            variant = a.split("=", 1)[1]
        elif a == "--uncapped":
            uncapped = True
        elif a == "--no-trees":
            trees = False
        elif a == "--fresh":                             # ignore any existing checkpoint
            fresh = True
        elif a == "--lb-cap":                            # LRU-cap the lb cache (exact)
            lb_cap = int(next(it, 0)) or None
        elif a.startswith("--lb-cap="):
            lb_cap = int(a.split("=", 1)[1]) or None
        elif a == "--memo-bytes":                        # LRU byte budget on the memo (exact)
            memo_bytes = _parse_bytes(next(it, "0")) or None
        elif a.startswith("--memo-bytes="):
            memo_bytes = _parse_bytes(a.split("=", 1)[1]) or None
        elif a == "--save-every":                        # mid-cap checkpoint, in MINUTES (0=off)
            save_every = float(next(it, 60)) * 60.0
        elif a.startswith("--save-every="):
            save_every = float(a.split("=", 1)[1]) * 60.0
        elif a == "--max-cap":                           # deepen up to this cap, then stop (resumable)
            max_cap = int(next(it, 64))
        elif a.startswith("--max-cap="):
            max_cap = int(a.split("=", 1)[1])
        elif not a.startswith("-"):
            pos.append(int(a))
    # Positionals mirror winprob: <length> [max_cap].  The optional 2nd number
    # sets the stop cap (an explicit --max-cap flag overrides it); default 64.
    length = pos[0] if pos else 3
    if max_cap is None:
        max_cap = pos[1] if len(pos) > 1 else 64
    lengths = [length]
    # Per-variant output dirs: "us" keeps the original data/shared/optimal/ and
    # data/local/optimal/; other variants go under data/{shared,local}/<variant>/optimal/.
    shared_dir = SHARED_DIR if variant == "us" else SHARED_DIR.parent / variant / "optimal"
    local_dir = LOCAL_DIR if variant == "us" else LOCAL_DIR.parent / variant / "optimal"
    shared_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)
    if variant != "us":
        print(f"[variant {variant!r}] output -> {shared_dir}")

    for L in lengths:
        print(f"\n===== length {L} =====")
        words = None if variant == "us" else [
            w.text for w in wl_load(min_len=L, max_len=L, variant=variant)]
        game = GreedyGame(L, words=words)
        solver = OptimalSolver(game)
        pm = game.per_word_misses(None)
        print(f"greedy: avg {game.average_misses():.4f}, max misses {int(pm.max())}, "
              f"max guesses {max(len(game.trace(w)) for w in game.words)}")

        # weighting chosen by --weighted: "uniform" (default), "zipf" (real word
        # frequency), or a freq_search objective (adversarial hardest-to-guess).
        weighting = weighted or "uniform"
        try:
            wfreq = resolve_weighting(weighting, L, variant=variant)
        except FileNotFoundError as e:                # freq_search obj not run yet
            print(f"-- {weighting}: {e}\n   skipping length {L} --")
            continue
        print(f"-- {weighting} --")
        if uncapped:
            solver.solve(wfreq)
        else:
            log = shared_dir / f"len{L:02d}_{weighting}.csv"
            solver.deepen(wfreq, log_path=log, save_trees=trees, max_cap=max_cap,
                          checkpoint=local_dir / f"{log.stem}.ckpt", resume=not fresh,
                          lb_cap=lb_cap, memo_bytes=memo_bytes,
                          checkpoint_interval=save_every)


if __name__ == "__main__":
    _main(sys.argv[1:])

"""Depth-cut decomposition prototype for the optimal solver -- a sandbox to play
with the "pin the subtree values at a chosen depth" idea.

THE IDEA (three tiers):
  depth <  D : top-level search, memoized whole (few shallow positions).
  depth == D : `cut_values` -- the optimal miss-count for each cut position,
               PINNED forever. Re-reaching a cut position (via a different guess
               order) is a free lookup that skips its entire subtree.
  depth >  D : each cut position is solved as an INDEPENDENT subproblem, reusing
               the exact _V (with its branch-and-bound). Its memo is either
               fresh-and-discarded (default) or a shared LRU across subproblems
               (--shared), so you can dial in cross-subproblem reuse. Subproblems
               are independent -> parallelizable across cores (not wired up yet).

Exact regardless of D and of the memo dial -- the cut changes computation, not
the answer.

KNOBS worth playing with:
  D (cut depth)        -- deeper cut = more, smaller subproblems (less peak
                          memory, more cross-subproblem recompute).
  SUBPROBLEM_UB_DEPTH  -- the depth a subproblem's root is solved at, i.e. how
                          tight its upper bound is (2 = opener_ub, 3+ = greedy).
  --shared N           -- share an N-entry LRU memo across subproblems instead of
                          discarding per subproblem (recaptures overlap). Single-
                          process only (mutually exclusive with --parallel).
  --parallel N         -- solve subproblems across N worker processes (3 phases:
                          enumerate cut positions, solve them in parallel, then
                          recombine). Scoped subproblems only. WATCH: peak * N
                          must fit RAM -- run single-process first to read `peak`,
                          then pick D and N so peak*N stays under your memory.

WHAT TO WATCH in the output:
  _V calls             -- total subproblem work (compare to the uncapped solve).
  peak subproblem      -- states in the largest single subproblem = the memory
                          bound per core. If this is << the full working set, the
                          decomposition fits where the whole doesn't (the point).

KNOWN COST: pinning EXACT cut values means each subproblem is solved fully, so
the decomposition gives up the cross-cut branch-and-bound pruning the integrated
solver has. That makes it slower on caps that already fit in RAM; the payoff is
only when the integrated solver would thrash (working set > RAM, i.e. deep caps).

usage:
  python math/cut_solver.py LENGTH CAP CUT_DEPTH [--shared N | --parallel N] [--weighted OBJ]
e.g.
  python math/cut_solver.py 3 8 4                     # scoped, single process
  python math/cut_solver.py 3 8 4 --shared 2000000   # 2M-entry shared LRU
  python math/cut_solver.py 3 12 4 --parallel 20     # 20 cores, the real target
"""
import sys, time
import multiprocessing as mp
from collections import OrderedDict
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import numpy as np
from optimal import OptimalSolver, INF, ALPHABET
from strategy import GreedyGame
try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except Exception:
    _HAVE_TQDM = False

SUBPROBLEM_UB_DEPTH = 2          # depth each subproblem root is solved at (bound tightness)
HEARTBEAT = 10.0                 # seconds between progress lines (like optimal.py's)


class SharedLRU(dict):
    """Optional shared memo across subproblems (byte-agnostic entry-count LRU)."""
    def __init__(self, cap):
        super().__init__(); self.cap = cap; self._d = OrderedDict(); self.evictions = 0
    def get(self, key, default=None):
        v = self._d.get(key, default)
        if v is not default: self._d.move_to_end(key)
        return v
    def __setitem__(self, key, value):
        d = self._d
        if key in d: d[key] = value; d.move_to_end(key); return
        d[key] = value
        if len(d) > self.cap: d.popitem(last=False); self.evictions += 1
    def pop(self, key, default=None): return self._d.pop(key, default)
    def __contains__(self, key): return key in self._d
    def __len__(self): return len(self._d)


def run(L, CAP, D, shared_cap=None, freq=None):
    s = OptimalSolver(length=L)
    s.freq = s.game._coerce_freq(freq)
    s._ubbuf = np.zeros(s.N, dtype=np.float64)
    s._verbose, s._heartbeat, s._ub_depth, s._opener_ub_depth = False, 1e9, 8, 2
    s._total = float(s.freq.sum())
    s._cap = s._solve_cap = CAP
    s._reset_progress()
    s._calls = 0
    s._t0 = s._last_beat = time.perf_counter()
    f, masks = s.freq, s.masks

    top_memo = {}
    cut_values = {}
    shared = SharedLRU(shared_cap) if shared_cap else None
    st = {"subs": 0, "hits": 0, "peak_sub": 0, "path": {}}

    # live heartbeat, mirroring optimal.py's -- _V already calls self._maybe_beat()
    # every 16384 calls, so overriding it here streams progress the same way.
    def heartbeat():
        now = time.perf_counter()
        if now - s._last_beat < HEARTBEAT:
            return
        s._last_beat = now
        el = now - s._t0
        cur = len(s.memo) if s.memo is not None else 0
        p = st["path"]
        # path[d] = (letter, letter_idx, n_letters, pat_idx, n_pats). Show the
        # LETTER-loop fraction (letter_idx/n_letters) at each level -- that's the
        # search progress, and its denominator is fixed per node (unlike the
        # per-letter pattern count, which jumps around).
        p0 = p.get(0)
        opener = f"opener '{p0[0]}' {p0[1]}/{p0[2]}" if p0 else "opener -/-"
        deeper = " ".join(f"L{d} {p[d][1]}/{p[d][2]}" for d in sorted(p) if 0 < d < D)
        print(f"cut@d{D} | {opener} | {deeper} | "
              f"subprob {st['subs']:,}, {st['hits']:,} hits | cur {cur:,} | "
              f"peak {st['peak_sub']:,} | {s._calls:,} calls, {el:.0f}s", flush=True)
    s._maybe_beat = heartbeat

    def subproblem(S, r):
        key = (S.tobytes(), r)
        v = cut_values.get(key)
        if v is not None:
            st["hits"] += 1
            return v
        st["subs"] += 1
        if shared is not None:
            before = len(shared)
            s.memo, s.lb = shared, {}
        else:
            s.memo, s.lb = {}, {}
        v = s._V(S, r, INF, SUBPROBLEM_UB_DEPTH)
        st["peak_sub"] = max(st["peak_sub"], len(s.memo) - (before if shared is not None else 0)
                             if shared is None else len(s.memo))
        if shared is None:
            s.memo = s.lb = None
        cut_values[key] = v
        return v

    def top(S, r, depth, bound):
        n = S.shape[0]
        if n <= 1 or r == 0:
            return 0.0
        if n == 2:
            return s._sep_two(int(S[0]), int(S[1]))[0]
        key = (S.tobytes(), r)
        e = top_memo.get(key)
        if e is not None:
            return e
        MS = masks[S]; fS = f[S]
        splits = MS.min(0) != MS.max(0)
        w_abs_all = fS @ (MS == 0)
        order = np.argsort(fS @ (MS > 0))[::-1]
        splitting = [int(c) for c in order if splits[int(c)]]
        best, achievable = bound, False
        for i, c in enumerate(splitting):
            w_abs = float(w_abs_all[c])
            if w_abs >= best:
                continue
            pats = MS[:, c]
            uniq = np.unique(pats)
            cost, broke = w_abs, False
            for j, pv in enumerate(uniq):
                # record where we are at this top level: which opener (letter) and
                # which of its pattern-branches -- the path down the top scaffold.
                st["path"][depth] = (ALPHABET[c], i + 1, len(splitting), j + 1, len(uniq))
                group = S[pats == pv]
                rr = r - 1 if pv == 0 else r
                nd = depth + 1
                cost += (subproblem(group, rr) if nd >= D
                         else top(group, rr, nd, best - cost))
                if cost >= best:
                    broke = True
                    break
            if not broke and cost < best:
                best, achievable = cost, True
        st["path"].pop(depth, None)            # left this level; drop stale deeper path
        if achievable:
            top_memo[key] = best
        return best

    root = np.arange(s.N, dtype=s._idt)
    t = time.perf_counter()
    val = top(root, CAP, 0, INF)
    el = time.perf_counter() - t
    return {"avg": val / s._total, "calls": s._calls, "subs": st["subs"],
            "hits": st["hits"], "peak_sub": st["peak_sub"],
            "top": len(top_memo), "cut": len(cut_values),
            "shared_evict": shared.evictions if shared else 0, "secs": el}


# ======================================================================
# PARALLEL MODE (--parallel N): subproblems are independent, so solve them
# across N cores. Three phases:
#   1. enumerate the cut positions (cheap top walk; greedy bounds so we only
#      collect the ones a real solve would reach -- a safe superset).
#   2. solve them all across a process pool -- the parallel win.
#   3. re-run the top search with the exact values filled in -> exact answer.
# Uses scoped subproblems (no shared memo), which is what parallelizes cleanly.
# WARNING: peak-subproblem * N must fit in RAM (each worker holds one). Pick D
# so `peak` (from a single-process run) times N stays under your memory.
# ======================================================================

def _make_solver(L, freq=None):
    s = OptimalSolver(length=L)
    s.freq = s.game._coerce_freq(freq)
    s._ubbuf = np.zeros(s.N, dtype=np.float64)
    s._verbose, s._heartbeat, s._ub_depth, s._opener_ub_depth = False, 1e9, 8, 2
    s._total = float(s.freq.sum())
    s._reset_progress()
    s._calls = 0
    s._t0 = s._last_beat = time.perf_counter()
    return s


_W = {}
def _init_worker(L, weighted):
    freq = None
    if weighted:
        import freq_search
        csv = freq_search._default_log_path(weighted, L)
        freq = freq_search.FrequencySearch.reconstruct(L, csv, objective=weighted).freq
    _W["s"] = _make_solver(L, freq)


def _solve_one(task):
    """Exact V(S, r) for one cut position, in a worker. Returns (key, value, peak)."""
    Sb, r = task
    s = _W["s"]
    S = np.frombuffer(Sb, dtype=s._idt).copy()
    s.memo, s.lb = {}, {}
    v = float(s._V(S, r, INF, SUBPROBLEM_UB_DEPTH))
    n = len(s.memo)
    s.memo = s.lb = None
    return (Sb, r), v, n


def _top_search(s, CAP, D, subproblem_fn):
    """Top-level branch-and-bound down to depth D, handing each cut position to
    subproblem_fn(S, r). Shared by phase 1 (record + greedy bound) and phase 3
    (exact lookup)."""
    masks, f = s.masks, s.freq
    top_memo = {}

    def top(S, r, depth, bound):
        n = S.shape[0]
        if n <= 1 or r == 0:
            return 0.0
        if n == 2:
            return s._sep_two(int(S[0]), int(S[1]))[0]
        if depth >= D:
            return subproblem_fn(S, r)
        key = (S.tobytes(), r)
        e = top_memo.get(key)
        if e is not None:
            return e
        MS = masks[S]; fS = f[S]
        splits = MS.min(0) != MS.max(0)
        w_abs_all = fS @ (MS == 0)
        order = np.argsort(fS @ (MS > 0))[::-1]
        best, ach = bound, False
        for c in (int(x) for x in order):
            if not splits[c]:
                continue
            w = float(w_abs_all[c])
            if w >= best:
                continue
            pats = MS[:, c]
            cost, broke = w, False
            for pv in np.unique(pats):
                group = S[pats == pv]
                rr = r - 1 if pv == 0 else r
                cost += top(group, rr, depth + 1, best - cost)
                if cost >= best:
                    broke = True
                    break
            if not broke and cost < best:
                best, ach = cost, True
        if ach:
            top_memo[key] = best
        return best

    return top(np.arange(s.N, dtype=s._idt), CAP, 0, INF)


def parallel_run(L, CAP, D, n_workers, freq=None, weighted=None):
    s = _make_solver(L, freq)

    # phase 1: enumerate cut positions. A greedy upper bound prunes the top
    # search to a safe superset of what phase 3 needs. CACHE the bound per
    # position -- the same cut position is reached once per guess-ordering, and
    # recomputing its greedy playout each time was the (super-linear) slowdown.
    t0 = time.perf_counter()
    cuts = {}
    gcache = {}
    prog = {"last": t0}
    def record(S, r):
        key = (S.tobytes(), r)
        v = gcache.get(key)
        if v is None:                        # first time we see this position
            v = s._greedy_ub(S, r)
            gcache[key] = v
            cuts[key] = None
            now = time.perf_counter()
            if now - prog["last"] > 5.0:      # progress so phase 1 isn't silent
                prog["last"] = now
                print(f"phase 1: {len(cuts):,} positions so far ({now - t0:.0f}s)",
                      flush=True)
        return v
    _top_search(s, CAP, D, record)
    print(f"phase 1: {len(cuts):,} cut positions collected  "
          f"({time.perf_counter() - t0:.1f}s)", flush=True)

    # phase 2: solve across the pool. chunksize=1 so the many tiny subproblems
    # keep flowing (and the bar keeps moving) even while a few workers grind on
    # huge ones -- with a larger chunk, a huge task strands its whole chunk.
    tasks = list(cuts.keys())
    cut_values, peak = {}, 0
    t0 = time.perf_counter()
    bar = tqdm(total=len(tasks), desc="phase 2", unit="sub", smoothing=0.05,
               disable=not _HAVE_TQDM)
    with mp.Pool(n_workers, initializer=_init_worker, initargs=(L, weighted)) as pool:
        for key, v, n in pool.imap_unordered(_solve_one, tasks, chunksize=1):
            cut_values[key] = v
            if n > peak:
                peak = n
                bar.set_postfix_str(f"peak {peak:,}/core (x{n_workers}={peak * n_workers:,})")
            bar.update(1)
    bar.close()
    par_secs = time.perf_counter() - t0
    print(f"phase 2: all {len(tasks):,} solved on {n_workers} cores, "
          f"peak {peak:,} states/core, {par_secs:.1f}s", flush=True)

    # phase 3: recombine (exact lookup; fall back to inline solve if ever missing)
    t0 = time.perf_counter()
    misses = [0]
    def lookup(S, r):
        v = cut_values.get((S.tobytes(), r))
        if v is None:
            misses[0] += 1
            s.memo, s.lb = {}, {}
            v = float(s._V(S, r, INF, SUBPROBLEM_UB_DEPTH))
            s.memo = s.lb = None
        return v
    val = _top_search(s, CAP, D, lookup)
    print(f"phase 3: recombined ({time.perf_counter() - t0:.1f}s, "
          f"{misses[0]} fallback solves)", flush=True)
    return {"avg": val / s._total, "cuts": len(cuts), "peak": peak,
            "workers": n_workers, "par_secs": par_secs}


def _main(argv):
    pos = [a for a in argv if not a.startswith("--")]
    L, CAP, D = int(pos[0]), int(pos[1]), int(pos[2])
    shared_cap = None
    if "--shared" in argv:
        shared_cap = int(argv[argv.index("--shared") + 1])
    n_workers = None
    if "--parallel" in argv:
        n_workers = int(argv[argv.index("--parallel") + 1])
    weighted = None
    freq = None
    if "--weighted" in argv:
        import freq_search
        weighted = argv[argv.index("--weighted") + 1]
        csv = freq_search._default_log_path(weighted, L)
        freq = freq_search.FrequencySearch.reconstruct(L, csv, objective=weighted).freq
    # startup line, matching optimal.py
    g = GreedyGame(L) if freq is None else None
    if g is not None:
        print(f"length {L}: {g.N:,} words  (greedy avg {g.average_misses():.4f}, "
              f"greedy max misses {int(g.per_word_misses(None).max())})", flush=True)

    if n_workers:                            # ---- parallel path ----
        print(f"cut@depth {D}, PARALLEL on {n_workers} cores, "
              f"subproblem_ub_depth={SUBPROBLEM_UB_DEPTH}", flush=True)
        r = parallel_run(L, CAP, D, n_workers, freq, weighted)
        print(f"cap {CAP:2d}: cut-optimal avg = {r['avg']:.4f}  |  {r['cuts']:,} "
              f"subproblems, {r['peak']:,} peak states/core, parallel {r['par_secs']:.1f}s",
              flush=True)
        return

    tag = f"shared {shared_cap:,}" if shared_cap else "scoped subproblems"
    print(f"cut@depth {D} ({tag}), subproblem_ub_depth={SUBPROBLEM_UB_DEPTH}", flush=True)

    r = run(L, CAP, D, shared_cap, freq)

    # completion line, matching optimal.py's "cap NN: capped optimal avg = ..." shape
    print(f"cap {CAP:2d}: cut-optimal avg = {r['avg']:.4f}  |  {r['calls']:,} calls, "
          f"{r['subs']:,} subproblems, {r['peak_sub']:,} peak states, {r['secs']:.1f}s",
          flush=True)
    # extra detail
    print(f"  cut-hits (subtrees skipped): {r['hits']:,}  |  top-memo {r['top']:,}  |  "
          f"pinned cut values {r['cut']:,}"
          + (f"  |  shared evictions {r['shared_evict']:,}" if shared_cap else ""), flush=True)


if __name__ == "__main__":
    _main(sys.argv[1:])

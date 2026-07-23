"""Max win-probability hangman under a HARD miss budget n, with a
lowest-expected-guesses tie-break.

Different objective from optimal.py:
  optimal.py     minimizes frequency-weighted AVERAGE misses (over ALL words).
  winprob.py     for a fixed budget n, MAXIMIZES the frequency-weighted
                 probability of finishing the word within n misses, and among
                 all strategies that tie on that, MINIMIZES the expected number
                 of misses over the games you WIN.

Model.  A strategy is a decision tree.  Each internal node guesses one letter;
words split by the letter's position-pattern (masks[i, c]), and the "letter
absent" branch (pattern 0) costs a miss (r -> r-1).  A word is WON at budget n
iff its path uses <= n misses before the set narrows to one candidate.

SINGLE pass over (surviving set S, misses remaining r), computing both objectives
at once as a lexicographic pair via `_solve`:
  lost = min mass that CANNOT be won within r misses (= max win probability), and
  miss = min total misses over the WON words among that min-lost play.
We minimize the DUAL `lost` (a min-of-sum, small when P(win) is high) so
lexicographic alpha-beta can prune whole letters -- maximizing `won` directly is
flat near the top and won't prune.  A miss is charged only on the letter-absent
branch (+1 per won word there).  `won(S,r)` and `mmin(S,r)` are thin readers of
`_solve`.

Exact.  usage:  python math/winprob.py LENGTH N
"""
import hashlib
import json
import os
import pickle
import time
from pathlib import Path

import numpy as np
from optimal import OptimalSolver, ALPHABET, INF

MEMO_FORMAT = 3                        # bump if the solver's stored values change meaning


class WinProbSolver:
    def __init__(self, length, freq=None, weighting=None):
        s = OptimalSolver(length=length)
        s.freq = s.game._coerce_freq(freq)
        self.s = s
        self.game = s.game
        self.f = s.freq
        self.masks = s.masks
        self.words = s.game.words
        self.length = length
        self.weighting = weighting or ("uniform" if freq is None else "custom")
        self.N = s.N
        self._idt = s._idt
        self.total = float(self.f.sum())
        # tolerance for "equal" masses/miss-sums.  Integer-valued weights (uniform,
        # or zipf via round(10**zipf)) give exact sums, so cap eps below 1 so large
        # weighted totals don't wash out genuine (>= 1) differences.
        self.eps = min(1e-9 * max(self.total, 1.0), 0.1)
        self.memo = {}                 # exact (lost, miss) pair per (S, r)
        self.lb = {}                   # lexicographic lower bounds from alpha-beta pruning
        self.move = {}                 # chosen letter index per exact (S, r)
        # progress / heartbeat state (optimal.py-style)
        self._verbose = True
        self._heartbeat = 60.0
        self._calls = 0
        self._t0 = 0.0
        self._last_beat = 0.0
        self._n = 0                    # budget currently being solved
        self._phase = ""               # "won" | "gmin"
        self._op = ("", 0, 0)          # root opener: letter, index, total
        self._best_p = 0.0             # best P(win<=n) so far this budget
        self._ckpt_path = None         # if set, _beat periodically saves the memo here
        self._ckpt_interval = 3600.0
        self._last_ckpt = 0.0

    def _signature(self):
        """Identifies which run a memo file belongs to (length + weighting +
        exact freq + solver format).  Guards against reusing a stale/incompatible
        checkpoint."""
        h = hashlib.sha256()
        h.update(f"winprob-v{MEMO_FORMAT}-len{self.length}-{self.weighting}".encode())
        h.update(np.ascontiguousarray(self.f, dtype=np.float64).tobytes())
        return h.hexdigest()

    def save_memo(self, path):
        """Persist the exact (lost, miss) memo + chosen moves so a later, deeper run
        can resume.  Only exact values are stored -- lower bounds are cheap to
        re-derive and would bloat the file.  Atomic (tmp + replace)."""
        data = {"sig": self._signature(), "memo": self.memo, "move": self.move}
        tmp = str(path) + ".tmp"
        with open(tmp, "wb") as fh:
            pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
        self._last_ckpt = time.perf_counter()

    def load_memo(self, path):
        """Restore the exact memo + moves from a previous run if present and
        compatible.  Returns the number of states loaded, or 0."""
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "rb") as fh:
                data = pickle.load(fh)
        except Exception:
            return 0
        if data.get("sig") != self._signature() or "memo" not in data:
            return 0
        self.memo = data["memo"]
        self.move = data.get("move", {})
        return len(self.memo)

    def _beat(self, force=False):
        """Periodic status line, in line with optimal.py's heartbeat."""
        self._calls += 1
        if not self._verbose:
            return
        if not force and (self._calls & 0x3FFF):
            return
        now = time.perf_counter()
        if not force and now - self._last_beat < self._heartbeat:
            return
        self._last_beat = now
        op, oi, ot = self._op
        frac = f"opener '{op}' {oi}/{ot} | " if ot else ""
        nst = len(self.memo) + len(self.lb)
        print(f"    [n={self._n} {self._phase}] {frac}{nst:,} states | "
              f"P<={self._n} so far {self._best_p:.4f} | {now - self._t0:.0f}s",
              flush=True)
        if self._ckpt_path and now - self._last_ckpt >= self._ckpt_interval:
            self.save_memo(self._ckpt_path)          # periodic mid-n checkpoint
            print(f"    checkpointed memo -> {self._ckpt_path}", flush=True)

    @staticmethod
    def _lex_less(a, b, eps):
        """(a_lost, a_miss) < (b_lost, b_miss) lexicographically, within tolerance."""
        if a[0] < b[0] - eps:
            return True
        if a[0] > b[0] + eps:
            return False
        return a[1] < b[1] - eps

    def _solve(self, S, r, bl, bm):
        """Single pass computing BOTH objectives at once as a lexicographic pair
        (lost, miss):
            primary   lost = min mass that CANNOT be won within r misses (= max win)
            secondary miss = min total misses over the WON words, among min-lost play
        Recurrence (a miss is charged only on the letter-absent branch):
            lost = min_c [ sum_present lost(p, r) + lost(absent, r-1) ]
            miss = matching sum_present miss(p, r) + miss(absent, r-1) + won(absent, r-1)
        `(bl, bm)` is a lexicographic upper bound -- alpha-beta.  We thread the
        remaining allowance into children, so a branch whose (lost, miss) already
        can't beat the incumbent aborts.  Returns the exact pair if it is < (bl, bm)
        lexicographically, else a valid LOWER bound >= (bl, bm).  Exact -> self.memo,
        lower bounds -> self.lb, the chosen move -> self.move.  Minimizing the dual
        `lost` (small when P(win) is high) is what lets alpha-beta cut whole letters
        where maximizing `won` directly would be flat and unprunable."""
        n = S.shape[0]
        fS = self.f[S]
        if r < 0:                          # budget blown -> everything lost, nothing won
            return float(fS.sum()), 0.0
        if n <= 1:                          # lone/empty word: won, no misses
            return 0.0, 0.0
        if r > n - 1:                       # extra misses never bind: collapse state
            r = n - 1
        eps = self.eps
        key = (S.tobytes(), r)
        ex = self.memo.get(key)
        if ex is not None:
            return ex
        lbv = self.lb.get(key)
        if lbv is not None and not self._lex_less(lbv, (bl, bm), eps):
            return lbv                      # already known >= (bl, bm) -> prune
        self._beat()
        MS = self.masks[S]
        splits = MS.min(0) != MS.max(0)
        order = np.argsort(fS @ (MS > 0).astype(np.float64))[::-1]
        is_root = n == self.N
        best_l, best_m, best_c = bl, bm, -1
        for oi in range(order.shape[0]):
            c = int(order[oi])
            if not splits[c]:
                continue
            if is_root:
                self._op = (ALPHABET[c], oi + 1, order.shape[0])
            pats = MS[:, c]
            acc_l = acc_m = 0.0
            pruned = False
            for pv in np.unique(pats):      # 0 (absent) sorts first
                grp = S[pats == pv]
                if pv == 0:                 # absent branch: its won words each take a miss
                    cl, cm = self._solve(grp, r - 1, best_l - acc_l, INF)
                    acc_l += cl
                    acc_m += cm + (float(self.f[grp].sum()) - cl)   # + won(absent) misses
                else:                       # present branch: no miss
                    cl, cm = self._solve(grp, r, best_l - acc_l, best_m - acc_m)
                    acc_l += cl
                    acc_m += cm
                if not self._lex_less((acc_l, acc_m), (best_l, best_m), eps):
                    pruned = True           # this letter can't beat the incumbent
                    break
            if not pruned and self._lex_less((acc_l, acc_m), (best_l, best_m), eps):
                best_l, best_m, best_c = acc_l, acc_m, c
                if is_root:
                    self._best_p = (self.total - best_l) / self.total
                if best_l <= eps and best_m <= eps:
                    break
        if self._lex_less((best_l, best_m), (bl, bm), eps):
            self.memo[key] = (best_l, best_m)       # exact
            self.move[key] = best_c
        elif lbv is None or self._lex_less(lbv, (bl, bm), eps):
            self.lb[key] = (bl, bm)                 # true value >= (bl, bm)
        return best_l, best_m

    def won(self, S, r):
        """Max frequency mass of S winnable with <= r misses."""
        n = S.shape[0]
        if n == 0:
            return 0.0
        mass = float(self.f[S].sum())
        if n == 1:
            return mass
        lost, _ = self._solve(S, r, mass + 1.0, INF)
        return mass - lost

    def mmin(self, S, r):
        """Min misses over the won words among max-win strategies (the tie-break)."""
        n = S.shape[0]
        if n <= 1:
            return 0.0
        mass = float(self.f[S].sum())
        _, miss = self._solve(S, r, mass + 1.0, INF)
        return miss

    def _choose(self, S, r):
        """The letter the optimal strategy plays at (S, r) -- recorded by _solve
        (max win, then min misses, ties by promise order).  Returns index or -1."""
        n = S.shape[0]
        if n <= 1:
            return -1
        mass = float(self.f[S].sum())
        rk = r if r <= n - 1 else n - 1
        self._solve(S, r, mass + 1.0, INF)          # ensure exact + move recorded
        return self.move.get((S.tobytes(), rk), -1)

    def best_opener(self, r):
        """Best first guess at budget r: (letter, won_mass, miss_sum). One pass."""
        root = np.arange(self.N, dtype=self._idt)
        self._n = r
        self._op = ("", 0, 0)
        self._best_p = 0.0
        self._phase = "solve"
        total = self.total
        lost, miss = self._solve(root, r, total + 1.0, INF)
        self._best_p = (total - lost) / total if total else 0.0
        c = self.move.get((root.tobytes(), r), -1)
        return (ALPHABET[c] if c >= 0 else "-"), total - lost, miss

    def _pattern_str(self, c, mask):
        """Letter c, its position bitmask -> revealed template, e.g. 'e_e_';
        mask 0 (absent) -> all underscores."""
        return "".join(ALPHABET[c] if (mask >> p) & 1 else "_"
                       for p in range(self.length))

    def build_tree(self, S, r, n0):
        """Nested optimal decision tree for (S, r).  n0 is the game's total
        budget, so a leaf records misses spent = n0 - r.
          internal: {"guess", "n", "branches": {template: subtree}}
          won leaf: {"word", "misses"}
          lost group (can't be won within budget): {"lost": [words]}"""
        k = S.shape[0]
        if k == 1:
            return {"word": self.words[int(S[0])], "misses": int(n0 - r)}
        if k == 0:
            return {}
        W = self.won(S, r)
        if W <= self.eps:                   # nothing here is winnable -> all lost
            return {"lost": [self.words[int(i)] for i in S]}
        c = self._choose(S, r)
        pats = self.masks[S, c]
        branches = {}
        for pv in np.unique(pats):
            grp = S[pats == pv]
            template = self._pattern_str(c, int(pv))
            if pv == 0 and r == 0:          # absent branch, no misses left -> lost
                branches[template] = {"lost": [self.words[int(i)] for i in grp]}
            else:
                branches[template] = self.build_tree(grp, r - 1 if pv == 0 else r, n0)
        return {"guess": ALPHABET[c], "n": int(k), "branches": branches}

    def save_tree(self, n, path, *, p_win=None, e_misses=None, opener=None):
        """Write the optimal tree for budget n to a self-describing JSON file."""
        root = np.arange(self.N, dtype=self._idt)
        payload = {
            "length": self.length,
            "n": n,
            "words": self.N,
            "weighting": self.weighting,
            "p_win": p_win,
            "e_misses": e_misses,
            "opener": opener,
            "tree": self.build_tree(root, n, n),
        }
        Path(path).write_text(json.dumps(payload))


def _main():
    import sys
    weighting, fresh, pos = "uniform", False, []
    it = iter(sys.argv[1:])
    for a in it:
        if a == "--fresh":                           # ignore any saved memo, start cold
            fresh = True
        elif a == "--weighted":                      # "zipf" = real word frequency
            weighting = next(it, "zipf")
        elif a.startswith("--weighted="):
            weighting = a.split("=", 1)[1]
        elif not a.startswith("--"):
            pos.append(a)
    L = int(pos[0])
    N = int(pos[1]) if len(pos) > 1 else 8
    hb = float(pos[2]) if len(pos) > 2 else 60.0     # heartbeat seconds
    import wordlist
    wp = WinProbSolver(L, freq=wordlist.resolve_weighting(weighting, L),
                       weighting=weighting)   # raises on unknown/not-yet-run weightings
    wp._heartbeat = hb
    wp._t0 = wp._last_beat = wp._last_ckpt = time.perf_counter()

    base = Path(__file__).resolve().parent / "data"
    shared_dir = base / "shared" / "winprob"         # committed: final trees
    local_dir = base / "local" / "winprob"           # gitignored: resume checkpoints
    shared_dir.mkdir(parents=True, exist_ok=True)
    local_dir.mkdir(parents=True, exist_ok=True)
    memo_path = local_dir / f"len{L:02d}_{wp.weighting}.memo.pkl"
    wp._ckpt_path = memo_path                        # enables hourly mid-n checkpoints

    print(f"len{L}: {wp.N:,} words   (maximize P(win within n misses), "
          f"tie-break min E[misses | won])")
    if fresh and memo_path.exists():
        memo_path.unlink()
        print(f"--fresh: cleared {memo_path.name}")
    elif not fresh:
        loaded = wp.load_memo(memo_path)
        if loaded:
            print(f"resumed from {memo_path.name}: {loaded:,} states reused")

    header = f"{'n':>3}  {'P(win<=n)':>10}  {'E[miss|won]':>13}  {'opener':>6}"
    print(header)
    rows = []                     # (n, p, em, letter) -- collected for the final report
    for n in range(N + 1):
        tn = time.perf_counter()
        letter, w, m = wp.best_opener(n)
        p = w / wp.total if wp.total else 0.0
        em = m / w if w > wp.eps else 0.0
        rows.append((n, p, em, letter))
        print(f"{n:>3}  {p:>10.4f}  {em:>13.3f}  {letter:>6}   "
              f"[{len(wp.memo) + len(wp.lb):,} states, +{time.perf_counter() - tn:.1f}s]", flush=True)
        # Save the tree FIRST (the deliverable) so it survives even if the
        # checkpoint below is killed.  Then free the (unsaved) lower-bound cache so
        # the memo pickle can reuse that memory instead of allocating more -- a huge
        # memo can otherwise OOM at the RAM ceiling right when writing the result.
        wp.save_tree(n, shared_dir / f"len{L:02d}_{wp.weighting}_n{n:02d}.json",
                     p_win=p, e_misses=em, opener=letter)
        wp.lb.clear()
        wp.save_memo(memo_path)
        print(f"     saved tree + checkpoint (n={n})", flush=True)
        if p >= 1.0 - 1e-9:
            print(f"     (all words winnable at n={n}; higher n is identical)")
            break

    # consolidated report (same table, clean, at the end)
    print(f"\n===== len{L}: win-probability report "
          f"({len(wp.memo) + len(wp.lb):,} positions, {time.perf_counter() - wp._t0:.1f}s) =====")
    print(header)
    for n, p, em, letter in rows:
        print(f"{n:>3}  {p:>10.4f}  {em:>13.3f}  {letter:>6}")


if __name__ == "__main__":
    _main()

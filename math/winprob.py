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

Two passes over (surviving set S, misses remaining r) so the win-probability
pass keeps its branch-and-bound:
  won(S, r)  = max frequency mass of S winnable with <= r misses.  A letter that
               wins ALL of S is optimal, so we stop at the first; and >= |S|-1
               misses always resolves |S| words, so those states short-circuit.
  mmin(S, r) = min miss-sum, taken ONLY over letters achieving won(S, r).  A miss
               happens only on the letter-absent branch, so it adds +1 per won
               word THERE (present branches add nothing):
                   mmin(S,r) = won(absent branch) + sum over win-optimal children of mmin(child)

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

MEMO_FORMAT = 2                        # bump if the solver's stored values change meaning


class WinProbSolver:
    def __init__(self, length, freq=None):
        s = OptimalSolver(length=length)
        s.freq = s.game._coerce_freq(freq)
        self.s = s
        self.game = s.game
        self.f = s.freq
        self.masks = s.masks
        self.words = s.game.words
        self.length = length
        self.weighting = "uniform" if freq is None else "custom"
        self.N = s.N
        self._idt = s._idt
        self.total = float(self.f.sum())
        self.eps = 1e-9 * max(self.total, 1.0)
        self.lmemo = {}                # exact lost(S, r)
        self.llb = {}                  # lower bounds on lost(S, r) from alpha-beta pruning
        self.mmemo = {}                # exact mmin(S, r)
        self.mlb = {}                  # lower bounds on mmin(S, r)
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
        """Persist the exact-value memos (lmemo, mmemo) so a later, deeper run can
        resume.  Only exact values are stored -- lower bounds (llb/mlb) are cheap
        to re-derive and would bloat the file.  Atomic (tmp + replace)."""
        data = {"sig": self._signature(), "lmemo": self.lmemo, "mmemo": self.mmemo}
        tmp = str(path) + ".tmp"
        with open(tmp, "wb") as fh:
            pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)
        self._last_ckpt = time.perf_counter()

    def load_memo(self, path):
        """Restore exact memos from a previous run if present and compatible.
        Returns the number of states loaded, or 0."""
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "rb") as fh:
                data = pickle.load(fh)
        except Exception:
            return 0
        if data.get("sig") != self._signature():
            return 0
        self.lmemo = data["lmemo"]
        self.mmemo = data["mmemo"]
        return len(self.lmemo) + len(self.mmemo)

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
        nst = len(self.lmemo) + len(self.llb) + len(self.mmemo) + len(self.mlb)
        print(f"    [n={self._n} {self._phase}] {frac}{nst:,} states | "
              f"P<={self._n} so far {self._best_p:.4f} | {now - self._t0:.0f}s",
              flush=True)
        if self._ckpt_path and now - self._last_ckpt >= self._ckpt_interval:
            self.save_memo(self._ckpt_path)          # periodic mid-n checkpoint
            print(f"    checkpointed memo -> {self._ckpt_path}", flush=True)

    def won(self, S, r):
        """Max frequency mass of S winnable with <= r misses = mass(S) - lost(S, r)."""
        n = S.shape[0]
        if n <= 1:
            return float(self.f[S].sum()) if n == 1 else 0.0
        mass = float(self.f[S].sum())
        return mass - self.lost(S, r, mass + 1.0)

    def lost(self, S, r, bound):
        """Min frequency mass of S that CANNOT be won within r misses (the dual of
        won).  This is a min-of-sum, so it prunes like optimal.py:
            lost(S,r) = min over letters of [ sum_present lost(p, r) + lost(absent, r-1) ]
        `bound` is an upper bound we care about -- alpha-beta.  We thread the
        remaining allowance into children, so a subtree whose lost already exceeds
        what's useful aborts early.  Returns the exact lost if it's < bound, else a
        valid LOWER bound (>= bound).  Exact results go in lmemo; lower bounds in llb.
        Why this beats maximizing `won` directly: near the top won ~= mass for every
        letter (flat, nothing prunes), but lost ~= 0 there, and a tiny incumbent lets
        alpha-beta cut whole letters."""
        n = S.shape[0]
        fS = self.f[S]
        if r < 0:                          # budget exceeded (absent branch at r=0)
            return float(fS.sum())         # -> everything here is lost, even a lone word
        if n <= 1:
            return 0.0
        if r >= n - 1:                     # >=|S|-1 misses always resolves S -> lost 0
            return 0.0
        key = (S.tobytes(), r)
        ex = self.lmemo.get(key)
        if ex is not None:
            return ex
        lbv = self.llb.get(key, 0.0)
        if lbv >= bound - self.eps:        # already known lost >= bound
            return lbv
        self._beat()
        eps = self.eps
        MS = self.masks[S]
        splits = MS.min(0) != MS.max(0)
        order = np.argsort(fS @ (MS > 0).astype(np.float64))[::-1]
        is_root = n == self.N
        best = bound
        for oi in range(order.shape[0]):
            c = int(order[oi])
            if not splits[c]:
                continue
            if is_root:
                self._op = (ALPHABET[c], oi + 1, order.shape[0])
            pats = MS[:, c]
            cost = 0.0
            pruned = False
            for pv in np.unique(pats):     # 0 (absent) sorts first -> prune fast
                grp = S[pats == pv]
                if pv == 0:
                    child = self.lost(grp, r - 1, best - cost)   # r-1<0 handled -> mass(grp)
                else:
                    child = self.lost(grp, r, best - cost)
                cost += child
                if cost >= best - eps:     # this letter can't beat the incumbent
                    pruned = True
                    break
            if not pruned and cost < best - eps:
                best = cost
                if is_root:
                    self._best_p = (self.total - best) / self.total
                if best <= eps:
                    break
        if best < bound - eps:
            self.lmemo[key] = best         # exact (fully-evaluated winning letter)
        elif bound > lbv:
            self.llb[key] = bound          # lost >= bound
        return best

    def mmin(self, S, r, mbound=INF):
        """Min miss-sum over won words, among strategies achieving won(S, r).
        A miss is charged only on the letter-absent branch (+1 per won word there).
        Alpha-beta on the miss-sum (same trick as `lost`, but on misses): thread the
        remaining allowance `mbound` into children so the min-miss resolution of the
        fully-winnable regions prunes instead of exploring every won-tied letter --
        which is what blew up before."""
        n = S.shape[0]
        if n <= 1:
            return 0.0
        if r > n - 1:                      # extra misses never bind: collapse state
            r = n - 1
        key = (S.tobytes(), r)
        ex = self.mmemo.get(key)
        if ex is not None:
            return ex
        mlbv = self.mlb.get(key, 0.0)
        if mlbv >= mbound - self.eps:      # already known miss >= mbound
            return mlbv
        self._beat()
        eps = self.eps
        W = self.won(S, r)
        if W <= eps:                       # nothing winnable -> no won words, 0 misses
            self.mmemo[key] = 0.0
            return 0.0
        MS = self.masks[S]
        fS = self.f[S]
        splits = MS.min(0) != MS.max(0)
        order = np.argsort(fS @ (MS > 0).astype(np.float64))[::-1]
        is_root = n == self.N
        best = mbound
        for oi in range(order.shape[0]):
            c = int(order[oi])
            if not splits[c]:
                continue
            if is_root:                    # show opener progress during the tie-break too
                self._op = (ALPHABET[c], oi + 1, order.shape[0])
            pats = MS[:, c]
            branch_w = 0.0
            absent_won = 0.0
            live = []
            for pv in np.unique(pats):
                grp = S[pats == pv]
                if pv == 0:
                    if r == 0:
                        continue           # absent words lost (0 won)
                    rr = r - 1
                    wa = self.won(grp, rr)
                    absent_won += wa       # each won word here takes a miss
                    branch_w += wa
                else:
                    rr = r
                    branch_w += self.won(grp, rr)
                live.append((grp, rr))
            if abs(branch_w - W) > eps:
                continue                   # not win-optimal -> skip
            miss = absent_won              # +1 miss per won word on the absent branch
            pruned = False
            for grp, rr in live:
                if miss >= best - eps:
                    pruned = True
                    break
                miss += self.mmin(grp, rr, best - miss)
            if not pruned and miss < best - eps:
                best = miss
                if best <= eps:
                    break
        if best < mbound - eps:
            self.mmemo[key] = best         # exact
        elif mbound > mlbv:
            self.mlb[key] = mbound         # miss >= mbound
        return best

    def _choose(self, S, r):
        """Chosen guess for the optimal strategy at (S, r): the letter achieving
        the max win-mass won(S, r), breaking ties by min expected misses over the
        won words, and remaining ties by lowest letter index (deterministic).
        Returns (letter_index, won_mass, miss_sum); letter_index = -1 if trivial."""
        n = S.shape[0]
        if n <= 1:
            return -1, (float(self.f[S].sum()) if n == 1 else 0.0), 0.0
        W = self.won(S, r)
        MS = self.masks[S]
        fS = self.f[S]
        splits = MS.min(0) != MS.max(0)
        eps = self.eps
        best_c, best_m = -1, INF
        for c in range(MS.shape[1]):        # lowest index first -> deterministic ties
            if not splits[c]:
                continue
            pats = MS[:, c]
            branch_w = 0.0
            absent_won = 0.0
            live = []
            for pv in np.unique(pats):
                grp = S[pats == pv]
                if pv == 0:
                    if r == 0:
                        continue            # absent words lost, 0 won
                    rr = r - 1
                    wa = self.won(grp, rr)
                    absent_won += wa
                    branch_w += wa
                else:
                    rr = r
                    branch_w += self.won(grp, rr)
                live.append((grp, rr))
            if abs(branch_w - W) > eps:
                continue                    # not win-optimal
            m = absent_won + sum(self.mmin(grp, rr) for grp, rr in live)
            if m < best_m - eps:
                best_m, best_c = m, c
        return best_c, W, (best_m if best_c >= 0 else 0.0)

    def best_opener(self, r):
        """Best first guess at budget r: (letter, won_mass, guess_sum)."""
        root = np.arange(self.N, dtype=self._idt)
        self._n = r
        self._op = ("", 0, 0)
        self._best_p = 0.0
        self._phase = "won"
        W = self.won(root, r)
        self._best_p = W / self.total if self.total else 0.0
        self._phase = "gmin"
        self._op = ("", 0, 0)
        c, W, g = self._choose(root, r)
        return (ALPHABET[c] if c >= 0 else "-"), W, g

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
        c, _, _ = self._choose(S, r)
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
    pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    L = int(pos[0])
    N = int(pos[1]) if len(pos) > 1 else 8
    hb = float(pos[2]) if len(pos) > 2 else 60.0     # heartbeat seconds
    fresh = "--fresh" in flags                       # ignore any saved memo, start cold
    wp = WinProbSolver(L)
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
              f"[{len(wp.lmemo) + len(wp.llb):,} states, +{time.perf_counter() - tn:.1f}s]", flush=True)
        # save the optimal tree AND the memo for this n, so a deeper rerun resumes here
        wp.save_tree(n, shared_dir / f"len{L:02d}_{wp.weighting}_n{n:02d}.json",
                     p_win=p, e_misses=em, opener=letter)
        wp.save_memo(memo_path)
        print(f"     saved tree + checkpoint (n={n})", flush=True)
        if p >= 1.0 - 1e-9:
            print(f"     (all words winnable at n={n}; higher n is identical)")
            break

    # consolidated report (same table, clean, at the end)
    print(f"\n===== len{L}: win-probability report "
          f"({len(wp.lmemo) + len(wp.llb):,} positions, {time.perf_counter() - wp._t0:.1f}s) =====")
    print(header)
    for n, p, em, letter in rows:
        print(f"{n:>3}  {p:>10.4f}  {em:>13.3f}  {letter:>6}")


if __name__ == "__main__":
    _main()

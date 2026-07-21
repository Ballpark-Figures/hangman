"""Independent validator for winprob.py.

Re-solves the SAME objective a totally different way: on raw word strings,
signatures = tuples of letter positions, one-pass lexicographic (max won-mass,
then min guess-sum) with NO pruning / NO clamp / NO two-phase.  If this agrees
with WinProbSolver over many random (subset, budget) cases, both the mask
encoding and the DP recurrence are confirmed.

usage:  python math/winprob_check.py [LENGTH ...]
"""
import sys
from functools import lru_cache
import numpy as np

sys.path.insert(0, "math")
from winprob import WinProbSolver


def brute(words, freq, r):
    """Independent (won_mass, guess_sum) on raw strings. words: tuple[str]."""
    @lru_cache(maxsize=None)
    def rec(ws, rr):
        n = len(ws)
        if n <= 1:
            return (freq[ws[0]] if n == 1 else 0.0), 0.0
        best_w, best_m = -1.0, 0.0
        letters = set().union(*(set(w) for w in ws))
        for x in letters:
            groups = {}
            for w in ws:
                sig = tuple(i for i, ch in enumerate(w) if ch == x)  # () = absent
                groups.setdefault(sig, []).append(w)
            if len(groups) <= 1:
                continue                               # x doesn't split
            cw = cm = 0.0
            for sig, g in groups.items():
                if sig == ():                          # absent -> miss
                    if rr == 0:
                        continue                       # lost
                    sw, sm = rec(tuple(g), rr - 1)
                    cw += sw
                    cm += sm + sw                      # +1 miss per won word on absent branch
                else:
                    sw, sm = rec(tuple(g), rr)
                    cw += sw
                    cm += sm                           # present branch: no miss
            if cw > best_w + 1e-12 or (abs(cw - best_w) <= 1e-12 and cm < best_m - 1e-12):
                best_w, best_m = cw, cm
        if best_w < 0.0:
            best_w, best_m = 0.0, 0.0
        return best_w, best_m

    return rec(tuple(words), r)


def check_length(L, trials=200, seed=0):
    wp = WinProbSolver(L)
    wp._verbose = False                    # no heartbeats during validation
    words = wp.game.words
    fr = {w: float(wp.f[i]) for i, w in enumerate(words)}
    rng = np.random.default_rng(seed + L)
    worst_w = worst_m = 0.0
    fails = 0
    for _ in range(trials):
        k = int(rng.integers(3, min(14, wp.N) + 1))
        idx = np.sort(rng.choice(wp.N, size=k, replace=False)).astype(wp._idt)
        r = int(rng.integers(0, 6))
        sub = [words[i] for i in idx]
        bw, bm = brute(sub, fr, r)
        w = wp.won(idx, r)
        m = wp.mmin(idx, r)
        dw, dm = abs(w - bw), abs(m - bm)
        worst_w, worst_m = max(worst_w, dw), max(worst_m, dm)
        if dw > 1e-6 or dm > 1e-6:
            fails += 1
            if fails <= 5:
                print(f"  MISMATCH len{L} r={r} k={k}: won {w:.6f} vs {bw:.6f} "
                      f"(d={dw:.2e}), mmin {m:.6f} vs {bm:.6f} (d={dm:.2e})")
                print(f"    words={sub}")
    status = "OK" if fails == 0 else f"{fails} FAILS"
    print(f"len{L}: {trials} random (subset,budget) cases  ->  {status}  "
          f"(max |dwon|={worst_w:.2e}, max |dmmin|={worst_m:.2e})")
    return fails == 0


if __name__ == "__main__":
    lengths = [int(a) for a in sys.argv[1:]] or [4, 5, 6, 7]
    ok = all(check_length(L) for L in lengths)
    print("\nALL PASS" if ok else "\nFAILURES PRESENT")
    sys.exit(0 if ok else 1)

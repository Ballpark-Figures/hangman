"""Audit: do the committed OPTIMAL trees actually realize the DP's reported
optimum? Replays every word through each converged uniform tree and compares the
realized mean misses to the CSV's converged `capped_avg`. A positive gap means
the serialized tree policy is slightly SUBOPTIMAL vs the value the solver reports.

    python math/optimal_tree_audit.py            # cross-length replay-vs-CSV table
    python math/optimal_tree_audit.py --fresh 10 # fresh in-process solve for L=10:
                                                 #   DP reported vs fresh tree replay
                                                 #   (isolates a live reconstruction
                                                 #    gap from stale committed data)

Companion to optimal_discrepancy_report.md. Read-only except --fresh (which
re-solves in memory only; writes nothing).
"""
import glob
import json
import re
import sys

sys.path.insert(0, "math")
from strategy import GreedyGame
from strategy_view import _optimal_cap_file


def _template(word, letter):
    return "".join(letter if ch == letter else "_" for ch in word)


def replay_mean(tree, words):
    """Mean misses realized by PLAYING the tree against every word (to the leaf,
    i.e. to determination; completion tails add no misses)."""
    tot = 0
    for w in words:
        node, m = tree, 0
        while "branches" in node:
            g = node["guess"]
            if g not in w:
                m += 1
            node = node["branches"][_template(w, g)]
        tot += m
    return tot / len(words)


def csv_converged_avg(weighting, L):
    """The converged-row `capped_avg` from the solver's CSV, or None."""
    path = f"math/data/shared/optimal/len{L:02d}_{weighting}.csv"
    try:
        rows = open(path).read().splitlines()[1:]
    except FileNotFoundError:
        return None
    for line in rows:
        f = line.split(",")
        if len(f) >= 7 and f[6].strip() == "1":
            return float(f[1])
    return None


def table(weighting="uniform", lengths=range(1, 21)):
    print(f"weighting={weighting}")
    print(f"{'L':>2} {'tree_replay':>12} {'csv_optimum':>12} {'gap':>10}")
    for L in lengths:
        found = _optimal_cap_file(weighting, L)
        if not found:
            continue
        path, cap, conv = found
        if not conv:
            continue
        words = GreedyGame(L).words
        tr = replay_mean(json.loads(open(path).read()), words)
        csv = csv_converged_avg(weighting, L)
        if csv is None:
            continue
        gap = tr - csv
        flag = "  <-- tree suboptimal" if gap > 1e-6 else ""
        print(f"{L:>2} {tr:>12.6f} {csv:>12.6f} {gap:>10.6f}{flag}")


def fresh(L, weighting="uniform"):
    from optimal import OptimalSolver
    g = GreedyGame(L)
    s = OptimalSolver(g)
    ret = s.deepen(verbose=False)
    reported = ret[0] if isinstance(ret, tuple) else ret
    tree = s.optimal_tree()
    print(f"L={L} words={g.N}")
    print(f"  DP reported (deepen)  = {float(reported):.6f}")
    print(f"  fresh tree replay     = {replay_mean(tree, g.words):.6f}")
    committed = _optimal_cap_file(weighting, L)
    if committed:
        ct = replay_mean(json.loads(open(committed[0]).read()), g.words)
        print(f"  committed tree replay = {ct:.6f}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--fresh":
        fresh(int(args[1]))
    else:
        table()

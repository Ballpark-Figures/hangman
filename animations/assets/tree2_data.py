"""Cached optimal-search data for scene 05 (the length-2 optimal tree).

Scene 05 teaches HOW the exact solver works, walking the search on the smallest
non-trivial game: the 49 length-2 words. The committed optimal tree
(`math/data/shared/optimal/len02_uniform_cap08.json`) records only the WINNING
guess per node, but the animation needs, at EVERY node, every candidate letter's
partition + the average misses of playing it then continuing optimally + the
resulting subtree. This module sources all of that from the exact solver
(`optimal.OptimalSolver.annotated_tree`, which surfaces intermediate `V(S)` values
the search already computed -- no new math) and persists it to the committed
`tree2_cache.json`. House pattern (see `greedy_data.py`): the solver is imported
only in `build()`, the scene reads only the cache via `get()`, the render never
touches `math/`.

The node `avg` is the LOCAL subtree average -- mean additional misses over just the
words that reach that node (0 for a branch that resolves with no further miss); the
root is 3.877551, which for length 2 equals the greedy average (optimal does not
beat greedy at length 2 -- length 2 is the illustrative case, not an improvement).

Regenerate with `build()` (or `python3 tree2_data.py`) whenever the wordlist or the
solver changes. Sourced numbers only -- nothing is invented here.
"""
from pathlib import Path
import json
import sys

_MATH = Path(__file__).resolve().parents[2] / "math"
CACHE = Path(__file__).resolve().parent / "tree2_cache.json"

LENGTH = 2
WEIGHTING = "uniform"


def _imports():
    if str(_MATH) not in sys.path:
        sys.path.insert(0, str(_MATH))
    import strategy
    import wordlist
    import optimal
    return strategy, wordlist, optimal


def _max_miss_depth(tree, misses=0):
    """Deepest miss-count reached in the optimal tree (a '____' branch = +1 miss)."""
    if "branches" not in tree:
        return misses
    guess = tree.get("guess", "")
    return max(
        _max_miss_depth(sub, misses + (1 if pat == "_" * len(pat) and guess not in pat
                                       else 0))
        for pat, sub in tree["branches"].items())


def build():
    strategy, wordlist, optimal = _imports()

    game = strategy.GreedyGame(LENGTH)
    freq = wordlist.resolve_weighting(WEIGHTING, LENGTH)   # "uniform" -> None
    greedy_avg = float(game.average_misses(freq))

    solver = optimal.OptimalSolver(game)
    opt_avg = solver.solve(freq, max_misses=None, verbose=False)   # UNCAPPED
    tree = solver.annotated_tree()

    data = {
        "meta": {
            "length": LENGTH,
            "weighting": WEIGHTING,
            "min_zipf": wordlist.DEFAULT_ZIPF,
            "n_words": int(game.N),
            "optimal_avg": opt_avg,
            "greedy_avg": greedy_avg,
            "optimal_first_letter": tree["optimal_letter"],
            "max_miss_depth": _max_miss_depth(tree["options"][0]["subtree"])
            if tree.get("options") else 0,
        },
        "tree": tree,
    }
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def _load():
    return json.loads(CACHE.read_text())


# ── render-side accessors (read the committed cache; no computation) ───────────
def get():
    """The whole cache dict (read straight from the committed JSON)."""
    return _load()


# ── provenance / verification ─────────────────────────────────────────────────
def _node_at(tree, path):
    """Walk `children` by a list of branch-pattern keys."""
    node = tree
    for pat in path:
        node = node["children"][pat]
    return node


if __name__ == "__main__":
    data = build()
    m = data["meta"]
    tree = data["tree"]
    size_kb = CACHE.stat().st_size / 1024
    print(f"wrote {CACHE.name}: length-{m['length']} {m['weighting']} game, "
          f"{m['n_words']} words, max miss depth {m['max_miss_depth']}  "
          f"({size_kb:.0f} KB)\n")

    # headline: optimal == greedy for length 2 (the illustrative, no-improvement case)
    print(f"[root] optimal first letter {m['optimal_first_letter']!r}, "
          f"avg misses {tree['avg']:.6f}   <- OptimalSolver.annotated_tree (uncapped)")
    print(f"[root] optimal_avg {m['optimal_avg']:.6f}  vs  greedy_avg "
          f"{m['greedy_avg']:.6f}")

    # GATE: exporter must agree with the committed solver output (CSV converged value)
    CSV_CONVERGED = 3.877551
    for name, val in (("optimal_avg", m["optimal_avg"]),
                      ("greedy_avg", m["greedy_avg"]),
                      ("root tree avg", tree["avg"])):
        ok = abs(val - CSV_CONVERGED) < 1e-6
        print(f"    gate {name:14s} = {val:.6f}  {'OK' if ok else 'MISMATCH!!'} "
              f"(vs len02_uniform.csv converged {CSV_CONVERGED})")
        assert ok, f"{name} {val} != {CSV_CONVERGED}"

    # root first-letter options, sorted by avg (feeds the "Avg misses: _ per letter" beat)
    print("\n[root options] avg misses if we open with each letter (best first):")
    for o in tree["options"][:6]:
        star = "  <- optimal" if o["letter"] == m["optimal_first_letter"] else ""
        print(f"    {o['letter']}: {o['avg']:.4f}  "
              f"({o['n_branches']} branch{'es' if o['n_branches'] != 1 else ''}){star}")
    print(f"    ... {len(tree['options'])} letters total")

    # transposition/dedup beat: a(miss)->o(miss) is the SAME position as o(miss)->a(miss)
    empty = "_" * LENGTH
    ao = _node_at(tree, [empty, empty])          # optimal path a-absent then o-absent
    print(f"\n[dedup] after a-miss then o-miss: {ao['n']} words, "
          f"avg {ao['avg']:.4f}, next guess {ao.get('optimal_letter')!r}  "
          f"(same position however you order a & o)")

    # pruning beat: at least one single-branch 'impossible letter' option must exist
    def _has_single_branch(node):
        if "options" in node and any(not o["splits"] for o in node["options"]):
            return True
        return any(_has_single_branch(c) for c in node.get("children", {}).values())
    print(f"[prune] a single-branch 'impossible letter' option exists somewhere: "
          f"{_has_single_branch(tree)}")

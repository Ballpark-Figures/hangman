"""One-time migration: extend every committed solver tree to word COMPLETION.

The solvers (optimal.py / winprob.py) now emit completion tails at write time, but
the trees committed BEFORE that change stop at unique DETERMINATION. This rewrites
each committed JSON in place through ``tree_complete.complete_tree`` -- a purely
structural, numbers-invariant transform (the appended guesses are guaranteed hits,
so average misses / p_win / e_misses are unchanged). No re-solving.

Idempotent: re-running on already-completed trees is a no-op (byte-identical
output). Run from the repo root:

    python math/complete_committed_trees.py             # all optimal + winprob trees
    python math/complete_committed_trees.py math/data/shared/optimal/len08_uniform_cap09.json
"""
import glob
import json
import sys

sys.path.insert(0, "math")
from tree_complete import complete_tree

SHARED = "math/data/shared"


def _optimal_paths():
    return sorted(glob.glob(f"{SHARED}/optimal/len*_cap*.json"))


def _winprob_paths():
    return sorted(glob.glob(f"{SHARED}/winprob/len*_n*.json"))


def rewrite(path: str) -> bool:
    """Complete the tree in ``path`` in place. Returns True if the file changed."""
    before = open(path).read()
    data = json.loads(before)
    if "tree" in data:                    # winprob payload: {..., "tree": <tree>}
        data["tree"] = complete_tree(data["tree"])
    else:                                 # optimal: the tree is the whole document
        data = complete_tree(data)
    after = json.dumps(data)              # same formatting the solvers write with
    if after == before:
        return False
    open(path, "w").write(after)
    return True


def main(paths):
    changed = 0
    for p in paths:
        if rewrite(p):
            changed += 1
    print(f"completed {len(paths)} trees; {changed} changed, "
          f"{len(paths) - changed} already complete")


if __name__ == "__main__":
    args = sys.argv[1:]
    paths = args if args else (_optimal_paths() + _winprob_paths())
    if not paths:
        print("no trees found under math/data/shared/{optimal,winprob}/")
        sys.exit(1)
    main(paths)

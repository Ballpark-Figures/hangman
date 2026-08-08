"""Longest single-letter-insertion word chains over the master wordlist.

A *chain* is a sequence of words where each word is the previous one with
exactly ONE extra letter INSERTED (letter order otherwise preserved -- NO
rearranging). We restrict to words with all-distinct letters, so the inserted
letter is always a brand-new letter.

Four insertion modes (where the new letter may go):

    end     w -> w + c                (previous word is a prefix)
    start   w -> c + w                (previous word is a suffix)
    ends    start OR end
    any     start, middle, or end     (previous = some 1-char deletion of next)

This is a longest-path problem on a DAG: nodes are words, edges go from a word
to any longer word reachable by one legal insertion (length always +1, so the
graph is acyclic, layered by length). We DP the longest chain ENDING at each
word, then enumerate EVERY maximal chain (all ties).

Stdlib-only. Run from math/:  python3 letter_chains.py [--min-zipf 2.5]
"""

from __future__ import annotations

import argparse
from collections import defaultdict

import wordlist


def load_words(min_zipf: float, variant: str = "us") -> set[str]:
    """All words at/above the cutoff whose letters are all distinct."""
    return {
        w.text
        for w in wordlist.load(min_zipf=min_zipf, variant=variant)
        if len(set(w.text)) == len(w.text) and w.text.isalpha()
    }


def predecessors(word: str, mode: str) -> list[str]:
    """The shorter strings that could become `word` via one legal insertion."""
    if mode == "end":
        return [word[:-1]]
    if mode == "start":
        return [word[1:]]
    if mode == "ends":
        return [word[:-1], word[1:]]
    if mode == "any":
        # every single-character deletion (dedup for the layered DAG)
        return list({word[:i] + word[i + 1:] for i in range(len(word))})
    raise ValueError(f"unknown mode {mode!r}")


def longest_chains(words: set[str], mode: str) -> tuple[int, list[list[str]]]:
    """Return (max chain length, list of every chain achieving it)."""
    by_len = sorted(words, key=len)
    best: dict[str, int] = {}          # longest chain ending AT this word
    parents: dict[str, list[str]] = {} # predecessors achieving that best-1

    for w in by_len:
        b, ps = 1, []
        for p in predecessors(w, mode):
            if p in words:
                bp = best[p]  # p is shorter, so already computed
                if bp + 1 > b:
                    b, ps = bp + 1, [p]
                elif bp + 1 == b:
                    ps.append(p)
        best[w] = b
        parents[w] = ps

    if not best:
        return 0, []
    longest = max(best.values())
    ends = [w for w, b in best.items() if b == longest]

    # enumerate all longest chains by backtracking parents (all ties)
    chains: list[list[str]] = []

    def walk(w: str, tail: list[str]) -> None:
        tail = [w] + tail
        if not parents[w]:
            chains.append(tail)
            return
        for p in parents[w]:
            walk(p, tail)

    for e in ends:
        walk(e, [])
    return longest, chains


MODES = [
    ("end",   "add a letter to the END"),
    ("start", "add a letter to the START"),
    ("ends",  "add a letter to the START or END"),
    ("any",   "add a letter ANYWHERE (start/middle/end)"),
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-zipf", type=float, default=wordlist.DEFAULT_ZIPF,
                    help="frequency cutoff (default %(default)s = game cutoff)")
    ap.add_argument("--variant", default="us")
    ap.add_argument("--max-show", type=int, default=40,
                    help="cap how many tied chains to print per mode")
    args = ap.parse_args()

    words = load_words(args.min_zipf, args.variant)
    print(f"wordlist: {len(words):,} distinct-letter words at zipf >= "
          f"{args.min_zipf} (variant {args.variant!r})\n")

    for mode, desc in MODES:
        longest, chains = longest_chains(words, mode)
        # group by the sequence of lengths just for a tidy header
        print(f"### mode {mode!r}: {desc}")
        print(f"    longest chain = {longest} words; {len(chains)} such chain(s)")
        for ch in sorted(chains)[:args.max_show]:
            print("    " + " -> ".join(ch))
        if len(chains) > args.max_show:
            print(f"    ... ({len(chains) - args.max_show} more)")
        print()


if __name__ == "__main__":
    main()

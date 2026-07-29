"""Extend a solver decision tree so play continues to word COMPLETION, not just
to unique DETERMINATION.

A solver emits a determined leaf ``{"word": W, ...}`` as soon as ONE candidate
remains -- but at that moment some of W's letters may still be blank. In the game
the player keeps guessing until the WORD IS COMPLETE, and every such guess is a
guaranteed HIT (the word is already known), so it adds ZERO misses. Hence the
average-misses and win-probability numbers are UNCHANGED -- this is a purely
structural rewrite: each determined leaf becomes the chain of single-branch
"completion" nodes (one per still-unguessed letter of W, in order of first
appearance) that finishes the word.

Idempotent; adds no misses; preserves any extra leaf fields (e.g. winprob's
``"misses"``). Shared by optimal.py / winprob.py (applied at tree emission), by
strategy_view's greedy-completion, and by the one-time rewrite of the committed
JSON trees (``complete_committed_trees.py``).
"""
from __future__ import annotations


def letter_pattern(letter: str, word: str) -> str:
    """Branch key for guessing ``letter``: the letter at each position it fills
    in ``word``, ``_`` elsewhere -- matches the solvers' ``_pattern_str`` and the
    view's ``_branch_key``. ``letter`` is assumed present in ``word``."""
    return "".join(letter if ch == letter else "_" for ch in word)


def remaining_letters(word: str, guessed) -> list[str]:
    """Distinct letters of ``word`` not in ``guessed``, in order of first
    appearance -- the letters still to guess to finish the word."""
    seen, out = set(guessed), []
    for ch in word:
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


def completion_tail(word: str, guessed, *, leaf_extra: dict | None = None) -> dict:
    """The single-branch node chain that guesses ``word``'s remaining letters
    (all hits) until it is complete, ending in ``{"word": word, **leaf_extra}``.
    With no letters left (already complete) it returns that leaf directly."""
    leaf: dict = {"word": word}
    if leaf_extra:
        leaf.update(leaf_extra)
    node = leaf
    for letter in reversed(remaining_letters(word, guessed)):
        node = {"guess": letter, "n": 1,
                "branches": {letter_pattern(letter, word): node}}
    return node


def complete_tree(node: dict, guessed: frozenset = frozenset()) -> dict:
    """Return ``node`` with every determined ``{"word"}`` leaf replaced by its
    completion tail, tracking the letters guessed from the root (each ancestor's
    ``guess``). Non-``word`` leaves (``capped`` / ``lost`` / empty ``{}``) are
    left untouched. Idempotent; mutates in place and returns the node."""
    if "branches" not in node:                        # a leaf
        if "word" in node:
            extra = {k: v for k, v in node.items() if k != "word"}
            return completion_tail(node["word"], guessed, leaf_extra=extra)
        return node
    g = guessed | {node["guess"]}
    node["branches"] = {k: complete_tree(v, g) for k, v in node["branches"].items()}
    return node

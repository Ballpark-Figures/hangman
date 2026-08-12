"""Guess-order statistics over a *set* of letters (shared pipeline helper).

Lifted VERBATIM from ``math/notebooks/letter_analysis.ipynb`` ("Guess-order
stats: set letters vs outside letters") so the same computation can feed a scene
data module without re-deriving it. The notebook still carries its own inline
copy of these functions; if you touch the logic, keep the two in sync (or make
the notebook import from here).

The headline quantity used by scene 16:

  ``set_before_outside`` -- given a collection of ``letters`` (a "set"), play the
  strategy under the *completion convention* (keep guessing until the word is
  fully revealed: the strategy's real guesses in order, then the word's remaining
  letters by first appearance) and count the number of set-letter OCCURRENCES
  (multi-counted) revealed BEFORE the first letter outside the set is guessed.
  Averaged over words per length (weighted by the ``weighting`` distribution,
  cross-length-normalised to N_L per length; == uniform-by-word for 'uniform').

For scene 16 the "set" is a cumulative union of tiers, and the fraction of a
length-L word filled when the strategy finishes that tier is
``set_before_outside(cum_set, L) / L``.

All strategies are built through the shared ``strategy_view.make_strategy`` -- the
math itself is never reinvented here.
"""
from pathlib import Path
import sys

_MATH = Path(__file__).resolve().parent
if str(_MATH) not in sys.path:
    sys.path.insert(0, str(_MATH))

import numpy as np
import strategy_view as sview


def _each_word_order(s, cb):
    """Call cb(word, path) for every word; `path` is the strategy's root->leaf guess
    sequence (real guesses, in order). `path` is REUSED (append/pop) -- copy it if you
    keep a reference. Walks the committed JSON tree for optimal/winprob, or a live
    greedy recursion for the greedy views."""
    g = s.g
    if hasattr(s, 'tree'):                            # optimal / winprob
        def walk(node, path):
            if 'branches' not in node:                # leaf
                for w in ([node['word']] if 'word' in node else node.get('capped', node.get('lost', []))):
                    cb(w, path)
                return
            path.append(node['guess'])
            for child in node['branches'].values():
                walk(child, path)
            path.pop()
        walk(s.tree, [])
    else:                                             # greedy / greedy_best
        f = s.word_freq()
        oc = g._opener_index(getattr(s, '_opener', None))
        def walk(S, gb, path):
            if S.shape[0] <= 1:
                if S.shape[0] == 1:
                    cb(g.words[int(S[0])], path)
                return
            c = g._pick_o(S, gb, f, oc)               # greedy's guess (honours a forced opener)
            pats = g.masks[S, c]
            ngb = gb | (1 << c)
            path.append(chr(97 + int(c)))
            for pat in np.unique(pats):
                walk(S[pats == pat], ngb, path)
            path.pop()
        walk(np.arange(g.N), 0, [])


def _order_metrics(order, w, Lset):
    """(set_before_outside, pairs) for one word's guess `order` (distinct letters, in
    order) and the set `Lset`. Pairs, per set letter alpha: the number of outside
    letters guessed before alpha -- OR, if alpha is NEVER guessed for this word, every
    outside letter that IS guessed (so seldom-guessed set letters are penalised, not
    rewarded)."""
    first_out = next((k for k, ch in enumerate(order) if ch not in Lset), len(order))
    before = sum(w.count(ch) for ch in order[:first_out])
    beta_before = pairs = guessed_in = 0
    for ch in order:
        if ch in Lset:
            pairs += beta_before                      # outside letters guessed before this alpha
            guessed_in += 1
        else:
            beta_before += 1
    pairs += (len(Lset) - guessed_in) * beta_before   # never-guessed alphas: all outside count
    return before, pairs


def _accumulate(s, Lset):
    """ONE traversal (via _each_word_order) accumulating both metrics over all words.
    A word's guess `order` is its root->leaf guess path (the completion convention's
    real guesses) then the word's remaining letters by first appearance. Each word
    contributes its cross-length effective weight freq * N_L/total_freq_L (so it sums
    to N_L per length -- common branches count proportionally; == uniform-by-word when
    weighting='uniform'). Returns (sum_before, sum_pairs, sum_weight, n_words)."""
    g = s.g
    freq = s.word_freq()
    total = float(freq.sum())
    scale = (g.N / total) if total else 0.0
    idx = g._index
    tot = [0.0, 0.0, 0.0, 0]                           # sum_before, sum_pairs, sum_weight, n
    def cb(w, path):
        seen, tail = set(path), []
        for ch in w:
            if ch not in seen:
                tail.append(ch); seen.add(ch)
        before, pairs = _order_metrics(path + tail, w, Lset)
        wt = float(freq[idx[w]]) * scale
        tot[0] += wt * before; tot[1] += wt * pairs; tot[2] += wt; tot[3] += 1
    _each_word_order(s, cb)
    return tot


def set_before_outside_by_length(letters, lengths=range(1, 21), *, strategy="optimal",
                                 weighting="uniform", budget=None, fill_capped=True):
    """Per-length average ``set_before_outside`` for the collection ``letters`` (see
    module docstring). Returns ``{length: avg_before}`` for every length with a
    committed solve (lengths with no solve are omitted). ONE tree traversal per length.
    """
    Lset = {c for c in letters.lower() if c.isalpha()}
    out = {}
    for L in lengths:
        s = sview.make_strategy(strategy, L, weighting=weighting, budget=budget,
                                fill_capped=fill_capped)
        if not s.available:
            continue
        sb, _pr, sw, _n = _accumulate(s, Lset)
        out[L] = (sb / sw) if sw else 0.0
    return out

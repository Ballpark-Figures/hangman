"""One notebook-facing interface over every hangman strategy.

The explorer notebook is built around :class:`strategy.GreedyGame`'s evaluation
surface -- ``per_word_misses``, ``trace``, ``state``, ``states_at_depth``,
``misses_by_starting_letter``. This module exposes that SAME surface for all four
strategies so a single ``STRATEGY`` selector drives every cell:

  "greedy"        -- greedy from the start (GreedyGame, live)
  "greedy_best"   -- forced best first letter, then greedy (GreedyGame, live)
  "optimal"       -- minimise expected misses (cached tree, data/shared/optimal/)
  "winprob"       -- maximise P(win within a miss budget k) (data/shared/winprob/)

The greedy pair is computed live and works for ANY weighting (including the new
word-mode distributions). ``optimal``/``winprob`` are replayed from the solver's
committed JSON trees; a generic walker (:class:`TreeStrategyView`) reconstructs
per-word misses, traces, node inspection and depth-k frontiers from a tree by
re-using GreedyGame's masks and board rendering, so the output matches the greedy
path field-for-field. When a strategy+weighting(+budget) has no committed solve,
:func:`make_strategy` returns an ``available == False`` view whose ``note`` says
what to run -- the notebook prints that instead of erroring.

``misses_by_starting_letter`` (the forced-opener sweep) is greedy-family only: it
means "force each opener, then play the strategy", which for optimal/winprob would
need a re-solve per opener that isn't cached. Those views return ``None`` for it.
"""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import numpy as np

import strategy
import wordlist
from tree_complete import complete_tree

ALPHABET = strategy.ALPHABET
_SHARED = Path(__file__).resolve().parent / "data" / "shared"


# --------------------------------------------------------------------------- #
# freq resolution (never lets a missing distribution crash the notebook)
# --------------------------------------------------------------------------- #
def _resolve_freq(weighting: str, length: int, min_zipf: float):
    """``(freq, note)`` for ``weighting`` -- ``note`` is set only on failure
    (e.g. a word-mode CSV that has not been generated yet)."""
    try:
        return wordlist.resolve_weighting(weighting, length, min_zipf=min_zipf), None
    except (FileNotFoundError, ValueError) as e:
        return None, str(e)


# --------------------------------------------------------------------------- #
# base view
# --------------------------------------------------------------------------- #
class StrategyView:
    """Uniform interface the notebook calls regardless of the backing strategy."""

    #: does this (strategy, weighting, length[, budget]) have a usable strategy?
    available = True
    #: human note -- why unavailable, or a caveat (e.g. capped approximation)
    note = ""

    def __init__(self, game: strategy.GreedyGame, freq, weighting: str,
                 kind: str, label: str):
        self.g = game
        self.freq = freq
        self.weighting = weighting
        self.kind = kind          # "greedy" | "greedy_best" | "optimal" | "winprob"
        self.label = label        # display label, e.g. "optimal (cap 11*)"
        self.length = game.length

    # -- capabilities -------------------------------------------------------
    def supports(self, feature: str) -> bool:
        """Whether ``feature`` (e.g. 'starting_letter') is defined for this view."""
        return True

    # -- headline -----------------------------------------------------------
    def opener(self) -> str: ...
    def headline_value(self) -> float | None: ...
    def headline_label(self) -> str: ...
    def summary(self) -> dict: ...

    # -- weighting ----------------------------------------------------------
    def word_freq(self) -> np.ndarray:
        """Per-word frequency weight under this view's weighting (aligned to
        ``g.words``; all-ones for uniform). This is the SAME array the strategy /
        headline use, so a node's ``fmass`` sums a subset of it."""
        return self.g._coerce_freq(self.freq)

    # -- evaluation (parity surface) ----------------------------------------
    def per_word_misses(self) -> np.ndarray: ...       # nan == unresolved

    def per_word_status(self) -> np.ndarray:
        """Per-word status aligned to words: 0 resolved, 1 capped (optimal),
        2 lost (winprob), 3 greedy-finished (capped branch completed greedily).
        The base view has no unresolved/greedy states, so all zeros."""
        return np.zeros(self.g.N, dtype=np.int8)

    def trace(self, word: str) -> list[tuple[str, bool]]: ...
    def state(self, board: str, missed="") -> dict: ...
    def states_at_depth(self, k: int) -> list[dict]: ...

    def misses_by_starting_letter(self) -> dict[str, float] | None:
        """Forced-opener sweep -- greedy-family only; ``None`` otherwise."""
        return None


class UnavailableView(StrategyView):
    """No committed solve for this combination. Every op returns empty; the
    notebook is expected to check ``available`` and print ``note``."""

    available = False

    def __init__(self, game, freq, weighting, kind, label, note):
        super().__init__(game, freq, weighting, kind, label)
        self.note = note

    def opener(self): return "?"
    def headline_value(self): return None
    def headline_label(self): return self.label
    def summary(self): return {"available": False, "note": self.note}
    def per_word_misses(self): return np.full(self.g.N, np.nan)
    def trace(self, word): return []
    def state(self, board, missed=""): return {"available": False, "reason": self.note}
    def states_at_depth(self, k): return []


# --------------------------------------------------------------------------- #
# greedy family -- delegate straight to GreedyGame (live, vectorised, exact)
# --------------------------------------------------------------------------- #
class GreedyStrategyView(StrategyView):
    """``greedy`` (opener=None) or ``greedy_best`` (forced best first letter)."""

    def __init__(self, game, freq, weighting, kind):
        self._opener = (None if kind == "greedy"
                        else game.best_opener_misses(freq)[0])
        label = "greedy" if kind == "greedy" else f"greedy+best opener {self._opener!r}"
        super().__init__(game, freq, weighting, kind, label)

    def opener(self):
        return (self.g.greedy_first_letter(self.freq) if self._opener is None
                else self._opener)

    def headline_value(self):
        if self._opener is None:
            return self.g.average_misses(self.freq)
        return self.g.best_opener_misses(self.freq)[1]

    def headline_label(self):
        return "avg misses"

    def summary(self):
        return {"opener": self.opener(), "avg_misses": self.headline_value()}

    def per_word_misses(self):
        return self.g.per_word_misses(self.freq, opener=self._opener)

    def trace(self, word):
        return self.g.trace(word, self.freq, opener=self._opener)

    def state(self, board, missed=""):
        return self.g.state(board, missed, self.freq, opener=self._opener)

    def states_at_depth(self, k):
        return self.g.states_at_depth(k, self.freq, opener=self._opener)

    def misses_by_starting_letter(self):
        # The forced-opener sweep is only well-defined for pure greedy after the
        # opener; expose it for both greedy views (greedy_best simply highlights
        # its own opener among the same bars).
        return self.g.misses_by_starting_letter(self.freq)


# --------------------------------------------------------------------------- #
# optimal / winprob -- replay the committed JSON decision tree
# --------------------------------------------------------------------------- #
class TreeStrategyView(StrategyView):
    """Walk a solver's committed tree to reproduce the full evaluation surface.

    Internal nodes are ``{"guess", "n", "branches": {board: child}}``; leaves are
    ``{"word"}`` / ``{"capped": [...]}`` (optimal) or ``{"word", "misses"}`` /
    ``{"lost": [...]}`` (winprob). Branch keys are the cumulative revealed board,
    so a child is found by rendering the post-guess board with the game's own
    ``_node_board`` -- guaranteeing tree navigation and greedy share one board
    convention.
    """

    def __init__(self, game, freq, weighting, kind, label, tree: dict,
                 meta: dict | None = None, *, greedy_finish: bool = False):
        super().__init__(game, freq, weighting, kind, label)
        self.tree = tree
        self.meta = meta or {}
        self._pw = None            # cached (misses, status)
        self._f = game._coerce_freq(freq)             # greedy-below uses this weighting
        #: words whose (optimal) branch was truncated and completed with greedy
        self._greedy_mask = np.zeros(game.N, dtype=bool)
        if greedy_finish and kind == "optimal":
            # Optimal above the cap, greedy below: rewrite every capped leaf into a
            # real greedy subtree so every replay surface treats it like any branch.
            self.tree = self._fill_capped(self.tree, 0, np.arange(game.N))
        # Play to word COMPLETION, not just determination: extend every determined
        # leaf with its single-branch completion tail (guaranteed hits, no misses).
        # Idempotent -- a no-op on trees already completed at emission.
        self.tree = complete_tree(self.tree)

    # -- tree helpers -------------------------------------------------------
    @staticmethod
    def _is_leaf(node: dict) -> bool:
        return "branches" not in node

    def _branch_key(self, gi: int, pat: int) -> str:
        """The branch key for guessing letter ``gi`` with revealed mask ``pat``.

        Tree keys are PER-GUESS -- only the just-played letter's positions, ``_``
        elsewhere (a miss is all blanks). Ancestor reveals are NOT carried into the
        key, so navigation keys on this guess alone (display still uses the game's
        cumulative ``_node_board``)."""
        b = ["_"] * self.length
        c = ALPHABET[gi]
        for p in range(self.length):
            if (pat >> p) & 1:
                b[p] = c
        return "".join(b)

    def _child(self, node: dict, gi: int, pat: int) -> dict:
        return node["branches"][self._branch_key(gi, int(pat))]

    # -- greedy completion of capped branches -------------------------------
    def _greedy_subtree(self, S: np.ndarray, guessed_bits: int) -> dict:
        """A greedy decision subtree (SAME node schema as the solver tree) that
        resolves candidate set ``S`` from state ``guessed_bits``, so every replay
        walk treats it exactly like an optimal branch. Grows from the TRUE guessed
        letters (not a fresh restart), which yields the same miss count as the
        solver's ``_greedy_ub`` while never re-guessing an already-revealed letter.
        """
        n = int(S.shape[0])
        if n <= 1:
            return {"word": self.g.words[int(S[0])]} if n == 1 else {}
        c = self.g._pick(S, guessed_bits, self._f)        # same rule as greedy _solve
        pats = self.g.masks[S, c]
        nxt = guessed_bits | (1 << c)
        branches = {self._branch_key(c, int(pat)): self._greedy_subtree(S[pats == pat], nxt)
                    for pat in np.unique(pats)}
        return {"guess": ALPHABET[c], "n": n, "branches": branches}

    def _fill_capped(self, node: dict, guessed_bits: int, S: np.ndarray) -> dict:
        """Replace every capped leaf under ``node`` with a greedy subtree grown
        from that node's candidate set + already-guessed letters. Records the
        completed words in ``self._greedy_mask``. Mutates and returns ``node``."""
        if "capped" in node:
            self._greedy_mask[S] = True
            return self._greedy_subtree(S, guessed_bits)
        if self._is_leaf(node):                           # {"word"} or {} -- nothing to do
            return node
        gi = ord(node["guess"]) - 97
        pats = self.g.masks[S, gi]
        for pat in np.unique(pats):
            grp = S[pats == pat]
            key = self._branch_key(gi, int(pat))
            node["branches"][key] = self._fill_capped(node["branches"][key],
                                                      guessed_bits | (1 << gi), grp)
        return node

    # -- per-word misses (single DFS, assigns every word to its leaf) --------
    def _compute_per_word(self):
        N = self.g.N
        masks = self.g.masks
        misses = np.full(N, np.nan)
        status = np.zeros(N, dtype=np.int8)   # 0 resolved, 1 capped, 2 lost

        def rec(node, S, gb, m):
            if self._is_leaf(node):
                misses[S] = m
                if "capped" in node:
                    status[S] = 1
                elif "lost" in node:
                    status[S] = 2
                return
            gi = ord(node["guess"]) - 97
            pats = masks[S, gi]
            for pat in np.unique(pats):
                grp = S[pats == pat]
                ngb = gb | (1 << gi)
                rec(self._child(node, gi, pat), grp, ngb, m + int(pat == 0))

        rec(self.tree, np.arange(N), 0, 0)
        status[self._greedy_mask] = 3          # capped branch, completed greedily
        self._pw = (misses, status)
        return self._pw

    def _per_word(self):
        return self._pw or self._compute_per_word()

    def per_word_misses(self):
        return self._per_word()[0]

    def per_word_status(self) -> np.ndarray:
        """0 resolved, 1 capped (optimal), 2 lost (winprob), aligned to words."""
        return self._per_word()[1]

    # -- headline -----------------------------------------------------------
    def opener(self):
        return self.tree.get("guess", "?")

    def headline_value(self):
        if self.kind == "winprob":
            return self.meta.get("p_win")
        misses, status = self._per_word()
        f = self.g._coerce_freq(self.freq)
        ok = (status == 0) | (status == 3)     # optimal + greedy-completed (upper bound)
        if not ok.any():
            return None
        return float((f[ok] * misses[ok]).sum() / f[ok].sum())

    def headline_label(self):
        if self.kind == "winprob":
            return f"P(win<={self.meta.get('n')})"
        return "avg misses"

    def summary(self):
        misses, status = self._per_word()
        out = {"opener": self.opener(), "note": self.note}
        if self.kind == "winprob":
            out.update(p_win=self.meta.get("p_win"),
                       e_misses_given_win=self.meta.get("e_misses"),
                       budget=self.meta.get("n"),
                       lost=int((status == 2).sum()))
        else:
            out.update(avg_misses=self.headline_value(),
                       capped=int((status == 1).sum()),
                       greedy_finished=int((status == 3).sum()))
        return out

    # -- trace one word -----------------------------------------------------
    def trace(self, word):
        i = self.g._index[word]
        masks = self.g.masks
        node, gb, seq = self.tree, 0, []
        while not self._is_leaf(node):
            gi = ord(node["guess"]) - 97
            hit = bool(masks[i, gi])
            seq.append((ALPHABET[gi], hit))
            gb |= 1 << gi
            node = self._child(node, gi, masks[i, gi])
        # resolved leaf: fill remaining letters as guaranteed hits (as greedy does)
        if "word" in node:
            for c in range(26):
                if masks[i, c] and not (gb >> c) & 1:
                    seq.append((ALPHABET[c], True))
                    gb |= 1 << c
        return seq

    # -- locate a node ------------------------------------------------------
    def state(self, board, missed=""):
        g = self.g
        required = g._parse_state(board, missed)
        norm_board, norm_missed = g._render_required(required)
        base = {"board": norm_board, "missed": norm_missed}

        node, S, gb, remaining = self.tree, np.arange(g.N), 0, dict(required)
        while remaining:
            if self._is_leaf(node):
                return {**base, "reachable": False, "candidates": [],
                        "n": int(S.shape[0]), "determined": True,
                        "guess": None, "outcomes": [],
                        "reason": "the word is already resolved here; the strategy "
                                  "stops before those letters would be guessed"}
            gi = ord(node["guess"]) - 97
            if gi not in remaining:
                return {**base, "reachable": False,
                        "candidates": [g.words[i] for i in S],
                        "n": int(S.shape[0]), "determined": False,
                        "guess": ALPHABET[gi], "outcomes": [],
                        "reason": f"the strategy's next guess would be "
                                  f"{ALPHABET[gi]!r}, which this state has not guessed"}
            req = remaining.pop(gi)
            S = S[g.masks[S, gi] == req]
            gb |= 1 << gi
            if S.shape[0] == 0:
                return {**base, "reachable": False, "candidates": [], "n": 0,
                        "determined": False, "guess": None, "outcomes": [],
                        "reason": "no word matches this board"}
            key = self._branch_key(gi, req)
            if key not in node["branches"]:
                return {**base, "reachable": False,
                        "candidates": [g.words[i] for i in S], "n": int(S.shape[0]),
                        "determined": False, "guess": None, "outcomes": [],
                        "reason": "this board is not a node the strategy reaches"}
            node = node["branches"][key]

        determined = self._is_leaf(node)
        out = {**base, "reachable": True,
               "candidates": [g.words[i] for i in S], "n": int(S.shape[0]),
               "determined": determined, "guess": None, "outcomes": []}
        if determined:
            return out
        gi = ord(node["guess"]) - 97
        out["guess"] = ALPHABET[gi]
        pats = g.masks[S, gi]
        for pat in np.unique(pats):
            grp = S[pats == pat]
            cb, cm = g._node_board(grp, gb | (1 << gi))
            out["outcomes"].append({
                "letter": ALPHABET[gi], "hit": bool(pat),
                "board": cb, "missed": cm, "n": int(grp.shape[0]),
                "sample": [g.words[i] for i in grp[:8]]})
        return out

    # -- every node at depth k ---------------------------------------------
    def states_at_depth(self, k, *, include_determined=True):
        g = self.g
        frontier = [(self.tree, np.arange(g.N), 0)]     # (node, S, guessed_bits)
        for _ in range(k):
            nxt = []
            for node, S, gb in frontier:
                if self._is_leaf(node):
                    continue
                gi = ord(node["guess"]) - 97
                pats = g.masks[S, gi]
                for pat in np.unique(pats):
                    grp = S[pats == pat]
                    ngb = gb | (1 << gi)
                    nxt.append((self._child(node, gi, pat), grp, ngb))
            frontier = nxt
        rows = []
        for node, S, gb in frontier:
            determined = self._is_leaf(node)
            if determined and not include_determined:
                continue
            board, missed = g._node_board(S, gb)
            rows.append({
                "board": board, "missed": missed, "n": int(S.shape[0]),
                "fmass": float(self._f[S].sum()),
                "determined": determined,
                "guess": None if determined else node["guess"],
                "sample": [g.words[i] for i in S[:6]]})
        return rows

    def supports(self, feature):
        return feature != "starting_letter"


# --------------------------------------------------------------------------- #
# loaders
# --------------------------------------------------------------------------- #
def _optimal_cap_file(weighting: str, length: int):
    """``(path, cap, converged)`` for the best committed optimal tree, or None.

    Prefers the cap the convergence log marks ``converged == 1`` (the proven
    uncapped optimum); otherwise the deepest cap on disk (a capped approximation,
    flagged by ``converged == False``)."""
    d = _SHARED / "optimal"
    caps = {}
    for p in glob.glob(str(d / f"len{length:02d}_{weighting}_cap*.json")):
        m = re.search(r"_cap(\d+)\.json$", p)
        if m:
            caps[int(m.group(1))] = Path(p)
    if not caps:
        return None
    conv = None
    csv = d / f"len{length:02d}_{weighting}.csv"
    if csv.exists():
        for line in csv.read_text().splitlines()[1:]:
            f = line.split(",")
            if len(f) >= 7 and f[6].strip() == "1":
                conv = int(f[0])
                break
    if conv is not None and conv in caps:
        return caps[conv], conv, True
    cap = max(caps)
    return caps[cap], cap, False


def _load_optimal(game, freq, weighting, length, min_zipf, *, greedy_finish=True):
    found = _optimal_cap_file(weighting, length)
    if found is None:
        note = (f"no committed optimal solve for length {length}, weighting "
                f"{weighting!r} (only some weightings are solved) -- run "
                f"`python math/optimal.py {length} --weighted {weighting}`")
        return UnavailableView(game, freq, weighting, "optimal",
                               f"optimal ({weighting})", note)
    path, cap, converged = found
    tree = json.loads(path.read_text())
    fill = greedy_finish and not converged            # converged trees have no capped leaves
    if converged:
        label = f"optimal ({weighting})"
    elif fill:
        label = f"optimal ({weighting}, cap {cap}*+greedy)"
    else:
        label = f"optimal ({weighting}, cap {cap}*)"
    view = TreeStrategyView(game, freq, weighting, "optimal", label, tree,
                            meta={"cap": cap, "converged": converged, "greedy_finish": fill},
                            greedy_finish=fill)
    if not converged and fill:
        view.note = (f"capped approximation, greedy-completed: deepest committed cap is "
                     f"{cap}; branches truncated at the cap are finished with greedy (optimal "
                     f"above the cap, greedy below), so every word resolves. The headline avg "
                     f"is the greedy-completed UPPER bound on the true optimum (optimal.py's "
                     f"`upper` column); the true optimum is <= it. Set FILL_CAPPED=False for "
                     f"the raw capped view.")
    elif not converged:
        view.note = (f"capped approximation: deepest committed cap is {cap} and the "
                     f"solve has not converged, so some words stay unresolved "
                     f"(shown as 'capped'). The true optimum is <= these misses. "
                     f"Set FILL_CAPPED=True to greedy-complete them instead.")
    return view


def _winprob_budgets(weighting: str, length: int) -> list[int]:
    d = _SHARED / "winprob"
    out = []
    for p in glob.glob(str(d / f"len{length:02d}_{weighting}_n*.json")):
        m = re.search(r"_n(\d+)\.json$", p)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def _load_winprob(game, freq, weighting, length, budget, min_zipf):
    budgets = _winprob_budgets(weighting, length)
    if not budgets:
        note = (f"no committed winprob solve for length {length}, weighting "
                f"{weighting!r} -- run "
                f"`python math/winprob.py {length} --weighted {weighting}`")
        return UnavailableView(game, freq, weighting, "winprob",
                               f"winprob ({weighting})", note)
    if budget is None:
        budget = budgets[-1]          # most permissive budget on disk
    if budget not in budgets:
        note = (f"winprob budget k={budget} not solved for length {length}, "
                f"weighting {weighting!r}; available: {budgets}")
        return UnavailableView(game, freq, weighting, "winprob",
                               f"winprob ({weighting}, k={budget})", note)
    path = _SHARED / "winprob" / f"len{length:02d}_{weighting}_n{budget:02d}.json"
    payload = json.loads(path.read_text())
    label = f"winprob ({weighting}, k={budget})"
    view = TreeStrategyView(game, freq, weighting, "winprob", label,
                            payload["tree"],
                            meta={"n": budget, "p_win": payload.get("p_win"),
                                  "e_misses": payload.get("e_misses"),
                                  "budgets": budgets})
    view.note = (f"budget k={budget} of available {budgets}; maximises P(resolve "
                 f"within k misses). 'lost' words cannot be won within k.")
    return view


# --------------------------------------------------------------------------- #
# factory
# --------------------------------------------------------------------------- #
STRATEGIES = ("greedy", "greedy_best", "optimal", "winprob")


def make_strategy(name: str, length: int, *, weighting: str = "uniform",
                  budget: int | None = None, fill_capped: bool = True,
                  min_zipf: float = wordlist.DEFAULT_ZIPF,
                  game: strategy.GreedyGame | None = None) -> StrategyView:
    """Build the notebook's uniform view for ``name`` at ``length``/``weighting``.

    ``name`` in :data:`STRATEGIES`. ``budget`` picks the winprob miss budget k
    (default: the most permissive committed one). ``fill_capped`` (optimal only,
    unconverged solves): when True, branches truncated at the miss cap are finished
    with greedy so every word resolves and the headline is the greedy-completed
    upper bound; when False, capped words stay unresolved. Returns an
    ``available == False`` view (never raises) when there is no committed solve.
    """
    if name not in STRATEGIES:
        raise ValueError(f"unknown strategy {name!r}; choose one of {STRATEGIES}")
    g = game if game is not None and game.length == length else \
        strategy.GreedyGame(length, min_zipf=min_zipf)
    freq, ferr = _resolve_freq(weighting, length, min_zipf)

    if name in ("greedy", "greedy_best"):
        if ferr is not None:
            return UnavailableView(g, None, weighting, name, name, ferr)
        return GreedyStrategyView(g, freq, weighting, name)
    if name == "optimal":
        return _load_optimal(g, freq, weighting, length, min_zipf,
                             greedy_finish=fill_capped)
    return _load_winprob(g, freq, weighting, length, budget, min_zipf)

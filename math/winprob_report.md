# winprob: max win-probability hangman under a miss budget

This explains what `math/winprob.py` computes, how, and how we know it's correct.
It is a *different* objective from `optimal.py`, so it's worth being precise.

---

## 1. The question we're answering

Real hangman gives you a fixed number of wrong guesses — say `n` — and you win a
word if you finish it before running out. So the natural question is:

> **Playing optimally, for a given word length and a budget of `n` wrong
> guesses, what is the highest probability of winning?**

And, because many different strategies can tie for that highest probability, a
secondary preference:

> **Among all strategies that hit that maximum win-probability, which one wins
> its games with the fewest wrong guesses on average?**

So there are two numbers per `(length, n)`:

- **`P(win ≤ n)`** — the probability (over words) that we finish within `n`
  misses, maximized. *This is the thing we optimize.*
- **`E[miss | won]`** — of the games we *win*, the average number of wrong
  guesses. *This is only a tie-breaker*, used to choose among equally-winning
  strategies. It is conditional on winning, so it's always ≤ `n`.

By default every word is equally likely to be the secret word (**uniform
weighting**, same convention as `optimal.py`'s `_uniform` files), so "probability"
= "fraction of words". Switching to frequency weighting is a one-line change
(pass a `freq` vector to `WinProbSolver`) and a re-run; the machinery is identical.

### How this differs from optimal.py

| | `optimal.py` | `winprob.py` |
|---|---|---|
| optimizes | average misses over **all** words | **probability** of ≤ `n` misses |
| cares about a word that takes 8 misses | yes — 8 is worse than 3 | no — if `n=6`, it's just a loss, same as 20 |
| budget `n` | swept (iterative deepening) to find the true optimum | **fixed** — it's the rules of the game |
| tie-break | n/a | fewest misses among the won games |

The key conceptual point: **winprob treats the budget as a hard cliff.** A word
is either won (≤ `n` misses) or lost, and all losses are equal. That's what makes
it "win probability" rather than "average misses".

---

## 2. The game model (shared with optimal.py)

A strategy is a **decision tree**. At each node you have a set `S` of candidate
words still consistent with everything revealed so far, and `r` misses remaining.
You guess one letter `c`:

- Every word in `S` either **contains** `c` (revealing its positions) or **does
  not**. This splits `S` into groups by the *revealed pattern* of `c`
  (`masks[i, c]` — the bitmask of positions where `c` sits in word `i`).
- The group where `c` is **absent** (pattern `0`) is the only one that costs a
  **miss**: those words go to `r − 1`. Groups where `c` is present cost nothing
  and stay at `r`.

You keep going until a group narrows to a single word (**won**) or a word takes a
miss it can't afford (`r` would go below 0 → **lost**).

A subtlety that makes the whole thing tractable: the value of a position depends
only on `(S, r)` — the surviving set and misses left — **not** on which letters
you happened to guess to get there. (Any letter you'd already guessed to reach
`S` was non-splitting on `S`, so it's irrelevant to what's optimal from here.)
That's why we can memoize on `(S, r)`.

---

## 3. The computation: one pass over a lexicographic pair

Everything is a single recursion over `(S, r)` — `_solve` — that computes **both**
objectives at once as a lexicographic pair `(lost, miss)`:

- **`lost`** = minimum word-mass that *cannot* be won within `r` misses. This is
  the dual of win-probability (`won = mass(S) − lost`), and it's what we minimize:
  it's a *min-of-sum* and is *small* when P(win) is high, so alpha-beta bites hard
  (see §6). Maximizing `won` directly would be flat near the top — every letter
  wins ≈ everything — and wouldn't prune.
- **`miss`** = minimum total misses over the *won* words, among the min-`lost`
  play. A miss is charged **only** on the letter-absent branch (+1 per won word
  there) — that's "misses, not guesses."

The recurrence, choosing the letter that minimizes the pair lexicographically
(first `lost`, then `miss`):

```
lost = min over letters of [ Σ_present lost(p, r) + lost(absent, r−1) ]
miss = (for that letter)    Σ_present miss(p, r) + miss(absent, r−1) + won(absent, r−1)
```

with base cases `(0, 0)` for a lone/empty word, and `(mass, 0)` once the budget
goes negative (a lone word isolated by a fatal miss is *lost*, not won — the order
of these base cases matters).

**Pruning.** `_solve` takes a lexicographic upper bound `(bl, bm)` and threads the
remaining allowance into each child. A branch whose `(lost, miss)` can't beat the
incumbent returns a lower bound and is abandoned. Exact pairs are memoized; lex
lower bounds are cached separately so a later tighter query can reuse them.

**Why one pass, not two.** The primary and secondary objectives are lexicographic,
so carrying them as a pair lets a single alpha-beta prune on both at once. (An
earlier version split this into a `won` pass and a separate `mmin` tie-break pass;
merging them removed the redundant second traversal and roughly halved the memo
entries.)

### The chosen move, and the tree

`_solve` records the winning letter for each exact state in `self.move`. Walking
those moves from the root down — following the chosen letter and branching on its
outcomes — *is* the optimal strategy tree, which is what we save (see §5).
`E[miss | won]` reported in the table is just `miss(root, n) / won(root, n)`.

---

## 4. Why it's exact, and how we check

The recursion has optimal substructure (the `(S, r)` value is independent of
path history, per §2), so the memoized DP is exact by construction. But "by
construction" is a claim, so it's checked two independent ways — both currently
passing with **zero** discrepancy:

1. **`winprob_check.py` — independent re-derivation.** Re-solves the same
   objective on the **raw word strings** (letter-position tuples, one-pass
   lexicographic, no pruning, no clamps, no memo tricks) and compares `won` and
   `mmin` against the real solver over 800 random `(subset, budget)` cases across
   len4–7. Result: `max |dwon| = 0`, `max |dmmin| = 0`. This catches any bug in
   the encoding *or* the recurrence.

2. **`winprob_verify_tree.py` — the artifact plays for real.** Loads a saved tree
   and *plays every word of that length through it*: walk the guesses, count a
   miss whenever the guessed letter is absent, stop at a leaf. Then confirm the
   tree's realized `fraction won` and `mean misses over winners` equal the
   `p_win` / `e_misses` the solver reported and stored. For len14 (all `n`):
   exact match, every won word within budget, no unreachable words. This proves
   the *saved strategy itself* delivers the claimed numbers — not just that some
   internal number was computed.

A nice built-in sanity check: `E[miss | won]` at `n = 0` is exactly `0.000`
(winning with zero misses means zero misses), and `P(win ≤ n)` rises to `1.0`
at the shallowest `n` where every word is resolvable.

---

## 5. What gets saved

After each `n` finishes, the optimal tree is written to
`math/data/shared/winprob/len{LL}_{weighting}_n{NN}.json` — the **committed** side
(final trees sync between machines). The resume checkpoint goes to the
**gitignored** side, `math/data/local/winprob/len{LL}_{weighting}.memo.pkl`. Trees
are written *as each `n` completes*, so if a long run is killed later, the ones it
finished are already on disk.

Each file is self-describing:

```json
{
  "length": 14, "n": 2, "words": 302, "weighting": "uniform",
  "p_win": 1.0, "e_misses": 0.1424, "opener": "i",
  "tree": { "guess": "i", "n": 302, "branches": {
      "____________i_": { "guess": "...", "branches": { ... } },
      "______________": { ...absent branch... }
  }}
}
```

Node/leaf shapes (same convention as `optimal.py`, plus a `lost` leaf):

- internal node — `{"guess": letter, "n": words_here, "branches": {template: subtree}}`
- branch key `template` — the revealed pattern of the guess, e.g. `"e_e_"` (letter
  at positions 0 and 2) or `"____"` (absent).
- won leaf — `{"word": w, "misses": misses_used_to_reach_it}`
- lost leaf — `{"lost": [words]}` — a group that runs out of budget on an absent
  branch; these are exactly the words counted against `P(win)`.

So the tree is a complete, playable strategy over the whole dictionary, and it
tells you both the winners (with their miss counts) and the losers.

---

## 6. Performance: the dual formulation (why §3 minimizes `lost`)

The naive way to compute this is to *maximize won mass* directly. That is
hopelessly slow, and the reason is subtle: near the top of the tree almost every
first guess wins almost everything, so `won ≈ mass` for every letter — the
objective is **flat**, nothing stands out, and no branch can be pruned. An early
version worked this way and blew up (len7 n=6 = 54M states / 73 min; n=7 ran out
of memory).

The fix is to minimize the **dual** — `lost`, the mass you *fail* to win. This
is a *min-of-sum*, the exact shape `optimal.py` prunes, and `lost` is *small*
when `P(win)` is high, so a tight incumbent plus alpha-beta (threading the
remaining allowance into children, exact + lower-bound memo) cuts whole letters.
The miss tie-break gets the same alpha-beta, on the miss-sum. This is why §3 is
written in terms of `lost`.

**What this buys, honestly:**
- **High-P regime (long words, or any word at a generous `n`): big win.** These
  are exactly the cases that used to OOM. E.g. len8 n=5 (P = 0.999): the old
  won-maximizing solver couldn't finish even the win-probability for `n=5` in
  420s; the dual does the full pipeline (win-prob + misses + trees) through n=4
  in ~200s.
- **The miss tie-break is the remaining cost driver.** In fully-winnable regions
  every letter ties on `won`, so identifying the miss-minimizing one is where the
  time now goes (~half the states). Skipping the tie-break (P(win) only) would
  reach substantially higher `n`.
- **Low-P regime (short words at moderate `n`, e.g. len4/5 at `n=6`, P ≈ 0.3):
  still hard.** There `lost` is *large*, so there's nothing small to minimize and
  the dual can't prune. Those cases remain the domain of the cut/parallel
  decomposition or a big-RAM box.

Because the solver prints and saves each `n` as it lands, running
`python math/winprob.py 8 6` gives you the exact rows/trees for `n = 0,1,2,…` as
far as it gets, and you can kill it once it stalls without losing them.

---

## 7. Running it

```bash
python math/winprob.py LENGTH N [HEARTBEAT_SECONDS]   # default heartbeat 60s
```

- Prints a row per `n` (`P(win ≤ n)`, `E[miss | won]`, best opener) as it
  finishes, optimal-style heartbeats during long `n`'s, and a clean consolidated
  report at the end.
- Saves the tree to `math/data/shared/winprob/` (committed) and a resume
  checkpoint to `math/data/local/winprob/` (gitignored) per `n`. Re-running a
  deeper `N` resumes from the checkpoint; `--fresh` ignores it.

```bash
python math/winprob_check.py 4 5 6 7          # independent DP validation
python math/winprob_verify_tree.py            # replay every saved tree end-to-end
```

**Memory note:** at `n = 6` the mid-lengths are memory-hungry (hundreds of
thousands to millions of states). Run one at a time, and not alongside a running
`optimal.py` job — the box can't hold both.

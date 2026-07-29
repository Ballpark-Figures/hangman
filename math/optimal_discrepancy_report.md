# Optimal solver: tree-vs-reported-value discrepancy (handoff)

**Date:** 2026-07-29. **Status:** root-caused to a region of code, not yet fixed.
Pre-existing; *not* caused by the "play to completion" change (that was verified
numbers-invariant — raw and completed trees replay to identical per-word misses).

Reproduce anytime with `python math/optimal_tree_audit.py` (see bottom).

---

## TL;DR

The committed **optimal decision trees realize a higher average misses than the
value the solver reports** (CSV `capped_avg`) for mid lengths (L7–L10). The DP
*value* is fine in every regime we can independently check; the **serialized tree
policy is slightly suboptimal** — i.e. `optimal.py`'s move reconstruction /
value reconciliation loses a little in the deep, capped search. Gap is ~0.3–1%.

Because `strategy_view` (and therefore the notebooks and the tree animation)
*replays the tree*, the notebook's OPTIMAL per-word-misses / headline is this
slightly-suboptimal tree value, ~0.3–1% above the CSV `capped_avg` for L7–L10.
Small lengths, L11–L12, and the winprob solver are unaffected.

---

## Finding 1 — tree replay > reported optimum (L7–L10)

Replaying every length-L word through the committed converged uniform tree and
comparing to the CSV converged `capped_avg`:

| L | tree replay | CSV optimum | gap |
|---|-------------|-------------|------|
| 1 | 0.500000 | 0.500000 | 0 |
| 7 | 2.153943 | 2.142393 | +0.011550 |
| 8 | 1.454338 | 1.442187 | +0.012151 |
| 9 | 0.964484 | 0.958047 | +0.006437 |
| 10 | 0.679369 | 0.674606 | +0.004763 |
| 11 | 0.468721 | 0.468721 | 0 |
| 12 | 0.332061 | 0.332061 | 0 |

(L2–L6 uniform have no converged committed solve, so they're skipped here.)

Both numbers are ≥ the true optimum, so "tree > reported" means the **tree is
suboptimal by at least the gap**.

### It's the current solver, not stale data

Fresh in-process solve for L=10 (`optimal_tree_audit.py --fresh 10`):

```
DP reported (deepen)  = 0.674606
fresh tree replay     = 0.677583      <- current solver's own tree misses the value
committed tree replay = 0.679369      <- committed tree is worse still (older solver)
```

So: the DP reports 0.674606, but the tree built from that same solve only
realizes 0.677583. The committed tree (0.679369) is from an older solver version
that reconstructed even less well. Re-solving would improve the committed trees
(0.6794 → 0.6776) but would **not** close the gap to 0.6746.

### The DP value & reconstruction are correct in the simple regime

Fuzz of 400 random small instances (length-4 words, 6–16 candidates, **uncapped**
`solve`): brute-force true optimum == reported == tree replay, **exactly**, every
trial. Deeper tiny instances (length-6 over a 4-letter alphabet, via `deepen`)
also all agree — but they converge at cap 0–1 (small candidate sets resolve in
0–2 misses), so they don't exercise the suspect machinery.

### Localization

The defect is specific to the **deep, capped `deepen()` path**:
- the cap-by-cap loop with cross-cap memo reuse (`memo[(S.tobytes(), r)]`), and
- the depth-gated upper bounds in `_V` (`_opener_ub` / `_greedy_ub` / the loose
  `r * Σf` bound at `depth > _ub_depth`), and
- the `achievable`/`best_letter` storage that `_build_tree` → `_move` replays.

It does **not** manifest uncapped or shallow, which is why the small
brute-forceable instances can't witness it.

### Open question (determines the fix)

Not yet distinguished, because it needs an independent true optimum on a *large,
deep* instance (not brute-forceable):
- **(a) reconstruction bug** — the reported value is achievable but the stored
  move at some deep capped node isn't optimal, so the replayed tree exceeds it; or
- **(b) value under-estimate** — a reused *capped* memo value (which under-counts
  misses past the budget, `_V` returns 0.0 at `r==0`) leaks into a context where
  it shouldn't, making the reported value a slight under-estimate.

Both leave the committed trees slightly suboptimal in practice.

### Suggested next step

Add a self-check to the solver: after `deepen()` converges, assert that the
freshly built tree *replays* to the reported optimum (the audit's `--fresh` does
exactly this comparison). If it fails (it will for L≥7), bisect the deep/capped
path — most cheaply by instrumenting `_V` to flag any node whose stored
`best_letter` does not achieve the stored value when children are played
optimally (recompute that node with an INF budget and compare). Start at the
shallowest node where tree-move value ≠ memo value.

**Gated code:** `optimal.py` feeds `winprob.py`; keep both winprob exactness
gates green for any change (`winprob_check.py`, `winprob_verify_tree.py` — see
`winprob_report.md`).

---

## Finding 2 — `winprob_verify_tree.py` mis-weights non-uniform trees

Separate, pre-existing, smaller. The gate replays each saved tree and checks the
realized P(win) / E[miss|won] against the file, but weights words like this:

```python
if data.get("weighting", "uniform") == "uniform":
    wt = {w: 1.0 for w in words}          # correct for uniform
else:
    wt = wordlist.freq_weights(...)        # zipf frequency weights
```

That's right for `uniform` and `zipf`, but **wrong for `greedy` / `best_opener`
/ `greedy_word` / `best_opener_word`**, which use adversarially *reconstructed*
frequencies (via `wordlist.resolve_weighting`), not zipf `freq_weights`. So the
realized aggregates don't match the file and the tree FAILs. Because the gate is
`all(verify(p) for p in paths)`, it short-circuits on the first such file
(`len01_best_opener_n00.json`) and never checks the rest.

Net: the gate currently only truly validates 2 of the 6 weightings. All **94
uniform** winprob trees pass with 0.0 discrepancy (that's what confirmed the
completion migration).

**Fix (small, contained):** replace the uniform/`freq_weights` branch with
`wordlist.resolve_weighting(data["weighting"], L)` so every weighting is scored
with the exact weights its solve used. Then the gate can validate all six.

---

## Reproduce

```
python math/optimal_tree_audit.py            # the L7–L10 gap table above
python math/optimal_tree_audit.py --fresh 10 # reported vs fresh vs committed
python math/winprob_verify_tree.py math/data/shared/winprob/len*_uniform_n*.json
                                             # 94 uniform trees, ALL OK, 0.0 disc.
```

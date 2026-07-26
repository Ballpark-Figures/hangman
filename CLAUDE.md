# hangman video — specifics

hangman-only conventions. The shared cross-video rules (`bpkfigures/CLAUDE.md`)
and private operational notes (`dotclaude/CLAUDE.md`) load via the two in-tree
symlink imports below — a within-project `@import` path that points out via a
symlink (an additional-dir CLAUDE.md won't auto-load, and a cross-dir `@../`
import won't expand). Committed + portable. See `yahtzee/CLAUDE.md` "Config
loading" for the full cross-machine debugging history.

@CLAUDE.shared.md
@CLAUDE.private.md

## Script
- `animations/Script.md` is the video script. Scenes become
  `scenes/NN<name>.py`. (Fill in this video's script/scene conventions.)

## Math / data
- `math/data/wordlist_master.txt` — the curated frequency wordlist
  (`word<TAB>zipf`, built by `math/build_wordlist.py`: wordfreq → hunspell
  filter → zipf floor). Load it via `math/wordlist.py` (default cutoff
  `zipf >= 2.5`); explore in `math/notebooks/wordlist_explorer.ipynb`.
- Data lives in `math/`, NOT `animations/assets/`. Source inputs
  (`wordlist_master.txt`, `allowlist.txt`, `blocklist.txt`) sit at `math/data/`.
- **Solver outputs are split by git status:**
  - `math/data/shared/<solver>/` — **committed**: final trees + csv results,
    meant to sync between machines (`shared/optimal/`, `shared/winprob/`).
  - `math/data/local/<solver>/` — **gitignored**: resume checkpoints / memo
    pickles (regenerable, can be GBs; `.ckpt` for optimal, `.memo.pkl` for
    winprob). The whole `math/data/local/` tree is in `.gitignore`.

### Solvers
Two EXACT solvers over a grid of lengths 1–20 × 6 weightings (uniform, zipf,
greedy, greedy_word, best_opener, best_opener_word):
- **`optimal.py`** — minimizes frequency-weighted AVERAGE misses. Iterative
  deepening on a miss cap (solve cap=1,2,…, reusing the memo); "converged" at the
  first cap whose optimal tree leaves NO word capped (proves nothing truncated).
  Writes `lenNN_<method>.csv` (one row/cap, `converged` col) + per-cap tree JSONs.
- **`winprob.py`** — maximizes P(win) under a HARD miss budget n, sweeping
  n=0,1,2,…; writes `lenNN_<method>_nNN.json` (exact `p_win`), "done" at p_win=1.
  Single-pass lexicographic `_solve` minimizing the DUAL `lost` (it prunes; a
  direct won-max is FLAT and OOMs). **Do NOT retry greedy short-circuit or
  greedy-seeded won-max B&B — both failed (flat objective).** Full writeup:
  `math/winprob_report.md`. Exactness is GATED two ways (keep both for any change):
  `winprob_check.py` (re-solve on raw strings) + `winprob_verify_tree.py` (replay
  each word through a saved tree); both must show 0.0 discrepancy.
- **Weighting** resolves through ONE `wordlist.resolve_weighting(name, length)`
  used by both solvers (`--weighted <name>`): uniform→None, zipf→integer
  per-billion weights, greedy/best_opener→reconstructed adversarial freqs. It
  RAISES on an unknown name / not-yet-run freq_search — NEVER silently falls back.
- **Status tables** (which grid cells are done/partial/none): OPTIMAL cell = status
  from the CSV `converged` col; for a partial, bracket Δ = upper − lower where lower
  = last row's `capped_avg` and upper = lower + greedy-finish of that cap-tree's
  `"capped"` leaves (`OptimalSolver._greedy_ub`) — Δ→0 at convergence. WINPROB has
  no bound pair (each n exact) → report r = 1 − p_win as "unresolved" (NOT a solver
  bound). The generator is a throwaway script (run it as a bare
  `python3 <scratchpad>/fulltables.py`).

## Gameplay layout
- (Describe this video's on-screen layout and the assets in `animations/assets/`.)

## Style
- Uses `bpkfigures` style + the local `config.py` for colors/fonts.

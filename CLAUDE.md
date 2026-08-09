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
- **In the animation column, "fill in <letter>" while the beat is describing a MISS
  means write that letter BELOW THE GALLOWS (the running wrong-guess tally), NOT fill a
  blank.** A hit "fills in" a blank; a miss "fills in" the miss row. So a beat like
  "guess, fill in E" on a word without an E is a miss (E goes under the gallows + draws
  the next body part), not a contradiction. (Bit us on scene 02: read the miss "fill
  in"s as blank-fills and misread the whole win/loss structure — the markdown DID encode
  it. Word there is BALLPARK; the non-ballpark letters e/i/o/t/n/d are the losing misses.)

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

### Game / guess-order convention
- **A game runs until the word is FULLY revealed** — you keep guessing until every
  letter is up. So a word's **guess order** is: the strategy's *real* guesses (its
  own order, hits AND misses) up to the point the word is UNIQUELY DETERMINED, then
  the word's remaining (not-yet-guessed) letters appended in order of **first
  appearance** in the word. Letters that are absent from the word and were not
  guessed before determination are NOT part of the order (you never needed them).
  Any analysis over "which letter is guessed before which" uses THIS order.
- **KNOWN DISCREPANCY:** `strategy.py`'s `GreedyGame.trace` (and the tree replay in
  `strategy_view.py`) appends its post-determination tail **alphabetically**, not by
  first-appearance. That only affects the *display* order of the trailing revealed
  letters (miss counts are unaffected — the tail is all hits), so it's left as-is;
  code that needs the convention builds the order itself (see `letter_analysis.ipynb`
  `_guess_order`). Align `trace` to first-appearance only if asked.

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
- **The shared board is `animations/assets/game_board.py` (imported as `gb`) — every
  gameplay scene uses it (02rules, 94chalkgame, 04greedy); do NOT reinvent the
  layout.** Fixed positions on the chalkboard: word blanks centred on the LEFT
  (`BLANK_CX`), the gallows on the RIGHT (`HANG_POS`), the wrong-guess tally centred
  under the gallows base (`MISS_Y`), the guesser's speech bubble growing from the
  LEFT edge (`BUBBLE_TIP`, `tail="left"`). All marks are chalk. Stateless builders +
  constants: `gb.build_rules(length)` (pass `cx=`/`slot=`/`gap=` for a long word or a
  different centre), `gb.build_gallows()` → `(container, parts)`, `gb.miss_slots(container,
  letters)`, and `gb.reveal_letter` / `gb.miss_letter` / `gb.bubble`. A scene keeps its
  own `self.rules`/`self.hang`/`self.miss_slots_x` handles built from these.
- **Guessing a letter is a STANDARD TWO-STEP: (1) a speech bubble containing the letter
  pops from the left edge (`gb.bubble`), then (2) the letter is WRITTEN ON — chalk
  strokes via `Create`, LEFT→RIGHT — into its blank(s) on a hit, or into the miss row +
  the next body part on a miss; then dismiss the bubble.** "Guess X" ALWAYS means
  bubble-then-write; never just reveal a guessed letter. (Exception: scene 04's greedy
  A-walk shows the PICK via the frequency bar graph — a decision view, not a played-out
  guess — so it has no per-guess bubbles.)
- **Writing a letter = draw its chalk STROKES with `Create` (the hand-written look),
  not `FadeIn`.** To write several letters, flatten their strokes into one VGroup and
  `LaggedStartMap(Create, strokes)` (Create over a whole multi-stroke letter inside a
  LaggedStart throws `int * VMobject`; Create over single strokes is fine).
- **"Written font" = the hand-drawn `chalk_letter` strokes (chalkboard.py), NOT the
  Inter `crisp_text`.** When the script says a word is "in written font," render it with
  chalk strokes (see scene 04's `_word_grid`, which monospaces them to equal width).
- **DEFAULT to the written (chalk) font for ALL text on the chalkboard.** On a
  chalkboard scene, basically every piece of text — words, numbers, percentages,
  labels, titles — is chalk strokes (`chalk_letter` / `chalk_phrase` / `chalk_number`
  from chalkboard.py), NOT `crisp_text`. The chalk font is CAPITALS-ONLY plus digits
  and the punctuation `' . , : % # * !`; add a glyph to `_PUNCT` if you need another.
  Use `crisp_text` on the chalkboard ONLY when explicitly asked. (This is why a
  chalkboard bar chart uses `get_bar_chart` with chalk factories, not `get_histogram`,
  which is `crisp_text`-only.)
- **Win/loss recolour tints the WHOLE board** — revealed letters, the blanks, the miss
  row, AND the gallows (`self.hang` includes it) → green on a win, red on a loss.

## Style
- Uses `bpkfigures` style + the local `config.py` for colors/fonts.

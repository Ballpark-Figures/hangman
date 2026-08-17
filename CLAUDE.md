# hangman video — specifics

hangman-only conventions. The shared cross-video rules (`bpkfigures/CLAUDE.md`)
and private operational notes (`dotclaude/CLAUDE.md`) load via the two imports
below. `CLAUDE.shared.md` and `CLAUDE.private.md` are **real files in this repo** —
gitignored copies of `bpkfigures/CLAUDE.md` and `dotclaude/CLAUDE.md`, refreshed
at every session start by `dotclaude/hooks/refresh-claude-imports.py`. They
cannot be symlinks: a CLAUDE.md `@import` will not resolve to a target outside
the project directory, by any route. See `yahtzee/CLAUDE.md` "Config loading" for the
measurements and the full cross-machine history.

@CLAUDE.shared.md
@CLAUDE.private.md

> **Import canary — check this first.** If you cannot see the tokens
> `SHARED-RULES-LOADED` and `PRIVATE-RULES-LOADED` in your context, the imports
> above **silently failed** and you are missing every shared and private
> convention. The copies are machine-local and gitignored, so the usual cause is
> a repo where they were never created — a fresh clone that has not had
> `/sync-videos` run in it, so `.claude/settings.local.json` (and therefore the
> refreshing hook) does not exist yet. Recover by reading `bpkfigures/CLAUDE.md`
> and `dotclaude/CLAUDE.md` directly for this session, then regenerate the copies
> with `python3 ../../dotclaude/hooks/refresh-claude-imports.py .` and tell the
> user to run `/sync-videos`.
>
> Do **not** trust a hook that claims to inject the rules as context: a
> SessionStart hook emitting the full ~121KB gets capped by the harness, saved to
> a file, and replaced with a ~2KB preview — which contains
> `SHARED-RULES-LOADED` and so reads as success while almost everything is
> missing. The tokens only mean anything when they come from the imports.

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
- **"Common uses" view (`assets/common_uses.py`) = a list of GAME STATES in which the
  strategy's NEXT guess is the letter in question** — each row is a blanked word with any
  letters MISSED so far listed to its RIGHT in red. (NO gallows — an earlier gallows +
  body-parts design was dropped; the misses moved from below to the right.) For a letter
  that is a BEST FIRST GUESS (E len 5-11, I len 12-20, A len 1-4 — the top tier) the state
  is a fresh game, so the row is LITERALLY a blank word (all underscores of that length)
  with no misses; a consonant guessed only AFTER misses shows a partially-revealed board +
  its red misses. Rows sit on a common rule BASELINE and the length label + misses align to
  the LETTER band (where a revealed letter sits), so blank and lettered rows line up. The
  example WORD behind a blank row is invisible (a blank board of length N is just N
  underscores); the sourced fact is the LENGTH RANGE each top-tier letter owns as the best
  first guess (partitions 1-20), cross-checked against `letter_analysis.ipynb`'s
  first-guess-by-length. Built on `assets/hangman_board.py` (brand-bg / ACCENT_FILL board —
  NOT the chalk `game_board.py`). Appears ONLY where the SCRIPT names a common-uses beat —
  so far scene 07 ONLY; 09-15 have none (heatmap + n-gram only, like test scene 96). NB the
  partial-board / red-misses path is BUILT but not yet exercised with real data (07 uses
  only blank boards) — expect to shake it out when a later scene first feeds it game states.

## Tier-list letter scenes (07 top · 09/10 high · 12/13 mid · 14/15 low · re-weighting …)
Every scene that walks ONE tier's letters shares `assets/tier_letter_scene.py`
(`TierLetterScene`, a `HangmanScene` subclass). The recurring visual per letter: fill the
letter into its tier row → the tier list tucks ×0.7 to the top-left → a big COPY of the
letter slides ↙ recolouring white→brand-blue → heatmap + n-gram views (+ common-uses only
where the script names it). A scene = its config + `@subscene` beats; @subscene beats MUST
live in the scene file (render tooling AST-scans it), so the base holds only helpers.
- **Config (class attrs):** `TIER_IDX` (0=TOP … 6=LOW↓) · `LETTERS` (that tier's letters,
  lowercase, in SLOT / tier-list order = `tier_list.TIER_LETTERS[TIER_IDX]`) · `FILLED`
  (`[(idx,"EIA"), …]` — the tiers ABOVE, shown filled from frame 0). `setup_scene` calls
  `self.build_board(on_screen=…)`: `True` = continuation (list centred on screen from frame
  0), `False` = blank start (an `establish` beat fades it in centred).
- **Beat helpers:** `enter_centered` · `intro_letter(i)` (first letter: fill+tuck+copy↙) ·
  `advance_letter(i)` (normal: clear views, return corner AS next fades in, copy↙) ·
  `rapid_letter(i, ch)` (a GROUP shown back-to-back: ONE-play crossfade — heatmap MORPHS +
  n-gram crossfades, views stay up) · `show_heat`/`add_ngram`/`show_common` (the two `show_`
  SWAP in over any current view in one play) · `clear_views` · `recenter_board`
  (tuck→centre, hand off to the next tier scene) / `close_all` (fade all → blank).
- **Reveal order is INDEPENDENT of slot order:** tiles live at fixed slots
  (`tier_tiles[slot]`), so a scene can reveal them in a PRESENTATION order that follows the
  narration; filling non-contiguous slots leaves visible gaps until the rest fill in. Use
  `rapid_letter` for letters the script GROUPS by shared profile, `advance_letter`
  otherwise. Done in 13 (present P/M/B rapid then U/G/H; tier lists PUGMBH). (Scene 14 was
  briefly built this way for V→W but is now a straight F/Y/V/W/K — the tier lists FYVWK, W
  above K, so no reorder is needed.)
- **Views** = the position heatmap ("Location Frequencies") + top n-grams ("Top N-grams"),
  each entering with 96's row-by-row rise, titles persisting; numbers come from the
  committed caches (`letter_heat_data` / `letter_ngram_data`). A row with no common-uses
  beat in the script → treat the scene exactly like test scene 96 (heatmap + n-gram only).
- **OPEN TODO — re-verify the START/END modes once scenes 08 and 11 exist.** The chain was
  built ASSUMING 08 (vowel/consonant discussion) and 11 (end-of-high-tier summary) are
  talking-head / non-tier-list scenes: 07 ends BLANK (`close_all`) → 08 → 09 blank-start
  (`establish`) → 10 continues centred → 10 recenters → 11 → 12 blank-start → 13/14/15
  continue centred, each recentring; 15 leaves the COMPLETE list centred for the "how to
  use it" scene. If 11 (or whatever precedes 14) actually LEAVES the tier list centred on
  screen, flip that scene's first line to `build_board(on_screen=True)` and delete its
  `establish` beat (reverse to go blank). So: **re-check 12's and 14's `on_screen=` when
  08/11 are built.** Also unresolved: all run_times are first-guess placeholders (a timing
  pass is owed), and the big letter for I / W reads as an ambiguous bar/shape.

## Frequency-search table scenes (19 short_words · 20 longer_words)
Scenes `19short_words.py` (lengths 2/3/4) and `20longer_words.py` (lengths 5-10 & 16, "ING
is king") present the CHOOSING strategy per word length as TABLES on the brand `BG_COLOR` (a
`HangmanScene` — NOT chalk, NOT navy): LEFT = letter-combo patterns + multipliers, RIGHT =
the chosen words + their frequency share, under a "N-Letter Words" title.
- **Shared base `assets/word_tables_scene.py` (`WordTablesScene`)** holds the table machinery
  (`_table`/`_reveal`/`_mono`/`_sig2`/`_mult`/`_scene_title`/`_table_title`/`_censor` + the
  layout constants); BOTH scenes subclass it. Their `@subscene` beats live in each scene file
  (render tooling AST-scans the scene file), so the base holds ONLY plain helpers.
- **Scene 20 specifics:** SOURCED via `assets/long_words_data.py` → `long_words_cache.json`
  (same freq_search best_opener pipeline; the FULL nonzero-frequency word list for 5/6/7 so the
  ending filters are truthful, top-12 for 8/9/10/16). Its signature move is the ENDING FILTER
  (`_filter_words`): strip words ending in Y / ED / ER / ES / ING and REFLOW — stripped rows
  fade, survivors slide up, newcomers RISE FROM BELOW the window (uniform travel = window
  height, so they scroll in from the bottom and land exactly, no gap). Beats l/m/n show
  patterns + words TOGETHER (`_reveal_pair`); beat o (len 16) is words ONLY, centered + bigger,
  10 rows, no patterns.
- **Data = the multiplier-based adversarial search tuned against the best-opener guesser**
  (`freq_search.FrequencySearch`, objective `best_opener` — the `data/freq_search/best_opener/
  lenNN.csv` runs; NOT the per-word `word/` variant). Sourced + cached by
  `assets/short_words_data.py` → `short_words_cache.json` (render reads only the cache):
  `tables` per length (patterns from `multipliers_df()`, words from `frequencies_df()`) +
  `by_length` (the beat-a double plot: optimal avg misses per length, uniform vs best_opener,
  scene-17 convention — exact where converged, mean of bounds where not). Regenerate with
  `python3 short_words_data.py`.
- **Table conventions (all routed through single helpers in the scene):**
  - **Common vs Rare split:** pattern tables show ONLY multiplier != 1 — **Common = boosted
    (mult > 1)**, **Rare = reduced (mult < 1)**; the unchanged (×1) patterns are dropped.
    Word tables are Common (highest freq) / Rare (lowest). Rare tables appear at length 2 ONLY
    (per the script); lengths 3/4/… show Common only.
  - **Number formatting:** a MULTIPLIER is ONE DECIMAL PLACE (`_mult`, e.g. `18.0`/`510.8`);
    a word % is 2 SIGNIFICANT FIGURES (`_sig2`). Everywhere, both scenes.
  - **A PATTERN is BOLD and MONOSPACED** (`_mono`, fixed `CHAR_W` slot) so its letters line up
    into COLUMNS down the table; a WORD is BOLD but PLAIN (`_word_label`, `_table(mono=False)`),
    NOT letter-spaced (the per-letter column look was dropped for words — user preference). All
    words in a length's table are equal length, so a plain centred word still lines up. The
    multiplier/frequency numbers are plain (not bold, not monospaced).
  - **Stacked (length-2) tables align by their TITLE**, not their last row — the top pair
    (Common) share `STACK_TOP`, the bottom pair (Rare) share `STACK_BOTTOM_TITLE`, so the two
    Rare captions sit at the same y regardless of row count.
  - **Censoring a word** (the "guess the profanity-filtered word" gag, e.g. PIMP at length 4):
    replace the whole word with a transparent-black box (`_censor`, `INK` @ 0.55) built INTO
    the row so it's never shown clear — NOT a blur (manim has no native blur).
- **The beat-a / scene-17 double plot both use the SHARED `bpkfigures.bar_graph.grouped_bar_chart`**
  (see the shared canonical-patterns index) — a value-per-length, two-series grouped bar chart
  with axes/labels/title/legend; the scene just passes its two series + labels + `ink_color`.

## The "misses by word length" chart recurs in TWO forms — match by MEDIUM, not by grep
The avg-misses-per-length bar chart appears more than once; a scene RECAPPING it ("bring
back that chart") must reuse the form from the SAME background, not the first title a grep
turns up (this bit us on scene 21: matched scene 17's title when the user meant the
CHALKBOARD one — one round-trip). The two established forms:
- **CHALKBOARD** — `get_bar_chart` line-outline chalk bars titled **"Average Misses by Word
  Length"** (no x-axis title), GREEDY data (`greedy_data["avg_misses_by_length"]`): scene 04
  (chalk) + its scene 05 navy recap (crisp, same title/data).
- **BRAND bg** — `grouped_bar_chart` filled bars titled **"Optimal Misses per Word"** with
  x-axis **"Word Length"**, OPTIMAL data (`scene17_chart_cache.json`): scene 17.
Scene 21 (chalkboard) "brings back" this chart with the CHALKBOARD title ("Average Misses by
Word Length") but OPTIMAL data — a deliberate title/data mismatch the user chose (the script
says "optimal misses", scene 04's chalkboard chart is greedy). So when several named versions
of one chart exist, SURFACE them (or match by medium) rather than silently pick one.

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
- **The ACTIVE marks of the game are drawn SEQUENTIALLY, one at a time — a SINGLE hand
  writing.** The BLANKS/rules (left→right, one underscore fully before the next), a
  guessed letter written into its blank(s), the running miss row, the "Words Remaining"
  header/number: draw these with `LaggedStartMap(Create, strokes, lag_ratio=1.0)` (lag
  1.0 = a stroke finishes before the next begins) — NOT `lag_ratio < 1` (draws several
  at once) or a bare `Create(group)`. A single letter's own strokes may overlap slightly
  (the miss row uses `lag_ratio=0.5` for one letter), but DISTINCT active marks (each
  blank, each guessed letter) are strictly one-after-another. (Bit us repeatedly on the
  blanks getting drawn simultaneously.)
- **EXCEPTION — a BULK reference LIST/GRID (many words shown at once, not "written" as
  gameplay) FADES IN as a group, it is NOT drawn stroke-by-stroke.** e.g. scene 11's ~21
  remaining-words grid and scene 04's 156 E-combos: build the items, `arrange_in_grid`,
  scale-to-fit the region, and `FadeIn` the whole VGroup (see 04 `e_combos`). Sequential
  hand-drawing is for the game's own live marks; a big enumerated set is a display, so
  `FadeIn`. (Crossing such a list off can still be per-item.)
- **"Written font" = the hand-drawn `chalk_letter` strokes (`bpkfigures/chalkboard.py`), NOT the
  Inter `crisp_text`.** When the script says a word is "in written font," render it with
  chalk strokes (see scene 04's `_word_grid`, which monospaces them to equal width).
- **DEFAULT to the written (chalk) font for ALL text on the chalkboard.** On a
  chalkboard scene, basically every piece of text — words, numbers, percentages,
  labels, titles — is chalk strokes (`chalk_letter` / `chalk_phrase` / `chalk_number`
  from `bpkfigures/chalkboard.py` — now a SHARED asset, moved out of hangman/assets),
  NOT `crisp_text`. The chalk font is CAPITALS-ONLY plus digits
  and the punctuation `' . , : % # * !`; add a glyph to `_PUNCT` if you need another.
  Use `crisp_text` on the chalkboard ONLY when explicitly asked. (This is why a
  chalkboard bar chart uses `get_bar_chart` with chalk factories, not `get_histogram`,
  which is `crisp_text`-only.)
- **HANGMAN WORDS (and their letters/combos) are UPPERCASE EVERYWHERE — `.upper()` them
  when rendering from the game/wordlist.** The chalk font is capitals-only (above), and
  the NON-chalk views uppercase too: scene 17's word bars (`.upper()`), the navy tree
  scenes, and `hangman_board` (`blanked_board`/`missed_letters` render `.upper()`). So a
  word/letter/combo pulled from the game (`game.words`, a wordlist entry, a `_y`-style
  pattern) is displayed uppercase — never a lowercase `crisp_text`. Bonus: uppercasing
  keeps a ROW of words aligned for free (caps are uniform-height with no descenders, so
  the baseline drift that needs `baseline_at`/`baseline_labels` only bites lowercase).
  (Bit us: scene 18 first rendered its words + combos lowercase — the lone deviation from
  the convention — before matching the rest of the video.)
- **Chalk font AND line-drawn/outline graphs are ONLY for the CHALKBOARD.** The chalk
  strokes (`chalk_*`) and the "made out of lines" chart look (`bar_outline="open"`/
  `"closed"`, no fill) belong to the framed-chalkboard scenes (02/03/04/94). On a
  NON-chalkboard background — the navy tree scenes (the intro `01`, `05optimal`, the
  `92/95/98` tree scenes) — use `crisp_text` and FILLED shapes instead: `crisp_text`
  labels/titles (light ink, e.g. `WHITE`) and solid-fill bars (`get_bar_chart` with no
  `bar_outline`). So a chart RECAPPED from a chalkboard scene onto navy is re-rendered
  crisp + filled, not chalk. (Navy is the board's slate colour, but a bare navy scene is
  NOT the chalkboard.)
- **TREE styling = the INTRO's, not `tree_view`'s big circles.** The decision-tree scenes
  (`01`, `05optimal`) render a node as a `Dot` COLOURED BY MISS-COUNT (0 misses = `CHALK`
  off-white, then `LIGHT_PALETTE` reversed 1→purple … 6→red) with the guess letter in
  `crisp_text` **`color=BOARD_NAVY`** (knocked out of the disc), bold, height
  `NODE_LETTER_H`×radius; edges are `Line`s coloured by the child node's miss-count. The
  canonical builders are `92wintree_test.py`'s `_miss_color` / `_node_marker` (layout +
  camera-dive) — currently inlined/copied in `01`, so a shared `tree_view` extraction is a
  promote-candidate (ASK first). Do NOT use `tree_view.guess_node`'s solid `ACCENT_FILL`
  circle + white letter for these scenes — that's the *other* tree style (95/98's walk).
  - **`05optimal` overrides the colouring to BINARY: a MISS edge/node is RED, a HIT
    edge/node (and any guess node) is WHITE** — not the graduated per-miss-count palette
    (`_miss_color` there returns `LIGHT_RED`/`CHALK`). Scene `01` keeps the graduated scheme.
  - **Blanks are a LEAF annotation** in `05optimal`: the partially-filled word (+ the red
    missed letter under the miss child) sits only under the CURRENT frontier nodes.
    Expanding a node REMOVES its blanks and adds them under its new children; un-expanded
    siblings keep theirs. The red missed-letter tally ACCUMULATES down the path (A, then
    A O, then A O I …) and appears under EVERY blank that sits below a miss node.
  - **A "LEAF" is the FINAL GUESS, NOT the point the word is uniquely determined.** Per the
    game convention (a game runs until every letter is UP — see "Game / guess-order
    convention"), you keep guessing even once the word is known; those remaining guesses are
    GUARANTEED HITS. So the base case with **"Avg misses: 0" is the node where the word is
    already determined and only guaranteed-hit guesses remain** (its child is the final-guess
    leaf) — NOT a node that still has a real choice/miss ahead. Concretely at length 2: the
    A→O→I→E→U all-miss drill reaches the 2-word set {BY, MY}; guessing B splits it into a HIT
    (BY) and a MISS (MY); the **MY node** (now determined, next guess is a forced hit) is the
    avg-0 base case. Do NOT label a node "Avg misses: 0" just because the word is knowable —
    label the node from which every remaining guess cannot miss. (Bit us building beat g:
    conflated "uniquely determined" with "leaf/avg 0".)
  - **`05optimal`'s drill beats (d/e/f…) render each option as a DIAGONAL tree rooted at
    A: the MISS branch is always the LEFT child**, so the tree grows down-left and the
    root sits OFF-CENTRE (never re-centred as you drill). Grids are GREEDY-sorted (most
    remaining words containing the letter first → greedy's pick top-left). The drilled-past
    path (A→O→…) is SHRUNK (`PATH_SCALE`) so the active option subtree dominates; the
    path's hit-siblings drop their blanks. See `_diag_cell`/`_path_diag`/`_mini_tree`.
  - **Drilling one grid → the next is the PIECE-BY-PIECE transform `_transform_into`** (do
    NOT whole-object morph the tree — see bpkfigures "per-mobject ledger" + the blob-morph
    gotcha). Role handles (`_mini_tree.gdot/glab/kid`, `_path_diag.levels`,
    `_diag_cell.path/sub/drilled_edge`) let it pair each source node/edge → its counterpart
    cell: the ORIGINAL becomes the top-left cell (`ReplacementTransform`), copies become the
    rest (`TransformFromCopy`); the extra text (blanks/tallies) MOVES + shrinks with the
    tree while fading (not a fade-in-place); THEN the drilled node's letter fades in and its
    children grow (d-style sprout). Ends with `clear()`+`add(cells)` to re-track clean
    groups. (This design cost ~10 rounds to converge — see the e/f postmortem; keep it.)
  - **Scene 05 is COMPLETE (beats a…zb).** The tail: y compare-openers, z dedup, za the
    single-branch bad-guess, zb the paired chart.
  - **Morphing the on-screen A-tree (beat y `compare_openers`): SWAP-then-morph, don't
    crossfade or blob-morph.** By beat x the visible A-tree is a PATCHWORK assembled across
    ~14 beats from pieces of five `_ctree`s (a_ref root + slid o/i/e/u subtrees + separate hit
    branches + transformed diagonal edges) — there's no single recursive handle structure to
    pair. But it's GEOMETRICALLY identical to a fresh `_ctree` of the same stored `self.a_spec`.
    So `_a_replica` builds that clean single `_ctree` (aligned to the on-screen A node via
    `self.a_root`), swaps it in INVISIBLY (`self.clear()`+`add` — no frame renders between), and
    `_morph_trees` does a true 1:1 role-handle morph (dots→dots, edges→edges, letters ride in on
    their nodes). Same trick powers the return to full screen. Don't reach for a crossfade when a
    clean equivalent is one build call away.
  - **za `bad_guess` = a letter that can only MISS.** After a successful A gives `_A` (A in pos
    2), guessing U — impossible in any `_A` word (FA/LA/MA/PA/TA/YA) — has a SINGLE miss branch
    (straight DOWN, the forced single-child convention). Shows all of A's branches, each with its
    board. SOURCED: `_a` is A's pos-2 hit; U's option there has `splits=False`.
  - **zb `paired_chart` = greedy-vs-optimal avg misses by length.** Left bar greedy
    (`greedy_data['avg_misses_by_length']`), right bar optimal uniform — SOURCED from
    `scene17_chart_data['uniform'][L]` = `{avg, lower, upper, converged}` (REUSED, not a new data
    module; its bounds come from `math/data/shared/optimal/lenNN_uniform.csv` — `lower`=capped_avg,
    `upper`=cap-tree greedy-finished). UNSOLVED lengths (`converged: False`) → a RED bar to `lower`
    + a lighter band up to `upper`, via the extended `grouped_bar_chart(series_highlight=…, bands=…)`.
    (Peak drop for the VO: ~6% at length 11, greedy 0.500→optimal 0.469, exact.)
- **Win/loss recolour tints the WHOLE board** — revealed letters, the blanks, the miss
  row, AND the gallows (`self.hang` includes it) → green on a win, red on a loss.

## Style
- Uses `bpkfigures` style + the local `config.py` for colors/fonts.

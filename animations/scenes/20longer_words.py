"""SCENE 20 — LONGER WORDS (the choosing strategy for lengths 5-9 & 16; "ING is king").

Borrows heavily from scene 19 (short_words): the SAME brand light-blue background +
crisp_text tables, routed through the SHARED WordTablesScene base (assets/word_tables_scene)
— LEFT = letter-combo patterns (letter-spaced) + multipliers, RIGHT = the chosen words
(plain, NOT letter-spaced) + their frequency share, under an "N-Letter Words" title. What's
NEW here is the ENDING FILTER: the strategy concentrates its word choices on a few suffixes,
so we repeatedly strip an ending (Y / ED / ER / ES / ING) and REFLOW the list in ONE play —
the stripped words fade out while, overlapping, survivors slide up and new words rise in
from the bottom to refill the slots.

BEAT MAP (Script.md scene 20; --- delimited, 14 beats a-n):
  a five_patterns   — title "5-Letter Words"; LEFT Common Letter Patterns.
  b five_words      — RIGHT Common Words (almost all end in Y).
  c remove_y        — strip Y-ending words + reflow → what's left usually ends in S.
  d six_full        — title → "6-Letter Words"; clear len-5; LEFT patterns + RIGHT words TOGETHER.
  e remove_ed       — strip ED endings + reflow.
  f remove_er       — strip ER endings + reflow.
  g remove_es       — strip ES endings + reflow.
  h remove_ing      — strip ING endings + reflow → only NUTMEG & AZALEA remain.
  i seven_patterns  — title → "7-Letter Words"; clear len-6; LEFT Common Letter Patterns.
  j seven_words     — RIGHT Common Words (all end in ING).
  k remove_ing7     — strip ING endings + reflow → NOTHING left.
  l eight_full      — title → "8-Letter Words"; clear; LEFT patterns + RIGHT words together.
  m nine_full       — title → "9-Letter Words"; clear; patterns + words together.
  n sixteen_full    — title → "16-Letter Words"; clear; ONLY Common Words, CENTERED + bigger,
                      10 rows, columns spread WIDER, no patterns table (top word UNDERREPRESENTED).

DATA (SOURCED, cached): assets.long_words_data -> long_words_cache.json. Per length:
`common_patterns` (boosted multiplier rows, uppercased) + `words` (every word the strategy
uses — frequency > 0 — for lengths 5/6/7 so the filters are truthful; top-12 for 8/9/16).
Each word carries its sourced `pct`; the ending filters are deterministic string ops. The
73% / 97% aggregates in the voiceover are NOT shown (script column 2 doesn't ask for them).

REUSE MAP (styling sources):
  - table machinery : assets.word_tables_scene.WordTablesScene — `_table`/`_reveal`/`_mono`/
                      `_word_label`/`_sig2`/`_mult`/`_scene_title` + layout constants (shared w/ 19).
  - text/colour     : crisp_text, INK = BLACK (base).

FLAGS (owned by a human — tune/decide in the timing+polish pass):
  - ROWS_SHOWN, all geometry (columns, row spacing, the single-table top_y, beat-n spread/scale)
    + run_times = guesses.
  - table TITLES ("Common Letter Patterns"/"Common Words") are rendered captions; reword if undesired.
  - length-16 words are wide — beat n uses widened columns + a scale; a long PATTERN elsewhere
    still leans on `_word_label`/`_mono`'s max-width clamp.
  - Length-9 (beat m) is only partly ING (dominance is strongest at 7/8) — shown faithfully; the
    script's beat-m VO was updated to match ("not as many clear patterns for even longer words").

Render:  render 20a --fast (…20n)  /  render 20 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import long_words_data
from assets.word_tables_scene import (
    WordTablesScene, INK, LEFT_X, RIGHT_X, LABEL_DX, VALUE_DX,
    ROW_FS, TITLE_GAP, HDR_GAP, ROW_DY)

ROWS_SHOWN = 12                    # rows visible per table (the pool underneath is deeper)
LONG_TOP = 2.85                    # the single table-per-side title y (matches scene 19 len-3/4)


class Scene20(WordTablesScene):
    """Longer words — the choosing strategy for lengths 5-10 & 16. See docstring for beats."""

    def setup_scene(self):
        self.tables = long_words_data.get()["tables"]
        self.title = None
        self.left = None            # patterns table (LEFT)
        self.right = None           # words table (RIGHT) — carries filter/reflow state

    # ── patterns table (base machinery) ───────────────────────────────────────
    def _pat_table(self, L):
        rows = self._pat_rows(self.tables[str(L)]["common_patterns"])
        return self._table("Common Letter Patterns", ("Pattern", "Multiplier"),
                           rows, top_y=LONG_TOP, cx=LEFT_X)

    # ── word table with a filter/reflow POOL underneath the visible rows ───────
    def _word_table(self, L, *, n=ROWS_SHOWN, cx=RIGHT_X,
                    label_dx=LABEL_DX, value_dx=VALUE_DX, title="Common Words"):
        pool = self.tables[str(L)]["words"]
        shown = pool[:n]
        tab = self._table(title, ("Word", "Frequency"), self._word_rows(shown),
                          top_y=LONG_TOP, cx=cx, mono=False,     # words plain, not letter-spaced
                          label_dx=label_dx, value_dx=value_dx)
        tab.pool = list(pool)
        tab.words = [d["word"] for d in shown]
        tab.n, tab.cx = n, cx
        tab.label_dx, tab.value_dx = label_dx, value_dx
        tab.row_by_word = {tab.words[i]: tab.rows[i] for i in range(len(tab.words))}
        return tab

    def _row_y(self, i):
        return LONG_TOP - TITLE_GAP - HDR_GAP - i * ROW_DY

    def _word_row(self, d, y, cx=RIGHT_X, label_dx=LABEL_DX, value_dx=VALUE_DX):
        """One word row (plain word + plain % value) on baseline y."""
        lx, vx = cx + label_dx, cx + value_dx
        return VGroup(self._word_label(d["word"], lx, y),
                      crisp_text(self._sig2(d["pct"]) + "%", font_size=ROW_FS,
                                 color=INK, baseline_at=(vx, y)))

    def _filter_words(self, ending, run_time, fade_rt=0.35):
        """Strip words ending in `ending` from the RIGHT table's pool, then reflow. The
        stripped rows FADE OUT over a SHORT `fade_rt` while, concurrently, survivors slide
        up to their new slots and newly-promoted words RISE UP FROM BELOW the window over
        the full `run_time` (uniform travel = window height, so they scroll in from the
        bottom and land exactly, no gap). With NOTHING left to move (the 7-letter case) it
        degrades to a plain fade-out over the full `run_time`."""
        tab = self.right
        pred = lambda w: w.endswith(ending)
        new_pool = [d for d in tab.pool if not pred(d["word"])]
        new_shown = new_pool[:tab.n]
        old_index = {w: i for i, w in enumerate(tab.words)}
        travel = tab.n * ROW_DY                             # > window height → starts below it
        fades = [FadeOut(tab.row_by_word[w]) for w in tab.words if pred(w)]
        moves, new_row_by_word = [], {}
        for i, d in enumerate(new_shown):
            w, y = d["word"], self._row_y(i)
            if w in tab.row_by_word:                        # survivor → slide up in place
                row = tab.row_by_word[w]
                dy = (old_index[w] - i) * ROW_DY
                if dy:
                    moves.append(row.animate.shift(UP * dy))
            else:                                           # newcomer → rise from below
                row = self._word_row(d, y - travel, tab.cx, tab.label_dx, tab.value_dx)
                moves.append(row.animate.shift(UP * travel))
            new_row_by_word[w] = row
        if moves:                                           # fast fade OVER the longer reflow
            groups = [AnimationGroup(*moves, run_time=run_time)]
            if fades:
                groups.append(AnimationGroup(*fades, run_time=min(fade_rt, run_time)))
            self.play(*groups)
        elif fades:                                         # 7-letter: just a fade-out
            self.play(*fades, run_time=run_time)

        tab.pool, tab.words = new_pool, [d["word"] for d in new_shown]
        tab.row_by_word = new_row_by_word
        tab.rows = VGroup(*new_row_by_word.values()) if new_row_by_word else VGroup()

    # ── reveal / clear helpers ────────────────────────────────────────────────
    def _reveal_pair(self, left, right, rows_run_time):
        """Reveal LEFT + RIGHT tables TOGETHER (titles+headers, then all rows rise)."""
        self.play(FadeIn(left.title), FadeIn(left.header),
                  FadeIn(right.title), FadeIn(right.header), run_time=0.4)
        rows = [*left.rows, *right.rows]
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.3) for r in rows],
                              lag_ratio=0.06), run_time=rows_run_time)

    def _clear(self, tab):
        return [FadeOut(tab.title), FadeOut(tab.header), FadeOut(tab.rows)]

    def _next_length(self, L, run_time):
        """Swap the scene title to L-letter and clear the current tables."""
        new = self._scene_title(f"{L}-Letter Words")
        anims = [Transform(self.title, new)]
        if self.left:
            anims += self._clear(self.left)
        if self.right:
            anims += self._clear(self.right)
        self.play(*anims, run_time=run_time)
        self.left = self.right = None

    # a : "5-Letter Words"; LEFT Common Letter Patterns
    @subscene
    def five_patterns(self):
        self.title = self._scene_title("5-Letter Words")
        self.play(FadeIn(self.title), run_time=0.5)
        self.left = self._pat_table(5)
        self._reveal(self.left, 1.4)

    # b : RIGHT Common Words (almost all end in Y)
    @subscene
    def five_words(self):
        self.right = self._word_table(5)
        self._reveal(self.right, 1.4)

    # c : strip Y-ending words + reflow (survivors usually end in S)
    @subscene
    def remove_y(self):
        self._filter_words("Y", 1.3)

    # d : "6-Letter Words"; clear len-5; LEFT patterns + RIGHT words TOGETHER
    @subscene
    def six_full(self):
        self._next_length(6, 0.6)
        self.left = self._pat_table(6)
        self.right = self._word_table(6)
        self._reveal_pair(self.left, self.right, 1.6)

    # e : strip ED endings + reflow
    @subscene
    def remove_ed(self):
        self._filter_words("ED", 1.1)

    # f : strip ER endings + reflow
    @subscene
    def remove_er(self):
        self._filter_words("ER", 1.1)

    # g : strip ES endings + reflow
    @subscene
    def remove_es(self):
        self._filter_words("ES", 1.1)

    # h : strip ING endings + reflow → only NUTMEG & AZALEA remain
    @subscene
    def remove_ing(self):
        self._filter_words("ING", 1.1)

    # i : "7-Letter Words"; clear len-6; LEFT Common Letter Patterns
    @subscene
    def seven_patterns(self):
        self._next_length(7, 0.6)
        self.left = self._pat_table(7)
        self._reveal(self.left, 1.4)

    # j : RIGHT Common Words (all end in ING)
    @subscene
    def seven_words(self):
        self.right = self._word_table(7)
        self._reveal(self.right, 1.4)

    # k : strip ING endings + reflow → NOTHING left
    @subscene
    def remove_ing7(self):
        self._filter_words("ING", 0.9)

    # l : "8-Letter Words"; clear; LEFT patterns + RIGHT words together
    @subscene
    def eight_full(self):
        self._next_length(8, 0.6)
        self.left = self._pat_table(8)
        self.right = self._word_table(8)
        self._reveal_pair(self.left, self.right, 1.6)

    # m : "9-Letter Words"; clear; patterns + words together
    @subscene
    def nine_full(self):
        self._next_length(9, 0.6)
        self.left = self._pat_table(9)
        self.right = self._word_table(9)
        self._reveal_pair(self.left, self.right, 1.6)

    # n : "16-Letter Words"; clear; ONLY Common Words, CENTERED, 10 rows, bigger font,
    #     columns spread WIDER (word ↔ %) — no patterns table here (top word UNDERREPRESENTED)
    @subscene
    def sixteen_full(self):
        self._next_length(16, 0.6)
        self.right = self._word_table(16, n=10, cx=0.0, label_dx=-1.9, value_dx=1.9)
        VGroup(self.right.title, self.right.header, self.right.rows).scale(1.25, about_edge=UP)
        self._reveal(self.right, 1.6)

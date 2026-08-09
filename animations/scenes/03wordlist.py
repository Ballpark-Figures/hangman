"""SCENE 03 — building the word list, on the chalkboard (crisp white text).

A data scene: the wordfreq list fills the board (top ~100 words by frequency),
we find a frequency cutoff, then a running "Total words:" counter (Yahtzee
"average points remaining" style) drops category by category as we strip
non-letter tokens / spellcheck / curated junk, landing on the final 34,483 —
then a bar graph of the final list's word counts by length.

Backdrop = the shared wooden `chalkboard` (like 02/04); all data is `crisp_text`
in off-white CHALK (NOT chalk strokes — this is a dense data scene). Every number
is SOURCED from `assets/wordlist_data.py` (committed cache); the render reads only
the cache (no wordfreq/hunspell at render).

Script row 03, split on '—' → beats a–q (voiceover ↔ animation zip 1:1) + a new
by-length beat r (user-requested):
  a columns   — top ~100 words by frequency fill the board, "the" first
  b pcts      — a % of all English text appears next to each word
  c cutoff    — zoom to real words straddling the frequency cutoff + a divider
  d ranks     — freq (1-in-N) at right, rank at left; the line sits near ~54,000
  e extras    — example junk wordfreq keeps: proper noun / abbr / roman / apostrophe / accent
  f counter   — "Total words:" counter (53,572); cross an apostrophe word → 51,077
  g spell     — a proper noun crossed by the spellchecker → 34,941
  h bldg      — show BLDG (the abbreviation the VO rants about)
  i abbrev    — cross bldg → 34,777
  j single    — 'p' → 34,753        k initial — 'mph' → 34,708
  l roman     — 'xiv' → 34,686      m interj  — 'hmm' → 34,645
  n profanity — '$#@%' (random chars, not a real word) → 34,535
  o greek     — 'phi', dropping 1 FURTHER (as if pi went too) → 34,527
  p pi        — pi ✓, counter back up +1 → 34,528
  q disagree  — styrofoam ✓ (+6 add-backs) → 34,534, then a removal (−51) → 34,483
  r by_length — bar graph: final list's word count by length (peak len 7 = 5,541)

REUSE MAP (every element → its source):
  backdrop            → assets.chalkboard.chalkboard (shared, as 02/04)
  all text            → crisp_text (style), color CHALK / LIGHT_BLUE / accents
  colours             → style.py CHALK, LIGHT_BLUE (data), LIGHT_RED (cross),
                        LIGHT_GREEN (kept ✓), ACCENT_GOLD (peak/emphasis)
  the counter         → local ValueTracker+always_redraw count (Yahtzee 05
                        `perfect_average` pattern), rebuilt static per drop so
                        snapshots stay picklable
  by-length bar chart → local `_by_length_chart` (vertical bars) — MIRRORS scene
                        04's `_avg_chart`; a promote-to-shared candidate (flagged)
  every number        → assets.wordlist_data (committed cache)

Render:  render 03a --fast … 03r   /   render 03 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every FadeIn/Create
run_time, the per-drop count run_time (COUNT_RT), the LaggedStart lags, and every
inter-beat fade. All are inlined literals at the call sites.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import chalkboard, CHALK
from assets import game_board as gb
from assets import wordlist_data

DATA = wordlist_data.get()
STEP = {s["key"]: s for s in DATA["counter"]}      # counter step by key (sourced values)

# ── font sizes ────────────────────────────────────────────────────────────────
WORD_FS   = 15     # a word in the top-100 columns
PCT_FS    = 13     # its % of English text
CUT_FS    = 24     # a word straddling the cutoff
CUT_META  = 16     # its rank / frequency
EXTRA_FS  = 28     # an example "extra" word
TAG_FS    = 20     # its category tag
LABEL_FS  = 30     # "Total words:"
NUM_FS    = 66     # the counter number
REM_FS    = 26     # a crossed-off / kept example word

# ── layout: the top-100 columns (beats a–b) ───────────────────────────────────
COLS, ROWS   = 5, 20
TABLE_X0     = -6.9      # left edge of column 0's word
TABLE_DX     = 2.85      # column pitch
TABLE_Y0     = 3.45      # top row baseline
TABLE_DY     = 0.365     # row pitch
TABLE_CELL_W = 2.35      # word-left → pct-right span within a cell

# ── layout: the cutoff zoom (beats c–d) ───────────────────────────────────────
CUT_CX   = 0.0
CUT_DY   = 0.50
CUT_RANK_X = -2.0        # rank sits left of the word
CUT_FREQ_X = 2.0         # frequency sits right of the word

# ── layout: the counter + crossed-off stack (beats f–q) ───────────────────────
LABEL_POS = np.array([-4.6, 1.0, 0])
NUM_POS   = np.array([-4.6, -0.2, 0])
REM_X     = 1.3          # left edge of a removed word
REM_TOP_Y = 3.1
REM_DY    = 0.52

COUNT_RT = 1.0           # default per-drop count run_time


class Scene03(HangmanScene):
    """Building the word list on the chalkboard. See module docstring / beat map."""

    # the wooden chalkboard is the backdrop — on screen from frame 0
    def setup_scene(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── small text helpers ────────────────────────────────────────────────────
    def _txt(self, s, fs, *, color=CHALK, weight="NORMAL"):
        # crisp_text at small font sizes wraps multi-word strings at the frame edge
        # (the supersample makes the pre-scale Text frame-wide); every label in this
        # scene is single-line, so use non-breaking spaces so Pango never breaks.
        return crisp_text(s.replace(" ", " "), font_size=fs, color=color,
                          font=FONT, weight=weight)

    def _num_text(self, v):
        return crisp_text(f"{v:,}", font_size=NUM_FS, color=CHALK, font=FONT,
                          weight="BOLD").move_to(NUM_POS)

    # ══════════════════════════════════════════════════════════════════════════
    #  a–b : the wordfreq list — top-100 columns, then % each
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_table(self):
        words, pcts = VGroup(), VGroup()
        for i, e in enumerate(DATA["top_words"]):
            col, row = divmod(i, ROWS)
            ax = TABLE_X0 + col * TABLE_DX
            ay = TABLE_Y0 - row * TABLE_DY
            w = self._txt(e["word"], WORD_FS).move_to([ax, ay, 0], aligned_edge=LEFT)
            p = self._txt(f'{e["pct"]:.2f}%', PCT_FS, color=LIGHT_BLUE)
            p.move_to([ax + TABLE_CELL_W, ay, 0], aligned_edge=RIGHT)
            words.add(w)
            pcts.add(p)
        self.table = VGroup(words, pcts)
        self.table.words, self.table.pcts = words, pcts

    # a : the top ~100 words by frequency fill the board, "the" first
    @subscene
    def columns(self):
        self._setup_table()
        self.play(LaggedStartMap(FadeIn, self.table.words, lag_ratio=0.03),
                  run_time=2.2)

    # b : a % of all English text appears next to each word
    @subscene
    def pcts(self):
        self.play(LaggedStartMap(FadeIn, self.table.pcts, lag_ratio=0.02),
                  run_time=1.6)

    # ══════════════════════════════════════════════════════════════════════════
    #  c–d : the frequency cutoff — a divider + rank/freq on nearby words
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_cutoff(self):
        cr = DATA["cutoff_region"]
        words, ranks, freqs = VGroup(), VGroup(), VGroup()
        # sort each side by rank so the numbers climb monotonically toward the
        # divider (rank crosses ~53,572 at the line). top→down within each side.
        above = sorted(cr["above"], key=lambda e: e["rank"])
        below = sorted(cr["below"], key=lambda e: e["rank"])
        rows = ([(e, len(above) - 1 - i) for i, e in enumerate(above)] +   # above line
                [(e, -1 - i) for i, e in enumerate(below)])                # below line
        for e, slot in rows:
            y = (0.5 + slot * CUT_DY) if slot >= 0 else (slot + 0.5) * CUT_DY
            w = self._txt(e["word"], CUT_FS).move_to([CUT_CX, y, 0])
            r = self._txt(f'#{e["rank"]:,}', CUT_META, color=LIGHT_BLUE)
            r.move_to([CUT_RANK_X, y, 0], aligned_edge=RIGHT)
            # compact + non-breaking spaces so crisp_text keeps it on ONE line
            f = self._txt(f'1 in {e["per_n"]/1e6:.1f}M', CUT_META,
                          color=LIGHT_BLUE)
            f.move_to([CUT_FREQ_X, y, 0], aligned_edge=LEFT)
            words.add(w)
            ranks.add(r)
            freqs.add(f)
        divider = Line([CUT_CX - 3.4, 0, 0], [CUT_CX + 3.4, 0, 0],
                       color=ACCENT_GOLD, stroke_width=3)
        cap = self._txt("frequency cutoff", TAG_FS, color=ACCENT_GOLD)
        cap.next_to(divider, RIGHT, buff=0.25)
        self.cutoff = VGroup(words, ranks, freqs, divider, cap)
        self.cutoff.words, self.cutoff.ranks = words, ranks
        self.cutoff.freqs, self.cutoff.divider, self.cutoff.cap = freqs, divider, cap

    # c : zoom to real words straddling the cutoff, with a divider at the line
    @subscene
    def cutoff(self):
        self.play(FadeOut(self.table), run_time=0.6)
        self.table = None
        self._setup_cutoff()
        self.play(LaggedStartMap(FadeIn, self.cutoff.words, lag_ratio=0.06),
                  run_time=1.2)
        self.play(Create(self.cutoff.divider), FadeIn(self.cutoff.cap), run_time=0.7)

    # d : freq (1-in-N) at right, rank at left; the line sits near ~54,000
    @subscene
    def ranks(self):
        self.play(LaggedStartMap(FadeIn, self.cutoff.ranks, lag_ratio=0.05),
                  LaggedStartMap(FadeIn, self.cutoff.freqs, lag_ratio=0.05),
                  run_time=1.4)

    # ══════════════════════════════════════════════════════════════════════════
    #  e : example "extras" wordfreq keeps
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_extras(self):
        ex = DATA["extras"]
        rows = [(ex["proper"], "proper noun"), (ex["abbr"], "abbreviation"),
                (ex["roman"], "roman numeral"), (ex["apostrophe"], "apostrophe"),
                (ex["accented"], "accent")]
        grp = VGroup()
        for word, tag in rows:
            w = self._txt(word, EXTRA_FS, weight="BOLD")
            t = self._txt(f"({tag})", TAG_FS, color=LIGHT_BLUE)
            row = VGroup(w, t).arrange(RIGHT, buff=0.4)
            grp.add(row)
        grp.arrange(DOWN, buff=0.42, aligned_edge=LEFT).move_to(ORIGIN)
        self.extras = grp

    # e : show examples of extra words that made it into the list
    @subscene
    def extras(self):
        self.play(FadeOut(self.cutoff), run_time=0.6)
        self.cutoff = None
        self._setup_extras()
        self.play(LaggedStartMap(FadeIn, self.extras, lag_ratio=0.15), run_time=1.6)

    # ══════════════════════════════════════════════════════════════════════════
    #  f–q : the "Total words:" counter dropping category by category
    # ══════════════════════════════════════════════════════════════════════════
    def _add_removed(self, word, *, color=CHALK):
        m = self._txt(word, REM_FS, color=color)
        m.move_to([REM_X, REM_TOP_Y - self.rem_i * REM_DY, 0], aligned_edge=LEFT)
        self.rem_i += 1
        self.removed.add(m)
        return m

    def _strike(self, m, run_time=0.4):
        ln = Line(m.get_left() + LEFT * 0.08, m.get_right() + RIGHT * 0.08,
                  color=LIGHT_RED, stroke_width=4)
        self.removed.add(ln)
        self.play(Create(ln), run_time=run_time)
        return ln

    def _check(self, m, run_time=0.4):
        a = m.get_right() + RIGHT * 0.28
        chk = VMobject(stroke_color=LIGHT_GREEN, stroke_width=6)
        chk.set_points_as_corners([a + np.array([-0.12, 0.0, 0]),
                                   a + np.array([-0.02, -0.15, 0]),
                                   a + np.array([0.22, 0.2, 0])])
        self.removed.add(chk)
        self.play(Create(chk), run_time=run_time)
        return chk

    def _count_to(self, new, run_time):
        """Roll the counter to `new` (Yahtzee style), then leave a static number
        (no updater on self → snapshots stay picklable)."""
        tr = ValueTracker(self.counter_value)
        live = always_redraw(lambda: self._num_text(int(round(tr.get_value()))))
        self.remove(self.counter_num)
        self.add(live)
        self.play(tr.animate.set_value(new), run_time=run_time)
        self.remove(live)
        self.counter_value = new
        self.counter_num = self._num_text(new)
        self.add(self.counter_num)

    def _drop(self, word, value, *, run_time=COUNT_RT):
        """Standard removal beat: a word appears on the right, gets struck, the
        counter rolls to `value`."""
        m = self._add_removed(word)
        self.play(FadeIn(m), run_time=0.4)
        self._strike(m, 0.4)
        self._count_to(value, run_time)
        return m

    # f : the counter appears (53,572); cross an apostrophe word → 51,077
    @subscene
    def counter(self):
        self.play(FadeOut(self.extras), run_time=0.6)
        self.extras = None
        self.counter_value = DATA["anchors"]["start"]
        self.counter_label = self._txt("Total words:", LABEL_FS).move_to(LABEL_POS)
        self.counter_num = self._num_text(self.counter_value)
        self.removed = VGroup()
        self.rem_i = 0
        self.play(FadeIn(self.counter_label), FadeIn(self.counter_num), run_time=0.9)
        self._drop(STEP["non_letter"]["example"], STEP["non_letter"]["value"])

    # g : a proper noun the spellchecker drops → 34,941
    @subscene
    def spell(self):
        self._drop(STEP["hunspell"]["example"], STEP["hunspell"]["value"])

    # h : show BLDG (the abbreviation the VO rants about) — no cross yet
    @subscene
    def bldg(self):
        self.bldg_mob = self._add_removed(STEP["abbreviations"]["example"])
        self.play(FadeIn(self.bldg_mob), run_time=0.5)

    # i : cross bldg → 34,777
    @subscene
    def abbrev(self):
        self._strike(self.bldg_mob, 0.4)
        self._count_to(STEP["abbreviations"]["value"], COUNT_RT)

    # j : single letters — 'p' → 34,753
    @subscene
    def single(self):
        self._drop(STEP["single_letters"]["example"], STEP["single_letters"]["value"])

    # k : initialisms — 'mph' → 34,708
    @subscene
    def initial(self):
        self._drop(STEP["initialisms"]["example"], STEP["initialisms"]["value"])

    # l : roman numerals — 'xiv' → 34,686
    @subscene
    def roman(self):
        self._drop(STEP["roman_numerals"]["example"], STEP["roman_numerals"]["value"])

    # m : interjections — 'hmm' → 34,645
    @subscene
    def interj(self):
        self._drop(STEP["interjections"]["example"], STEP["interjections"]["value"])

    # n : profanity — '$#@%' (random chars, not a real word) → 34,535
    @subscene
    def profanity(self):
        self._drop(STEP["profanity"]["example"], STEP["profanity"]["value"])

    # o : greek letters — 'phi', dropping 1 FURTHER as if pi went too → 34,527
    @subscene
    def greek(self):
        s = STEP["greek_letters"]
        m = self._add_removed(s["example"])
        self.play(FadeIn(m), run_time=0.4)
        self._strike(m, 0.4)
        # the fake extra: pi is struck too (we pretend to remove it), counter dips 1 further
        self.pi_mob = self._add_removed(s.get("pi_example", "pi"))
        self.play(FadeIn(self.pi_mob), run_time=0.4)
        self.pi_strike = self._strike(self.pi_mob, 0.4)
        self._count_to(s["value"] - s.get("fake_extra", 0), COUNT_RT)   # 34,527

    # p : pi ✓ — restore it, counter back up +1 → 34,528
    @subscene
    def pi(self):
        self.play(FadeOut(self.pi_strike), run_time=0.3)
        self._check(self.pi_mob, 0.4)
        self._count_to(STEP["greek_letters"]["value"], 0.7)             # 34,528

    # q : disagreements — styrofoam ✓ (+6) → 34,534, then a removal (−51) → 34,483
    @subscene
    def disagree(self):
        up = STEP["disagree_up"]
        m = self._add_removed(up["example"], color=CHALK)
        self.play(FadeIn(m), run_time=0.4)
        self._check(m, 0.4)
        self._count_to(up["value"], 0.8)                               # 34,534
        down = STEP["disagree_down"]
        self._drop(down["example"], down["value"])                     # → 34,483

    # ══════════════════════════════════════════════════════════════════════════
    #  r : the final list's word count by length (NEW beat)
    # ══════════════════════════════════════════════════════════════════════════
    def _by_length_chart(self):
        """Vertical bar chart of the final list's word count by length. Mirrors
        scene 04's `_avg_chart` (a shared-asset promote candidate). Handles:
        .axes .bars .labels .title .bar_of{L}."""
        data = DATA["by_length"]
        lengths = [d["length"] for d in data]
        vals = [d["count"] for d in data]
        x0, x1, base, height = -6.6, 6.6, -3.0, 5.2
        ymax = max(vals)
        n = len(lengths)
        slot = (x1 - x0) / n
        xaxis = Line([x0, base, 0], [x1, base, 0], color=CHALK, stroke_width=3)
        bars, labels, bar_of = VGroup(), VGroup(), {}
        peak = max(range(n), key=lambda i: vals[i])
        for i, L in enumerate(lengths):
            h = max(vals[i] / ymax * height, 1e-3)
            x = x0 + (i + 0.5) * slot
            col = ACCENT_GOLD if i == peak else LIGHT_BLUE
            bar = Rectangle(width=slot * 0.72, height=h, fill_color=col,
                            fill_opacity=1.0, stroke_width=0)
            bar.move_to([x, base + h / 2, 0])
            bars.add(bar)
            bar_of[L] = bar
            lab = self._txt(str(L), 16).move_to([x, base - 0.3, 0])
            labels.add(lab)
        # value on the peak bar
        pk = self._txt(f"{vals[peak]:,}", 18, color=ACCENT_GOLD)
        pk.next_to(bars[peak], UP, buff=0.12)
        title = self._txt("Words by length", 34).move_to([0, base + height + 0.55, 0])
        grp = VGroup(xaxis, bars, labels, pk, title)
        grp.axes, grp.bars, grp.labels, grp.title = xaxis, bars, labels, title
        grp.bar_of = bar_of
        return grp

    # r : the by-length bar graph, then clear to the bare chalkboard (04 follows)
    @subscene
    def by_length(self):
        board = VGroup(self.counter_label, self.counter_num, self.removed)
        self.play(FadeOut(board), run_time=0.6)
        self.counter_label = self.counter_num = self.removed = None
        self.chart = self._by_length_chart()
        base_y = self.chart.axes.get_center()[1]
        full = self.chart.bars.copy()
        for b in self.chart.bars:
            b.stretch_to_fit_height(0.001).set_y(base_y)
        self.play(FadeIn(self.chart.axes), FadeIn(self.chart.labels),
                  FadeIn(self.chart.title),
                  LaggedStart(*[Transform(b, fb)
                                for b, fb in zip(self.chart.bars, full)],
                              lag_ratio=0.04), run_time=1.8)
        self.play(FadeIn(self.chart[3]), run_time=0.5)      # the peak value label
        self.wait(1.2)                                      # VO
        self.play(FadeOut(self.chart), run_time=0.7)        # clear → bare chalkboard

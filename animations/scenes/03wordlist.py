"""SCENE 03 — building the word list, on the chalkboard (WRITTEN chalk font).

A data scene: the final word list fills the board (top 96 words by frequency),
we find a frequency cutoff, then a running "TOTAL WORDS" tally drops category by
category as we strip non-letter tokens / spellcheck / curated junk, landing on
34,483 — then a bar graph of the final list's word counts by length.

EVERYTHING is the WRITTEN (chalk-stroke) font — `chalk_phrase`/`chalk_number`
(chalkboard.py), never `crisp_text` (the chalkboard default; see hangman
CLAUDE.md). The counter is a CASCADE: the current number sits at the bottom of a
column; to remove a category we write its example word beside the number, cross
off the word, cross off the number, and write the new number below. Kept/added
words (PI, STYROFOAM) are written in green and never struck. Every number is
SOURCED from `assets/wordlist_data.py` (committed cache).

Script row 03, split on '—' → beats a–q + a by-length beat r (user-requested):
  a columns   — top 96 FINAL-list words by frequency fill the board, "the" first
  b pcts      — a % of English text (2 sig figs) beside each word
  c cutoff    — real words straddling the frequency cutoff, divider midway between
  d ranks     — frequency (% ) at right FIRST, then rank at left
  e extras    — example junk kept by wordfreq: a proper noun / abbr / roman / apostrophe
  f–q counter — the TOTAL WORDS cascade dropping to 34,483 (see _remove); PI/
                STYROFOAM green; pi drops 1 EXTRA with the greek then comes back +1
  r by_length — bar graph of word count by length (peak len 7 = 5.5k); stays up

REUSE MAP:
  backdrop         → assets.chalkboard.chalkboard (shared, as 02/04)
  all text         → chalk_phrase / chalk_number / chalk_letter (chalkboard.py)
  colours          → CHALK (white), LIGHT_GREEN (kept ✓), ACCENT_GOLD (divider)
  by-length chart  → SHARED bpkfigures.bar_graph.get_bar_chart (chalk factories)
  every number     → assets.wordlist_data (committed cache)

Render:  render 03a --fast … 03r   /   render 03 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel): every Create/FadeIn run_time, the per-step
write/strike run_times, the LaggedStart lags, inter-beat fades — all inlined.
"""
from pathlib import Path
import sys
import math

import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import get_bar_chart
from assets.chalkboard import chalkboard, chalk_phrase, chalk_number, CHALK
from assets import wordlist_data

DATA = wordlist_data.get()
STEP = {s["key"]: s for s in DATA["counter"]}      # counter step by key (sourced)


def _pct_str(p):
    """A percentage rounded to 2 significant figures, in decimal (not scientific)
    notation: 5.37 -> '5.4%', 0.00316 -> '0.0032%'."""
    if p <= 0:
        return "0%"
    decimals = max(0, 1 - math.floor(math.log10(p)))
    return f"{p:.{decimals}f}%"


def _klabel(c):
    """A by-length bar count: >= 1000 shown as 'X.Xk' rounded to the nearest 100
    (5541 -> '5.5k'); below 1000 shown as the integer."""
    return f"{round(c / 100) / 10:.1f}k" if c >= 1000 else str(c)


def _sci_freq(p, y, x, *, height, color=CHALK):
    """A word's frequency (as a FRACTION, not a percentage — no % sign) in
    scientific notation, written in chalk, left-aligned at (x, y) on the mantissa:
    a 3.16e-5 % rate -> '3.2×10⁻⁷' (2-sig-fig mantissa, raised exponent). Returns a
    VGroup(mantissa+×10, exponent)."""
    frac = p / 100.0                                  # percentage -> fraction
    exp = math.floor(math.log10(frac))
    mant = frac / 10 ** exp
    base = chalk_phrase(f"{mant:.1f}×10", height=height, color=color)
    base.move_to([x, y, 0], aligned_edge=LEFT)
    sup = chalk_phrase(str(exp), height=height * 0.62, color=color)
    sup.next_to(base, RIGHT, buff=0.04).shift(UP * height * 0.30)
    return VGroup(base, sup)


# ── layout: the top-80 columns (beats a–b) ────────────────────────────────────
COLS, ROWS = 5, 16
COL_X0, COL_DX = -6.7, 2.85      # left edge of column 0's word / column pitch
ROW_Y0, ROW_DY = 3.55, 0.462     # top row baseline / row pitch (spread to fill)
PCT_DX = 1.35                    # word-left → pct-left within a cell
WORD_H, PCT_H = 0.24, 0.20

# ── layout: the cutoff zoom (beats c–d) ───────────────────────────────────────
CUT_CX = 0.0
CUT_G = 0.56                     # row gap; divider sits at y=0, midway between sides
CUT_WORD_H, CUT_META_H = 0.30, 0.22
CUT_RANK_X, CUT_FREQ_X = -2.1, 2.1

# ── layout: the TOTAL WORDS cascade (beats f–q) ───────────────────────────────
CAS_NUM_R = -1.2                 # right edge of the number column
CAS_WORD_L = -0.6                # left edge of the removed word (right of number)
CAS_LABEL_R = -3.0               # right edge of the "TOTAL WORDS:" label
CAS_Y0, CAS_DY = 3.10, 0.50
CAS_NUM_H, CAS_WORD_H, CAS_LABEL_H = 0.32, 0.32, 0.28


class Scene03(HangmanScene):
    """Building the word list on the chalkboard, in the written font. See docstring."""

    def setup_scene(self):
        self.cb = chalkboard(15.2, 8.4)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ══════════════════════════════════════════════════════════════════════════
    #  a–b : the word list — top-96 columns, then % each
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_table(self):
        words, pcts = VGroup(), VGroup()
        for i, e in enumerate(DATA["top_words"]):
            col, row = divmod(i, ROWS)
            ax = COL_X0 + col * COL_DX
            ay = ROW_Y0 - row * ROW_DY
            w = chalk_phrase(e["word"], height=WORD_H).move_to([ax, ay, 0],
                                                               aligned_edge=LEFT)
            # % right after the word (close, never overlapping a long word)
            p = chalk_phrase(_pct_str(e["pct"]), height=PCT_H, color=LIGHT_BLUE)
            p.next_to(w, RIGHT, buff=0.28).set_y(ay)
            words.add(w)
            pcts.add(p)
        self.table = VGroup(words, pcts)
        self.table.words, self.table.pcts = words, pcts

    # a : the top 96 FINAL-list words by frequency fill the board, "the" first
    @subscene
    def columns(self):
        self._setup_table()
        self.play(LaggedStartMap(FadeIn, self.table.words, lag_ratio=0.03),
                  run_time=2.2)

    # b : a % of English text (2 sig figs) beside each word
    @subscene
    def pcts(self):
        self.play(LaggedStartMap(FadeIn, self.table.pcts, lag_ratio=0.02),
                  run_time=1.6)

    # ══════════════════════════════════════════════════════════════════════════
    #  c–d : the frequency cutoff — a divider midway, then freq then rank
    # ══════════════════════════════════════════════════════════════════════════
    def _setup_cutoff(self):
        cr = DATA["cutoff_region"]
        above = sorted(cr["above"], key=lambda e: e["rank"])   # ascending rank
        below = sorted(cr["below"], key=lambda e: e["rank"])
        words, ranks, freqs = VGroup(), VGroup(), VGroup()
        placed = []                                            # (entry, y)
        for j, e in enumerate(above):                          # nearest-line last
            placed.append((e, (len(above) - j) * CUT_G - CUT_G / 2))
        for j, e in enumerate(below):                          # nearest-line first
            placed.append((e, -(j + 0.5) * CUT_G))
        for e, y in placed:
            words.add(chalk_phrase(e["word"], height=CUT_WORD_H).move_to([CUT_CX, y, 0]))
            r = chalk_phrase(f"#{e['rank']:,}", height=CUT_META_H)   # # sign back
            r.move_to([CUT_RANK_X, y, 0], aligned_edge=RIGHT)
            ranks.add(r)
            freqs.add(_sci_freq(e["pct"], y, CUT_FREQ_X, height=CUT_META_H))
        divider = Line([CUT_CX - 3.3, 0, 0], [CUT_CX + 3.3, 0, 0],
                       color=ACCENT_GOLD, stroke_width=3)
        cap = chalk_phrase("CUTOFF", height=0.24, color=ACCENT_GOLD)
        cap.next_to(divider, RIGHT, buff=0.3)
        self.cutoff = VGroup(words, ranks, freqs, divider, cap)
        self.cutoff.words, self.cutoff.ranks = words, ranks
        self.cutoff.freqs, self.cutoff.divider, self.cutoff.cap = freqs, divider, cap

    # c : zoom to real words straddling the cutoff, divider midway between sides
    @subscene
    def cutoff(self):
        self.play(FadeOut(self.table), run_time=0.6)
        self.table = None
        self._setup_cutoff()
        self.play(LaggedStartMap(FadeIn, self.cutoff.words, lag_ratio=0.06),
                  run_time=1.2)
        self.play(Create(self.cutoff.divider), FadeIn(self.cutoff.cap), run_time=0.7)

    # d : frequency (%) at right FIRST, then rank at left
    @subscene
    def ranks(self):
        self.play(LaggedStartMap(FadeIn, self.cutoff.freqs, lag_ratio=0.05),
                  run_time=1.0)
        self.play(LaggedStartMap(FadeIn, self.cutoff.ranks, lag_ratio=0.05),
                  run_time=1.0)

    # ══════════════════════════════════════════════════════════════════════════
    #  e : example "extras" wordfreq keeps (no category tags)
    # ══════════════════════════════════════════════════════════════════════════
    @subscene
    def extras(self):
        self.play(FadeOut(self.cutoff), run_time=0.6)
        self.cutoff = None
        ex = DATA["extras"]
        rows = [ex["proper"], ex["abbr"], ex["roman"], ex["apostrophe"]]
        grp = VGroup(*[chalk_phrase(w, height=0.44) for w in rows])
        grp.arrange(DOWN, buff=0.50).move_to(ORIGIN)
        self.extras = grp
        for w in grp:                    # one at a time, written on
            self._write(w, 0.6)

    # ══════════════════════════════════════════════════════════════════════════
    #  f–q : the TOTAL WORDS cascade dropping to 34,483
    # ══════════════════════════════════════════════════════════════════════════
    def _write(self, mob, run_time):
        """Write a chalk phrase on, stroke by stroke (the hand-written look)."""
        strokes = VGroup(*[s for glyph in mob for s in glyph])
        self.play(LaggedStartMap(Create, strokes, lag_ratio=0.6), run_time=run_time)

    def _strike(self, mob, run_time=0.35, color=CHALK):
        y = mob.get_center()[1]
        ln = Line([mob.get_left()[0] - 0.06, y, 0], [mob.get_right()[0] + 0.06, y, 0],
                  color=color, stroke_width=4)
        self.cascade.add(ln)
        self.play(Create(ln), run_time=run_time)

    def _write_word(self, text, *, color=CHALK, run_time=0.5):
        """Write the removed/kept example word to the right of the current number."""
        m = chalk_phrase(text, height=CAS_WORD_H, color=color)
        m.move_to([CAS_WORD_L, self.cas_y, 0], aligned_edge=LEFT)
        self.pending_word = m
        self.cascade.add(m)
        self._write(m, run_time)

    def _revise(self, new_value, *, strike_word=True, run_time=0.5):
        """Cross off the word (unless kept/green), cross off the current number, and
        write the new number one row below."""
        if strike_word and self.pending_word is not None:
            self._strike(self.pending_word, 0.35)
        self._strike(self.cur_num, 0.35)
        self.cas_y -= CAS_DY
        m = chalk_number(new_value, height=CAS_NUM_H)
        m.move_to([CAS_NUM_R, self.cas_y, 0], aligned_edge=RIGHT)
        self.cur_num, self.cur_value = m, new_value
        self.cascade.add(m)
        self._write(m, run_time)

    def _drop(self, word, new_value):
        self._write_word(word)
        self._revise(new_value)

    # f : the TOTAL WORDS tally appears; cross an apostrophe word → 51,077
    @subscene
    def counter(self):
        self.play(FadeOut(self.extras), run_time=0.6)
        self.extras = None
        self.cascade = VGroup()
        self.cas_y = CAS_Y0
        self.cas_value = DATA["anchors"]["start"]
        label = chalk_phrase("TOTAL WORDS:", height=CAS_LABEL_H)
        label.move_to([CAS_LABEL_R, self.cas_y, 0], aligned_edge=RIGHT)
        self.cur_num = chalk_number(self.cas_value, height=CAS_NUM_H)
        self.cur_num.move_to([CAS_NUM_R, self.cas_y, 0], aligned_edge=RIGHT)
        self.cur_value = self.cas_value
        self.pending_word = None
        self.cascade.add(label, self.cur_num)
        self._write(label, 0.9)                    # write out "TOTAL WORDS:"
        self._write(self.cur_num, 0.7)
        self._drop(STEP["non_letter"]["example"], STEP["non_letter"]["value"])

    # g : a proper noun the spellchecker drops → 34,941
    @subscene
    def spell(self):
        self._drop(STEP["hunspell"]["example"], STEP["hunspell"]["value"])

    # h : write BLDG beside the current number (no cross yet)
    @subscene
    def bldg(self):
        self._write_word(STEP["abbreviations"]["example"])

    # i : cross off BLDG → 34,777
    @subscene
    def abbrev(self):
        self._revise(STEP["abbreviations"]["value"])

    # j–n : single letters / initialisms / roman / interjections / profanity
    @subscene
    def single(self):
        self._drop(STEP["single_letters"]["example"], STEP["single_letters"]["value"])

    @subscene
    def initial(self):
        self._drop(STEP["initialisms"]["example"], STEP["initialisms"]["value"])

    @subscene
    def roman(self):
        self._drop(STEP["roman_numerals"]["example"], STEP["roman_numerals"]["value"])

    @subscene
    def interj(self):
        self._drop(STEP["interjections"]["example"], STEP["interjections"]["value"])

    # n : profanity — a grawlix, not a real word → 34,535
    @subscene
    def profanity(self):
        self._drop(STEP["profanity"]["example"], STEP["profanity"]["value"])

    # o : greek letters, dropping 1 EXTRA (as if pi went too) → 34,527
    @subscene
    def greek(self):
        s = STEP["greek_letters"]
        self._write_word(s["example"])
        self._revise(s["value"] - s.get("fake_extra", 0))          # 34,527

    # p : PI written in green — brings the count back up +1 → 34,528
    @subscene
    def pi(self):
        self._write_word(STEP["greek_letters"].get("pi_example", "pi"),
                         color=LIGHT_GREEN)
        self._revise(STEP["greek_letters"]["value"], strike_word=False)   # 34,528

    # q : STYROFOAM green (+6 add-backs) → 34,534, then a removal (−51) → 34,483
    @subscene
    def disagree(self):
        up = STEP["disagree_up"]
        self._write_word(up["example"], color=LIGHT_GREEN)
        self._revise(up["value"], strike_word=False)               # 34,534
        down = STEP["disagree_down"]
        self._drop(down["example"], down["value"])                 # → 34,483

    # ══════════════════════════════════════════════════════════════════════════
    #  r : the final list's word count by length (stays up; all counts white)
    # ══════════════════════════════════════════════════════════════════════════
    def _by_length_chart(self):
        counts = {d["length"]: d["count"] for d in DATA["by_length"]}
        return get_bar_chart(
            list(counts.items()), center=[0, -0.35, 0], width=13.2, height=4.6,
            bar_color=LIGHT_BLUE, ink_color=CHALK, bar_ratio=0.7,
            label_factory=lambda L: chalk_number(L, height=0.24, commas=False),
            label_buff=0.22,
            value_labels=True,
            value_factory=lambda c: chalk_phrase(_klabel(c), height=0.20),
            value_buff=0.10,
            x_axis=True,
            title_mobject=chalk_phrase("WORDS BY LENGTH", height=0.36),
            title_buff=0.5,
        )

    # r : clear the cascade, grow the by-length bars, all counts in white — STAY up
    @subscene
    def by_length(self):
        self.play(FadeOut(self.cascade), run_time=0.6)
        self.cascade = None
        self.chart = self._by_length_chart()
        self._write(self.chart.title, 1.0)                      # write out the title
        base_y = self.chart.x_axis.get_center()[1]
        full = self.chart.bars.copy()
        for b in self.chart.bars:
            b.stretch_to_fit_height(0.001).set_y(base_y)
        statics = VGroup(self.chart.x_axis, self.chart.labels)
        self.play(FadeIn(statics),
                  LaggedStart(*[Transform(b, fb)
                                for b, fb in zip(self.chart.bars, full)],
                              lag_ratio=0.04), run_time=1.8)
        self.play(FadeIn(self.chart.values), run_time=0.6)      # all counts, white

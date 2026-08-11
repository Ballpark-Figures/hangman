"""SCENE 08 — vowels vs consonants (a data interlude after the top tier).

On a NAVY background (transitions in from / back out to the light-blue world): a pie
of the vowel/consonant letter split, the vowel/consonant position-frequency grid
(red = vowel, blue = consonant), then before/after adjacency pies for VOWEL and
CONSONANT. Every number is SOURCED from the committed cache (`vowel_consonant_data`);
vowels = A E I O U Y (Y always a vowel). Pies use the pie asset's `fan_all`
(continuous clockwise sweep). Standalone — does NOT use the tier-list machinery.

Script row 08, split on '—' → beats (voiceover ↔ animation zip 1:1):
  a to_navy        turn the background navy
  b alphabet_grid  the 26 letters in 13 rows of 2 (every vowel is at an ODD position)
  c color_letters  turn the vowels red, the consonants blue
  d letters_pie    pie: % of all letters that are vowels vs consonants (clears the grid)
  e freq           the vowel/consonant position-frequency grid, titled (stats NARRATED)
  f vowel_row      VOWEL (⅓ down): before-pie ← VOWEL → after-pie (letters adjacent)
  g consonant_row  CONSONANT (⅔ down): before-pie ← CONSONANT → after-pie
  h to_light       clear + turn the background back to light blue

ROUGH first pass — LAYOUT + TIMING are guesses (the beat-c callout placement and the
pie sizes/positions especially). Judge from the video; tune freely.

Render:  render 08a --fast  (…08f)  /  render 08 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import BOARD_NAVY
from assets import vowel_consonant_data as vcd
from assets.vowel_consonant_view import vowel_consonant_heatmaps
from bpkfigures.pie_chart import get_pie_chart

VOWEL_C = LIGHT_RED        # vowels red, consonants blue — throughout the scene
CONS_C  = LIGHT_BLUE
ROW_PIE_R = 0.95           # small before/after pies
BIG_PIE_R = 2.0
ROW_Y     = 2.2            # VOWEL row at +ROW_Y, CONSONANT row at -ROW_Y


class Scene08(HangmanScene):
    """Vowels vs consonants. See the module docstring for the beat map."""

    def setup_scene(self):
        self.d = vcd.get()                          # cached stats (no compute at render)
        self.navy_rect = None
        self.alpha = None
        self.pie = None
        self.view = self.view_title = None

    def _navy(self):
        r = Rectangle(width=config.frame_width, height=config.frame_height,
                      fill_color=BOARD_NAVY, fill_opacity=1.0, stroke_width=0)
        r.set_z_index(-10)
        return r

    def _alphabet_grid(self):
        """The 26 letters in 13 rows × 2 columns — left column the ODD alphabet
        positions (A C E … Y), right column the even (B D … Z). Every vowel is odd, so
        A E I O U Y all land in the left column. `.by_letter` maps char → mobject."""
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        grid, by_letter = VGroup(), {}
        col_x, pitch = (-0.3, 0.3), 0.6      # column gap ≈ row pitch (square-ish grid)
        top = (13 - 1) / 2 * pitch
        for i in range(13):
            for c in range(2):
                ch = alphabet[2 * i + c]
                t = crisp_text(ch, font_size=34, color=WHITE, weight=BOLD)
                t.move_to([col_x[c], top - i * pitch, 0])
                grid.add(t)
                by_letter[ch] = t
        grid.by_letter = by_letter
        return grid

    def _rise(self, parent, rows, *, lag_ratio=0.14, shift=0.28):
        """The letter/tier views' row-by-row rise-in (see TierLetterScene._rise)."""
        for row in rows:
            row.shift(DOWN * shift).set_opacity(0)
        self.add(parent)
        return LaggedStart(*[row.animate.shift(UP * shift).set_opacity(1)
                             for row in rows], lag_ratio=lag_ratio)

    def _class_pie(self, dist, center):
        """A small [vowel, consonant] pie at `center`, % shown INSIDE each slice."""
        return get_pie_chart([dist["vowel"], dist["consonant"]],
                             colors=[VOWEL_C, CONS_C], radius=ROW_PIE_R, center=center,
                             label_mode="inside", label_font_size=18, inner_frac=0.5,
                             inner_frac_spread=0.45, stroke_color=WHITE)

    def _adjacency_row(self, name, adj, y, word_color):
        """`name` (VOWEL red / CONSONANT blue) centred at height y, a before-pie to its
        LEFT and an after-pie to its RIGHT, each linked by a short line."""
        word = crisp_text(name, font_size=FONT_SIZE_LG,
                          color=word_color).move_to([0, y, 0])
        after = self._class_pie(adj["after"], [4.2, y, 0])
        before = self._class_pie(adj["before"], [-4.2, y, 0])
        # connect to each pie's true geometric centre (.pie_center), NOT the VGroup
        # bbox centre — the labels stick out asymmetrically and would skew the lines
        line_r = Line(word.get_right() + RIGHT * 0.25,
                      after.pie_center + LEFT * (ROW_PIE_R + 0.2),
                      color=WHITE, stroke_width=3)
        line_l = Line(word.get_left() + LEFT * 0.25,
                      before.pie_center + RIGHT * (ROW_PIE_R + 0.2),
                      color=WHITE, stroke_width=3)
        self.play(FadeIn(word), Create(line_l), Create(line_r), run_time=0.8)
        after.fan_all(self, 1.0)
        before.fan_all(self, 1.0)

    # a : turn the background navy
    @subscene
    def to_navy(self):
        self.navy_rect = self._navy()
        self.play(FadeIn(self.navy_rect), run_time=0.8)

    # b : the alphabet in 13 rows of 2 (every vowel is at an ODD position → left column)
    @subscene
    def alphabet_grid(self):
        self.alpha = self._alphabet_grid()
        self.play(LaggedStartMap(FadeIn, self.alpha, lag_ratio=0.03), run_time=1.2)

    # c : colour the vowels red, the consonants blue
    @subscene
    def color_letters(self):
        self.play(*[t.animate.set_color(VOWEL_C if ch in "AEIOUY" else CONS_C)
                    for ch, t in self.alpha.by_letter.items()], run_time=1.0)

    # d : pie — % of all letters that are vowels vs consonants (clears the grid first)
    @subscene
    def letters_pie(self):
        self.play(FadeOut(self.alpha), run_time=0.5)
        self.alpha = None
        v = self.d["pct_vowel_letters"]
        self.pie = get_pie_chart([v, 1 - v], colors=[VOWEL_C, CONS_C],
                                 labels=["VOWELS", "CONSONANTS"], radius=BIG_PIE_R,
                                 stroke_color=WHITE)
        self.pie.fan_all(self, 1.6)

    # c : the vowel/consonant position-frequency grid, titled like the letter views
    #     (the start/end/2nd-position stats are NARRATED, not captioned — see column 2)
    @subscene
    def freq(self):
        self.play(FadeOut(self.pie), run_time=0.5)
        self.pie = None
        self.view = vowel_consonant_heatmaps(center=[0.0, -0.4, 0])
        self.view_title = crisp_paragraph("Location", "Frequencies", font_size=30,
                                          color=WHITE, alignment="center")
        self.view_title.next_to(self.view, UP, buff=0.5)
        rows = [VGroup(lab, hm)
                for lab, hm in zip(self.view.labels, self.view.heatmaps)]
        self.play(FadeIn(self.view_title), self._rise(self.view, rows), run_time=1.2)

    # d : VOWEL (⅓ down) with before ← VOWEL → after adjacency pies
    @subscene
    def vowel_row(self):
        self.play(FadeOut(self.view), FadeOut(self.view_title), run_time=0.5)
        self.view = self.view_title = None
        self._adjacency_row("VOWEL", self.d["adjacency"]["vowel"], ROW_Y, VOWEL_C)

    # e : CONSONANT (⅔ down) with before ← CONSONANT → after adjacency pies
    @subscene
    def consonant_row(self):
        self._adjacency_row("CONSONANT", self.d["adjacency"]["consonant"], -ROW_Y, CONS_C)

    # f : remove the content FIRST, THEN turn the background back to light blue
    @subscene
    def to_light(self):
        content = [m for m in self.mobjects if m is not self.navy_rect]
        self.play(*[FadeOut(m) for m in content], run_time=0.6)
        self.play(FadeOut(self.navy_rect), run_time=0.6)

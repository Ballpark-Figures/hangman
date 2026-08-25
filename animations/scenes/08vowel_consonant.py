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
  f vc_bars        split each box red(vowel)|blue(consonant), coalesce into a red bar
                   then a blue bar per length; label avg #vowels (1dp, if fits) + #cons
  g vowel_row      VOWEL (⅓ down): before-pie ← VOWEL → after-pie (letters adjacent)
  h consonant_row  CONSONANT (⅔ down): before-pie ← CONSONANT → after-pie
  i to_light       clear + turn the background back to light blue

ROUGH first pass — LAYOUT + TIMING are guesses (the beat-c callout placement and the
pie sizes/positions especially). Judge from the video; tune freely.

Render:  render 08a --fast  (…08i)  /  render 08 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.chalkboard import BOARD_NAVY
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
        self.bars = None

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
                             inner_frac_spread=0.6, stroke_color=WHITE)

    def _build_adjacency_row(self, name, adj, y, word_color):
        """Build the pieces of an adjacency row (UNPLAYED): `name` (VOWEL red /
        CONSONANT blue) centred at height y, a before-pie to its LEFT and an after-pie
        to its RIGHT, each linked by a short line. Returns (word, line_l, line_r, before,
        after); the SUBSCENE plays them so the two pie fans stay SEPARATE steps — the
        'after' pie and the 'before' pie land on different sentences of the narration, so
        a wait can sit between them (see the g/h bodies)."""
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
        return word, line_l, line_r, before, after

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

    # e : the vowel/consonant position-frequency grid, titled like the letter views
    #     (the start/end/2nd-position stats are NARRATED, not captioned — see column 2)
    @subscene
    def freq(self):
        self.play(FadeOut(self.pie), run_time=0.5)
        self.pie = None
        self.view = vowel_consonant_heatmaps(center=[0.0, -0.4, 0])
        self.view_title = crisp_text("Position Frequencies", font_size=30,
                                     color=WHITE)
        self.view_title.next_to(self.view, UP, buff=0.5)
        rows = [VGroup(lab, hm)
                for lab, hm in zip(self.view.labels, self.view.heatmaps)]
        self.play(FadeIn(self.view_title), self._rise(self.view, rows), run_time=1.2)

    @staticmethod
    def _fmt(x):
        """One-decimal label, dropping a leading zero for values < 1 (".9" not "0.9")."""
        s = f"{x:.1f}"
        return s[1:] if s.startswith("0.") else s

    def _vc_title(self):
        """The bars' title 'Vowels/Consonants per Word' — Vowels red, Consonants blue,
        the rest white. Pieces share ONE text baseline (so 'per' hangs its descender
        correctly) and are laid out left-to-right by shifting in x only."""
        fs = 30
        spec = [("Vowels", VOWEL_C, 0.0), ("/", WHITE, 0.06),
                ("Consonants", CONS_C, 0.06), ("per Word", WHITE, 0.28)]
        pieces, x = [], 0.0
        for txt, col, gap in spec:
            m = crisp_text(txt, font_size=fs, color=col, baseline_at=(0, 0))
            m.shift(RIGHT * (x + gap - m.get_left()[0]))    # left edge at x+gap, baseline kept
            x = m.get_right()[0]
            pieces.append(m)
        return VGroup(*pieces)

    def _split_bars(self):
        """Overlay each freq CELL with a red (vowel) block on the left + blue
        (consonant) block on the right, sized by that position's vowel fraction; and
        compute each block's COALESCE target — reds packed to the row's left edge into
        one red bar, blues packed to the right into one blue bar, so the row's total
        width (= L cells) is unchanged. The little blocks are BORDERLESS (overlapping a
        hair so no hairline navy gaps show); once coalesced they're swapped for two
        clean MERGED bars per row (red then blue) that DO carry a white border. Returns
        (reds, blues, merged, num_labels): reds/blues are (block, target) pairs; merged
        the bordered final bars; num_labels the avg-#vowels/#consonants, centred on each
        merged bar (vowel kept only if it fits). Builds from the carried-in `self.view`
        geometry, so it lives here, not in setup."""
        grid = self.d["grid"]
        reds, blues, merged, num_labels = [], [], [], []
        EPS = 1e-3
        OV = 0.04          # widen each little block a hair so abutting blocks overlap
                           # (no hairline navy gaps); merged bars are single rects so
                           # they need no overlap — centres unchanged either way
        for i, L in enumerate(self.d["grid_lengths"]):
            # read geometry off the actual CELL squares, NOT hm's bbox: get_heatmap
            # returns VGroup(cells, values) with an EMPTY values group at the origin,
            # so hm.height / hm.get_center() are polluted by that origin point
            row_cells = self.view.heatmaps[i].cells[0]        # L squares, left->right
            cs = row_cells[0].width                           # cell size (== height)
            left = row_cells[0].get_left()[0]
            y = row_cells[0].get_center()[1]
            vf = grid[L]
            total_v = sum(vf)                   # == avg_vowels[L] (within rounding)
            red_w, blue_w = cs * total_v, cs * (L - total_v)
            boundary = left + red_w             # red bar ends / blue bar starts here
            red_acc = blue_acc = 0.0
            for p in range(L):
                v, c = vf[p], 1 - vf[p]
                cell_l = left + p * cs
                if v > EPS:
                    r = Rectangle(width=cs * v + OV, height=cs, fill_color=VOWEL_C,
                                  fill_opacity=1.0, stroke_width=0)
                    r.move_to([cell_l + cs * v / 2, y, 0])
                    reds.append((r, [left + cs * red_acc + cs * v / 2, y, 0]))
                    red_acc += v
                if c > EPS:
                    b = Rectangle(width=cs * c + OV, height=cs, fill_color=CONS_C,
                                  fill_opacity=1.0, stroke_width=0)
                    b.move_to([cell_l + cs * v + cs * c / 2, y, 0])
                    blues.append((b, [boundary + cs * blue_acc + cs * c / 2, y, 0]))
                    blue_acc += c
            # clean bordered bars the little blocks resolve into (one red, one blue)
            red_bar = Rectangle(width=red_w, height=cs, fill_color=VOWEL_C,
                                fill_opacity=1.0, stroke_color=WHITE, stroke_width=2.0)
            red_bar.move_to([left + red_w / 2, y, 0])
            blue_bar = Rectangle(width=blue_w, height=cs, fill_color=CONS_C,
                                 fill_opacity=1.0, stroke_color=WHITE, stroke_width=2.0)
            blue_bar.move_to([boundary + blue_w / 2, y, 0])
            merged += [red_bar, blue_bar]
            # labels centred on the actual bar mobjects (exact centring); a value < 1
            # drops its leading 0 (".9" not "0.9") so it fits the small box
            vt = crisp_text(self._fmt(self.d['avg_vowels'][L]), font_size=20,
                            color=WHITE)
            vt.move_to(red_bar)
            if vt.width < red_w - 0.08:                      # "if it fits" (script)
                num_labels.append(vt)
            ct = crisp_text(self._fmt(self.d['avg_consonants'][L]), font_size=20,
                            color=WHITE)
            ct.move_to(blue_bar)
            num_labels.append(ct)
        return reds, blues, merged, num_labels

    # f : split each box red|blue, coalesce into a red bar then a blue bar per length;
    #     label avg #vowels (1dp, if it fits) + avg #consonants (VO: "vowels and
    #     consonants per word")
    @subscene
    def vc_bars(self):
        reds, blues, merged, num_labels = self._split_bars()
        length_labels = self.view.labels                     # keep the length numbers
        split = VGroup(*[r for r, _ in reds], *[b for b, _ in blues])
        title = self._vc_title().move_to(self.view_title)     # replaces "Position Frequencies"
        # break each box up: the title cross-fades to "Vowels/Consonants per Word" as the
        # blended heatmap cells fade out and the red|blue split fades in over them
        self.play(FadeOut(self.view.heatmaps), FadeOut(self.view_title),
                  FadeIn(title), FadeIn(split), run_time=1.0)
        self.view = self.view_title = None
        # move the red blocks left, the blue blocks right, into one red then one blue bar
        self.play(*[r.animate.move_to(t) for r, t in reds],
                  *[b.animate.move_to(t) for b, t in blues], run_time=1.5)
        # resolve the little blocks into clean bordered bars: fade the (same-colour)
        # bordered bars in over the blocks so only the white borders appear, then drop
        # the now-hidden blocks
        bars = VGroup(*merged)
        self.play(FadeIn(bars), run_time=0.5)
        self.remove(split)
        nums = VGroup(*num_labels)
        self.play(FadeIn(nums), run_time=0.6)
        self.bars = VGroup(bars, nums, length_labels, title)

    # g : VOWEL (⅓ down) with before ← VOWEL → after adjacency pies
    #     (after pie = "followed by a consonant"; before pie = "preceded by a
    #      consonant" — separate sentences, so the fans are separate plays)
    @subscene
    def vowel_row(self):
        self.play(FadeOut(self.bars), run_time=0.5)
        self.bars = None
        word, line_l, line_r, before, after = self._build_adjacency_row(
            "VOWEL", self.d["adjacency"]["vowel"], ROW_Y, VOWEL_C)
        self.play(FadeIn(word), Create(line_l), Create(line_r), run_time=0.8)
        after.fan_all(self, 1.0)      # "...will be followed by a consonant"
        self.wait(4.0)
        before.fan_all(self, 1.0)     # "...will be preceded by a consonant"

    # h : CONSONANT (⅔ down) with before ← CONSONANT → after adjacency pies
    #     (after pie = "followed by vowels"; before pie = "preceded by vowels")
    @subscene
    def consonant_row(self):
        word, line_l, line_r, before, after = self._build_adjacency_row(
            "CONSONANT", self.d["adjacency"]["consonant"], -ROW_Y, CONS_C)
        self.play(FadeIn(word), Create(line_l), Create(line_r), run_time=0.8)
        after.fan_all(self, 1.0)      # "62% chance of being followed by vowels"
        self.wait(2.0)
        before.fan_all(self, 1.0)     # "61% chance of being preceded by vowels"

    # i : remove the content FIRST, THEN turn the background back to light blue
    @subscene
    def to_light(self):
        content = [m for m in self.mobjects if m is not self.navy_rect]
        self.play(*[FadeOut(m) for m in content], run_time=0.6)
        self.play(FadeOut(self.navy_rect), run_time=0.6)

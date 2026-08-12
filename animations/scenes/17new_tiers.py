"""SCENE 17 — re-weighting the tier list (frequency, then British English).

On the BRAND light-blue tier-list background. Four beats:
  a equal_bars   — all 49 length-2 words as bars in 3 rows, sorted by DESCENDING
                   frequency, ALL THE SAME height; titled "Word Frequency"
  b freq_bars    — morph the bar heights to each word's actual frequency (zipf)
  c freq_list    — clear the bars; the equal-weighted tier list on the LEFT
                   ("Equal Weighted Words") → arrow → the FREQUENCY-weighted list on the
                   RIGHT ("Frequency Weighted"; 6 tiers — the two HIGH tiers merge)
  d british_list — retitle to "American English" / "British English" and swap the right
                   list for the British one (A passes I in TOP; Z drops to LOW↓ bottom)

Numbers/orderings SOURCED: the 49 words + zipf from `assets/scene17_data` (the committed
cache); the three tier orderings from `assets/tier_list` (TIER_LETTERS /
FREQ_TIER_LETTERS / GB_TIER_LETTERS — hand-copied from letter_analysis.ipynb).

ROUGH first pass — LAYOUT + TIMING are guesses (bar sizes/rows, list scale, title
sizes). Judge from the video; tune freely.

Render:  render 17a --fast (…17d)  /  render 17 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets import scene17_data
from bpkfigures.bar_graph import get_bar_chart, morph_bar_chart

# ── bar graph (beats a/b) ─────────────────────────────────────────────────────
BAR_ROWS = 3
ROW_CYS = [2.05, 0.35, -1.35]     # the 3 bar-row baselines (title above, top → bottom)
BAR_ROW_W = 13.5                  # width of each bar row
BAR_ROW_H = 1.35                  # bar height at y_max
BAR_INK = BLACK                   # dark ink for the 2-letter labels (tier-list convention)

# ── tier lists (beats c/d) ────────────────────────────────────────────────────
LIST_SCALE = 0.62
LEFT_X, RIGHT_X = -3.45, 3.45
LIST_Y = -0.45
TITLE_Y = 2.75
TITLE_COLOR = BLACK               # tier-list world uses BLACK labels on the light bg


class Scene17(HangmanScene):
    """Re-weighting the tier list. See the module docstring for the beat map."""

    def setup_scene(self):
        self.words = scene17_data.get()["len2"]        # sorted DESC by frequency
        self.ymax = self.words[0]["freq"]              # tallest bar = the commonest word
        self.bar_rows = None
        self.title = None
        self.left = self.right = None
        self.left_title = self.right_title = None
        self.arrow = None

    # ── bar-graph helpers ─────────────────────────────────────────────────────
    def _row_slice(self, r):
        per = (len(self.words) + BAR_ROWS - 1) // BAR_ROWS       # ~17
        return self.words[r * per:(r + 1) * per]

    def _bar_row(self, r, values):
        """One bar row: a bar per word (label = the 2-letter word), heights `values`,
        a shared y_max so rows are comparable."""
        slice_ = self._row_slice(r)
        items = [(w["word"].upper(), v) for w, v in zip(slice_, values)]
        return get_bar_chart(items, center=[0, ROW_CYS[r], 0], width=BAR_ROW_W,
                             height=BAR_ROW_H, y_max=self.ymax, n_slots=self._per(),
                             bar_color=ACCENT_FILL, ink_color=BAR_INK, bar_ratio=0.7,
                             label_buff=0.14)

    def _per(self):
        return (len(self.words) + BAR_ROWS - 1) // BAR_ROWS

    def _equal_values(self, r):
        return [self.ymax] * len(self._row_slice(r))             # all the same height

    def _freq_values(self, r):
        return [w["freq"] for w in self._row_slice(r)]           # ACTUAL frequency (10**zipf)

    # ── tier-list helpers ─────────────────────────────────────────────────────
    def _filled_list(self, letters, *, names=None):
        """A tier list (default 7-tier named; `names` for a custom structure) with its
        `letters` filled in, scaled + ready to place."""
        t = tl.get_tier_list("name") if names is None else tl.get_tier_list(names=names)
        for i, lets in enumerate(letters):
            tl.fill_tier(t, i, lets)
        return t.scale(LIST_SCALE)

    def _title(self, text, x):
        return crisp_text(text, font_size=30, color=TITLE_COLOR,
                          weight=BOLD).move_to([x, TITLE_Y, 0])

    # ── beats ─────────────────────────────────────────────────────────────────
    # a : all 49 length-2 words as equal-height bars (3 rows, desc-freq order) + title
    @subscene
    def equal_bars(self):
        self.title = crisp_text("Word Frequency", font_size=40, color=TITLE_COLOR,
                                weight=BOLD).move_to([0, 3.55, 0])
        self.bar_rows = [self._bar_row(r, self._equal_values(r)) for r in range(BAR_ROWS)]
        self.play(FadeIn(self.title), run_time=0.6)
        self.play(*[FadeIn(row) for row in self.bar_rows], run_time=1.0)

    # b : morph the bar heights to each word's actual frequency (zipf)
    @subscene
    def freq_bars(self):
        anims, new_rows = [], []
        for r in range(BAR_ROWS):
            new = self._bar_row(r, self._freq_values(r))
            anims += morph_bar_chart(self.bar_rows[r], new)
            new_rows.append(new)
        self.play(*anims, run_time=1.4)
        self.bar_rows = new_rows

    # c : clear the bars; equal-weighted list (left) → arrow → frequency-weighted (right)
    @subscene
    def freq_list(self):
        self.play(FadeOut(self.title), *[FadeOut(r) for r in self.bar_rows], run_time=0.6)
        self.title = self.bar_rows = None
        self.left = self._filled_list(tl.TIER_LETTERS).move_to([LEFT_X, LIST_Y, 0])
        self.right = self._filled_list(tl.FREQ_TIER_LETTERS,
                                       names=tl.FREQ_NAME_LABELS).move_to([RIGHT_X, LIST_Y, 0])
        self.left_title = self._title("Equal Weighted Words", LEFT_X)
        self.right_title = self._title("Frequency Weighted", RIGHT_X)
        self.arrow = Arrow([-1.05, LIST_Y, 0], [1.05, LIST_Y, 0], buff=0.0,
                           color=TITLE_COLOR, stroke_width=6)
        self.play(FadeIn(self.left, self.left_title), run_time=0.8)
        self.play(GrowArrow(self.arrow), run_time=0.5)
        self.play(FadeIn(self.right, self.right_title), run_time=0.8)

    # d : retitle American/British; swap the right list for the British tier list
    @subscene
    def british_list(self):
        brit = self._filled_list(tl.GB_TIER_LETTERS).move_to([RIGHT_X, LIST_Y, 0])
        self.play(Transform(self.left_title, self._title("American English", LEFT_X)),
                  Transform(self.right_title, self._title("British English", RIGHT_X)),
                  run_time=0.7)
        self.play(FadeOut(self.right), FadeIn(brit), run_time=0.8)
        self.right = brit

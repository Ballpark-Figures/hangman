"""SCRATCH / analysis — the letter view stepped through the WHOLE alphabet.

One subscene per letter, A..Z (so `render 96a` = A … `render 96z` = Z). Each shows:
  • the letter grid tucked top-left, the chosen letter big at bottom-left,
  • "Location Frequencies": the length-2..10 position heatmaps (middle),
  • "Top ngrams": the top-5 bigrams + top-5 trigrams, letter-centered (right).
The grid enters + chooses A on the first beat; every later beat swaps to the next
letter and refreshes the heatmaps + ngrams. Titles are persistent.

Render:  render 96 sub   (whole alphabet)   /   render 96e --fast   (just 'E')
"""
from pathlib import Path
import string
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.letter_grid import letter_grid
from assets.letter_heatmaps import letter_heatmaps
from assets.letter_ngrams import letter_ngrams

LETTERS = string.ascii_uppercase

HEAT_CENTER  = np.array([0.2, -0.4, 0.0])      # heatmap stack center (middle)
LOC_TITLE    = np.array([0.2, 3.2, 0.0])       # "Location Frequencies" (2 lines)
NG_TITLE     = np.array([5.3, 3.2, 0.0])       # "Top N-grams" (2 lines, same y)
NG_TOP       = np.array([5.3, 1.9, 0.0])       # anchored-letter column, top row


class LetterGridTest(HangmanScene):

    def _two_line(self, l1, l2, center):
        # crisp_paragraph spaces lines by font metrics (descender-independent), so
        # both titles get identical leading regardless of which letters descend.
        return crisp_paragraph(l1, l2, font_size=30, color=BLACK,
                               alignment="center").move_to(center)

    def _show(self, idx):
        lc = LETTERS[idx].lower()
        heat = letter_heatmaps(lc, center=HEAT_CENTER)
        ngrams = letter_ngrams(lc, top_center=NG_TOP)
        if idx == 0:
            # enter + ENLARGE first; the titles + first panels appear only after,
            # each title alongside its own content.
            self.grid = letter_grid()
            self.grid.to_edge(LEFT, buff=0.8).set_y(0)
            self.grid.slide_in(self, run_time=1.0)
            self.grid.choose(self, LETTERS[idx], run_time=1.1)
            self.loc_title = self._two_line("Location", "Frequencies", LOC_TITLE)
            self.ng_title = self._two_line("Top", "N-grams", NG_TITLE)
            self.play(FadeIn(self.loc_title), FadeIn(heat), run_time=0.6)
            self.play(FadeIn(self.ng_title), FadeIn(ngrams), run_time=0.5)
        else:
            # switch letters: the grid swaps while the heatmaps TRANSITION in place
            # to the new letter (same grid of cells, recoloured); ngrams cross-fade
            # (their structure differs letter to letter). Titles persist.
            ret, pick, _ = self.grid.swap(self, LETTERS[idx], play=False)
            self.play(ret, pick, ReplacementTransform(self.heat, heat),
                      FadeOut(self.ngrams), run_time=1.0)
            self.play(FadeIn(ngrams), run_time=0.4)
        self.heat = heat
        self.ngrams = ngrams

    # one @subscene per letter, in order → render 96a..96z map to A..Z. (Explicit
    # methods, not a setattr loop, so the render tooling's AST scan finds them.)
    @subscene
    def a(self): self._show(0)
    @subscene
    def b(self): self._show(1)
    @subscene
    def c(self): self._show(2)
    @subscene
    def d(self): self._show(3)
    @subscene
    def e(self): self._show(4)
    @subscene
    def f(self): self._show(5)
    @subscene
    def g(self): self._show(6)
    @subscene
    def h(self): self._show(7)
    @subscene
    def i(self): self._show(8)
    @subscene
    def j(self): self._show(9)
    @subscene
    def k(self): self._show(10)
    @subscene
    def l(self): self._show(11)
    @subscene
    def m(self): self._show(12)
    @subscene
    def n(self): self._show(13)
    @subscene
    def o(self): self._show(14)
    @subscene
    def p(self): self._show(15)
    @subscene
    def q(self): self._show(16)
    @subscene
    def r(self): self._show(17)
    @subscene
    def s(self): self._show(18)
    @subscene
    def t(self): self._show(19)
    @subscene
    def u(self): self._show(20)
    @subscene
    def v(self): self._show(21)
    @subscene
    def w(self): self._show(22)
    @subscene
    def x(self): self._show(23)
    @subscene
    def y(self): self._show(24)
    @subscene
    def z(self): self._show(25)

    # za : close — put Z back and clear the heatmap + N-gram views (grid → home)
    @subscene
    def close(self):
        self.play(FadeOut(self.heat), FadeOut(self.ngrams),
                  FadeOut(self.loc_title), FadeOut(self.ng_title), run_time=0.5)
        self.grid.restore(self, run_time=1.0)

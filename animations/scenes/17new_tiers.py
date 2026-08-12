"""SCENE 17 — re-weighting the tier list (frequency, then British English).

On the BRAND light-blue tier-list background. Four beats:
  a equal_bars   — the top 30 five-letter words (bold) as bars in 3 rows, sorted by
                   DESCENDING frequency, ALL THE SAME height; titled "Word Frequency"
  b freq_bars    — morph the bar heights to each word's actual frequency (10**zipf)
  c freq_list    — clear the bars; the equal-weighted list (left, "Equal Weighted
                   Words"); a COPY morphs into the FREQUENCY-weighted list (right,
                   "Frequency Weighted"; 6 tiers — the two HIGH tiers merge); arrow AFTER
  d strategy_chart — double bar chart: the optimal strategy's avg misses per word length,
                   EQUAL (uniform) vs FREQUENCY (zipf) weighting — frequency is lower
                   everywhere. Sourced from scene17_chart_data (exact where converged, avg
                   of lower/upper bounds where not).
  e brit_list    — repeat the comparison, American (left) → copy morphs into British
                   (right); A↔I in TOP, Z→bottom of LOW↓; arrow AFTER
  f enc_spelling — below the lists: ENCYCLOPEDIA → ENCYCLOPAEDIA (why A gains in British)
  g realize_spelling — below that: REALIZE → REALISE (why Z drops in British)

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
from assets import scene17_chart_data
from bpkfigures.bar_graph import get_bar_chart, morph_bar_chart, grow_bars

# beat-d double bar chart (optimal misses, uniform vs zipf)
UNIFORM_COLOR = ACCENT_FILL        # equal-weighted bars
ZIPF_COLOR = CRIMSON               # frequency-weighted bars

# ── bar graph (beats a/b) ─────────────────────────────────────────────────────
BAR_ROWS = 3
ROW_CYS = [2.05, -0.15, -2.35]    # the 3 bar-row BASELINES (bars grow UP from here)
BAR_ROW_W = 13.5                  # width of each bar row
BAR_ROW_H = 1.55                  # bar height at y_max (a full bar clears the row above)
BAR_INK = BLACK                   # dark ink for the 2-letter labels (tier-list convention)

# ── tier lists (beats c/d) ────────────────────────────────────────────────────
LIST_SCALE = 0.62
LEFT_X, RIGHT_X = -3.45, 3.45
LIST_Y = -0.15
TITLE_Y = 2.9
TITLE_COLOR = BLACK               # tier-list world uses BLACK labels on the light bg
SPELL_Y = [-2.9, -3.55]           # the two spelling-example lines below the lists (f/g)


class Scene17(HangmanScene):
    """Re-weighting the tier list. See the module docstring for the beat map."""

    def setup_scene(self):
        self.words = scene17_data.get()["words"]       # top 30 5-letter, DESC by frequency
        self.ymax = self.words[0]["freq"]              # tallest bar = the commonest word
        self.bar_rows = None
        self.title = None
        self.left = self.right = None
        self.left_title = self.right_title = None
        self.arrow = None
        self.chart = None
        self.enc = self.realize = None

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
                             bar_color=ACCENT_FILL, bar_ratio=0.7, label_buff=0.16,
                             label_factory=lambda s: crisp_text(s, font_size=22,
                                                                color=BAR_INK, weight=BOLD))

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

    def _spell_pair(self, us, gb, y):
        """A spelling example at height y, laid out to MIRROR the tier lists: the US word
        RIGHT-aligned under the left (American) list, the GB word LEFT-aligned under the
        right (British) list, with an arrow IDENTICAL to the one between the lists."""
        left = crisp_text(us, font_size=26, color=TITLE_COLOR, weight=BOLD)
        left.move_to([self.left.get_right()[0], y, 0], aligned_edge=RIGHT)
        right = crisp_text(gb, font_size=26, color=TITLE_COLOR, weight=BOLD)
        right.move_to([self.right.get_left()[0], y, 0], aligned_edge=LEFT)
        arrow = Arrow([-1.05, y, 0], [1.05, y, 0], buff=0.0, color=TITLE_COLOR,
                      stroke_width=6)                          # == the tier-list arrow
        return VGroup(left, arrow, right)

    def _morph_into(self, src, dst, src_letters, dst_letters, row_map, run_time, *,
                    extra=()):
        """Transform a COPY of tier list `src` into `dst`: per-role structure
        (cell/panel/label of src row i → dst row `row_map[i]`, so two rows can MERGE
        onto one) + per-LETTER moves (each letter slides to its dst tile). `src` stays
        put; `dst` is left on screen at the end. `extra` plays ALONGSIDE (e.g. the right
        title fading in as the list moves). Piece-by-piece (role handles), never a blob
        morph — see bpkfigures CLAUDE.md."""
        dst_tile = {ch: dst.contents[i][k]
                    for i, lets in enumerate(dst_letters) for k, ch in enumerate(lets)}
        pairs = []
        for i, j in enumerate(row_map):
            pairs += [(src.cells[i], dst.cells[j]), (src.panels[i], dst.panels[j]),
                      (src.labels[i], dst.labels[j])]
        for i, lets in enumerate(src_letters):
            for k, ch in enumerate(lets):
                pairs.append((src.contents[i][k], dst_tile[ch]))
        movers = [a.copy() for a, _ in pairs]
        for m in movers:
            self.add(m)
        self.play(*[Transform(m, b.copy()) for m, (_, b) in zip(movers, pairs)],
                  *extra, run_time=run_time)
        self.remove(*movers)
        self.add(dst)

    # ── beats ─────────────────────────────────────────────────────────────────
    # a : all 49 length-2 words as equal-height bars (3 rows, desc-freq order) + title
    @subscene
    def equal_bars(self):
        self.title = crisp_text("Word Frequency", font_size=40, color=TITLE_COLOR,
                                weight=BOLD).move_to([0, 3.55, 0])
        self.play(FadeIn(self.title), run_time=0.6)
        self.bar_rows = [self._bar_row(r, self._equal_values(r)) for r in range(BAR_ROWS)]
        labels = VGroup(*[row.labels for row in self.bar_rows]).set_opacity(0)
        self.add(*self.bar_rows)          # grow_bars collapses the bars next → no flash
        bars = [b for row in self.bar_rows for b in row.bars]
        grow_bars(self, bars, 1.3, lag=0.04, extra=[labels.animate.set_opacity(1)])

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

    # c : equal-weighted list (left); a copy MORPHS into the frequency-weighted list
    #     (right) — the two HIGH tiers merge, letters slide to new tiers — THEN the arrow
    @subscene
    def freq_list(self):
        self.play(FadeOut(self.title), *[FadeOut(r) for r in self.bar_rows], run_time=0.6)
        self.title = self.bar_rows = None
        self.left = self._filled_list(tl.TIER_LETTERS).move_to([LEFT_X, LIST_Y, 0])
        self.left_title = self._title("Equal Weighted Words", LEFT_X)
        self.play(FadeIn(self.left, self.left_title), run_time=0.8)
        # a copy of the left list slides right and re-forms as the frequency list,
        # the right title fading in AS it moves
        self.right = self._filled_list(tl.FREQ_TIER_LETTERS,
                                       names=tl.FREQ_NAME_LABELS).move_to([RIGHT_X, LIST_Y, 0])
        self.right_title = self._title("Frequency Weighted", RIGHT_X)
        self._morph_into(self.left, self.right, tl.TIER_LETTERS, tl.FREQ_TIER_LETTERS,
                         [0, 1, 1, 2, 3, 4, 5], 2.0,                 # HIGH↑,HIGH↓ → HIGH
                         extra=[FadeIn(self.right_title)])
        self.arrow = Arrow([-1.05, LIST_Y, 0], [1.05, LIST_Y, 0], buff=0.0,
                           color=TITLE_COLOR, stroke_width=6)
        self.play(GrowArrow(self.arrow), run_time=0.5)               # arrow drawn AFTER

    # d : double bar chart — the OPTIMAL strategy's avg misses per word length, EQUAL
    #     (uniform) vs FREQUENCY (zipf) weighting; frequency is lower everywhere
    def _legend(self, entries, pos):
        g = VGroup()
        for name, color in entries:
            sq = Square(side_length=0.28, fill_color=color, fill_opacity=1.0,
                        stroke_width=0)
            g.add(VGroup(sq, crisp_text(name, font_size=22,
                                        color=TITLE_COLOR)).arrange(RIGHT, buff=0.18))
        return g.arrange(DOWN, buff=0.22, aligned_edge=LEFT).move_to(pos)

    def _strategy_chart(self):
        data = scene17_chart_data.get()
        lengths = sorted(int(L) for L in data["uniform"])
        ymax = max(data[w][str(L)]["avg"] for w in ("uniform", "zipf") for L in lengths)
        W, cy, H = 12.6, -0.55, 3.8
        N, slot = len(lengths), 12.6 / len(lengths)
        dx = slot / 4.2                                     # half-gap between the paired bars

        def series(w, color, off):
            items = [(str(L), data[w][str(L)]["avg"]) for L in lengths]
            return get_bar_chart(items, center=[off, cy, 0], width=W, height=H,
                                 y_max=ymax, n_slots=N, bar_color=color, bar_ratio=0.42,
                                 show_labels=False)

        uni, zipc = series("uniform", UNIFORM_COLOR, -dx), series("zipf", ZIPF_COLOR, dx)
        base_y = cy - H / 2
        xlabels = VGroup(*[crisp_text(str(L), font_size=20, color=TITLE_COLOR).move_to(
                              [-W / 2 + (i + 0.5) * slot, base_y - 0.28, 0])
                           for i, L in enumerate(lengths)])
        xtitle = crisp_text("word length", font_size=24, color=TITLE_COLOR).move_to(
            [0, base_y - 0.78, 0])
        title = crisp_text("Optimal Misses per Word", font_size=34, color=TITLE_COLOR,
                           weight=BOLD).move_to([0, cy + H / 2 + 0.7, 0])
        legend = self._legend([("Equal", UNIFORM_COLOR), ("Frequency", ZIPF_COLOR)],
                              [4.9, cy + H / 2 - 0.2, 0])
        return VGroup(uni, zipc, xlabels, xtitle, title, legend)

    @subscene
    def strategy_chart(self):
        self.play(FadeOut(self.left, self.left_title, self.right, self.right_title,
                          self.arrow), run_time=0.6)
        self.left = self.right = self.left_title = self.right_title = self.arrow = None
        self.chart = self._strategy_chart()
        bars = [*self.chart[0].bars, *self.chart[1].bars]     # uniform + zipf series
        rest = VGroup(*self.chart[2:]).set_opacity(0)         # axis labels, title, legend
        self.add(self.chart)                                  # grow_bars collapses bars next
        grow_bars(self, bars, 1.1, lag=0.02, extra=[rest.animate.set_opacity(1)])

    # e : repeat the comparison — American (left); a copy MORPHS into British (right);
    #     same 7 tiers, A↔I swap in TOP and Z→bottom in LOW↓; arrow drawn AFTER
    @subscene
    def brit_list(self):
        self.play(FadeOut(self.chart), run_time=0.5)          # clear the beat-d chart
        self.chart = None
        self.left = self._filled_list(tl.TIER_LETTERS).move_to([LEFT_X, LIST_Y, 0])
        self.left_title = self._title("American English", LEFT_X)
        self.play(FadeIn(self.left, self.left_title), run_time=0.8)
        self.right = self._filled_list(tl.GB_TIER_LETTERS).move_to([RIGHT_X, LIST_Y, 0])
        self.right_title = self._title("British English", RIGHT_X)
        self._morph_into(self.left, self.right, tl.TIER_LETTERS, tl.GB_TIER_LETTERS,
                         [0, 1, 2, 3, 4, 5, 6], 2.0,             # same 7 tiers
                         extra=[FadeIn(self.right_title)])       # title in AS it moves
        self.arrow = Arrow([-1.05, LIST_Y, 0], [1.05, LIST_Y, 0], buff=0.0,
                           color=TITLE_COLOR, stroke_width=6)
        self.play(GrowArrow(self.arrow), run_time=0.5)

    # f : below the lists — ENCYCLOPEDIA → ENCYCLOPAEDIA (why A gains in British)
    def _play_spell(self, pair):
        """Reveal a spelling pair in order: first word → growing arrow → second word."""
        left, arrow, right = pair
        self.play(FadeIn(left), run_time=0.4)
        self.play(GrowArrow(arrow), run_time=0.4)
        self.play(FadeIn(right), run_time=0.4)

    @subscene
    def enc_spelling(self):
        self.enc = self._spell_pair("ENCYCLOPEDIA", "ENCYCLOPAEDIA", SPELL_Y[0])
        self._play_spell(self.enc)

    # g : below that — REALIZE → REALISE (why Z drops in British)
    @subscene
    def realize_spelling(self):
        self.realize = self._spell_pair("REALIZE", "REALISE", SPELL_Y[1])
        self._play_spell(self.realize)

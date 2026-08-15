"""SCENE 21 — why ING-reduction works: longer words reduce to shorter ones.

Follows scene 20 (a brand-bg table scene). The chalkboard FADES back in (beat a),
recaps the optimal-misses-per-length graph (beat b), then a 7-blank reduction demo
(c/d: guess I·N·G into the last 3 blanks → a 7-letter word is now a 4-letter prefix
+ ING), two walls of words comparing the 4- and 7-letter lists (e/f), and finally
the GAINING game played out (h) to show why the strategy avoids words with an EXTRA
I/N/G (the guesser starts with ING, so extras leak the answer).

Everything on the chalkboard is CHALK (chalk_letter/chalk_phrase strokes, the
line-outline bar chart), per the video's chalkboard convention.

Script row 21 splits on '—' → 8 beats, one @subscene each (a–h). See the beat map.

SOURCED DATA
  • beat b graph = OPTIMAL avg misses per length, UNIFORM weighting — reuses the
    existing committed cache `scene17_chart_cache.json`
    (`scene17_chart_data.get()["uniform"]`); NOT recomputed here.
  • beats e/f word walls + the VO word counts = `assets/scene21_data.py`
    (committed `scene21_cache.json`), read from `math/wordlist.py` (cutoff zipf≥2.5):
      words4 = FIRST 99 4-letter words BY FREQUENCY   — LEFT wall (+ a "…" cell → 100)
      words7 = FIRST 279 7-letter words BY FREQUENCY  — RIGHT wall (+ a "…" cell → 280)
      counts = {len4: 2120, len7: 5541, len7_ing: 658} — the VO's three ___ blanks
    The walls are the MOST COMMON words (a natural alphabet spread); the counts are
    the true totals, SPOKEN in the VO only (NOT rendered). Of the 279 shown 7-letter
    words, 42 end in -ING (survive beat f); the "…" cell STAYS too (both walls keep
    their "…" to hint the lists run on).

FLAGS (confirm)
  • beat b: chart TITLE matches the CHALKBOARD chart (scene 04 `_avg_chart` /
    scene 05 recap) = "Average Misses by Word Length". DATA is the OPTIMAL uniform
    series (scene17 cache), per the script's "optimal misses" wording (user chose
    optimal over greedy — scene 04's chalkboard chart itself uses greedy data).
  • beat h GAINING guess order = I·N·G then A — the ILLUSTRATIVE "start with ING"
    order the VO prescribes (all hits, 0 misses), NOT a solver trace. It ends on the
    fully-revealed white board (no green win / no fade) — the script names neither.
    If scene 22 is animated (not a talking head), beat h likely needs a fade-out.

BEAT MAP
  a bring_board     — the chalkboard fades back in
  b chart           — chalk line-outline graph: optimal misses per word length
  c blanks_gallows  — erase the chart; draw 7 word blanks + the gallows
  d guess_ing       — guess I, N, G → written into the LAST 3 blanks (the reduction)
  e word_walls      — clear the demo; LEFT = 100 4-letter (99+…), RIGHT = 280 7-letter (279+…), by freq
  f erase_nonings   — fade the right-wall words NOT ending in ING (only -ING survive)
  g erase_all       — erase the board (both walls)
  h gaining         — play GAINING out: I·N·G·A, all hits (extras give it away)

Render:  render 21a --fast   (…21h)   /   render 21 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import get_bar_chart
from bpkfigures.chalkboard import chalkboard, chalk_letter, chalk_phrase, chalk_number, CHALK
from assets import game_board as gb
from assets import scene21_data
from assets import scene17_chart_data

CHART_COLOR = LIGHT_BLUE            # light palette — reads on the navy slate

# ── the reduction demo + the GAINING game (7-letter boards) ────────────────────
WORD_G = "gaining"                  # beat h — the played-out example
ING_POS = [4, 5, 6]                 # beat d — I·N·G go into the LAST 3 of 7 blanks
GAINING_GUESSES = ["i", "n", "g", "a"]   # start with ING (VO), then the leftover A


class Scene21(HangmanScene):
    """Chalkboard recap → reduction demo → word walls → GAINING game.
    See the module docstring for the full beat map, sourcing, and flags."""

    # nothing on screen from frame 0 (continues from scene 20's brand bg)
    def setup_scene(self):
        pass

    # ── a : the chalkboard fades back in ──────────────────────────────────────
    def _setup_board(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)

    @subscene
    def bring_board(self):
        self._setup_board()
        self.play(FadeIn(self.cb), run_time=0.8)

    # ── b : chalk line-outline graph — optimal misses per word length ─────────
    def _setup_chart(self):
        uni = scene17_chart_data.get()["uniform"]
        lengths = sorted(int(k) for k in uni)
        items = [(L, uni[str(L)]["avg"]) for L in lengths]
        chart = get_bar_chart(
            items, center=[0, 0, 0], width=12.0, height=4.2, y_max=7,
            bar_color=CHART_COLOR, ink_color=CHALK, bar_ratio=0.75,
            bar_stroke_width=4, bar_outline="open",   # 3-sided (x-axis is the base)
            label_factory=lambda L: chalk_number(L, height=0.24), label_buff=0.20,
            x_axis=True, y_axis=True,
            y_ticks=range(0, 8, 2),
            y_tick_factory=lambda t: chalk_number(t, height=0.22),
            # title matches the CHALKBOARD chart (scene 04's `_avg_chart`, recapped
            # in scene 05) — no separate x-axis title, as there
            title_mobject=chalk_phrase("Average Misses by Word Length", height=0.38),
            title_buff=0.5,
        )
        chart.shift([0, -chart.get_center()[1], 0])       # centre vertically
        chart.axes = VGroup(chart.x_axis, chart.y_axis)
        self.chart = chart

    @subscene
    def chart(self):
        self._setup_chart()
        self.play(FadeIn(self.chart.axes), FadeIn(self.chart.labels),
                  FadeIn(self.chart.yticks), FadeIn(self.chart.title),
                  *[Create(b) for b in self.chart.bars], run_time=1.8)

    # ── c : erase the chart; draw 7 blanks + the gallows ──────────────────────
    def _setup_game7(self):
        self.rules7 = gb.build_rules(7)
        self.hang7, self.hang7_parts = gb.build_gallows()
        self.rev7 = VGroup()                              # the I·N·G written on

    @subscene
    def blanks_gallows(self):
        self._setup_game7()
        self.play(FadeOut(self.chart), run_time=0.5)
        self.chart = None
        self.play(LaggedStartMap(Create, self.rules7, lag_ratio=1.0), run_time=2.0)
        self.play(LaggedStartMap(Create, self.hang7.gallows, lag_ratio=0.6),
                  run_time=1.6)

    # ── d : guess I, N, G → written into the LAST 3 blanks (the reduction) ─────
    @subscene
    def guess_ing(self):
        # one continuous beat: bubble-then-write each of I·N·G into its blank (all
        # hits — a generic 7-blank board, so no underlying word / no misses)
        for ch, pos in zip("ing", ING_POS):
            bub = gb.bubble(ch, tail="left")
            self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.7)
            L = gb.reveal_letter(ch, self.rules7[pos])
            self.rev7.add(L)
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.9)
            self.play(FadeOut(bub), run_time=0.4)

    # ── e : clear the demo; LEFT = 100 4-letter words, RIGHT = 500 7-letter ────
    def _word_wall(self, words, *, cols, region_w, region_h, cx, cy):
        """A dense block of monospaced chalk words, `cols` columns, scaled to fit
        region_w×region_h and centred at (cx, cy). Submobject i == words[i]."""
        cell_w = 0.30
        rows = VGroup()
        for w in words:
            row = VGroup(*[
                chalk_letter(ch, height=0.30, stroke_width=2.0, color=CHALK)
                .move_to([j * cell_w, 0, 0])
                for j, ch in enumerate(w)])
            rows.add(row)
        rows.arrange_in_grid(cols=cols, buff=(0.5, 0.22), aligned_edge=LEFT)
        rows.scale(min(region_w / rows.width, region_h / rows.height, 1.0))
        rows.move_to([cx, cy, 0])
        return rows

    def _setup_walls(self):
        d = scene21_data.get()
        w4 = d["words4"] + ["..."]                 # "…" last cell → 100 (5×20)
        w7 = d["words7"] + ["..."]                 # "…" last cell → 280 (7×40)
        self.wall4 = self._word_wall(w4, cols=5,
                                     region_w=6.4, region_h=7.4, cx=-3.9, cy=0)
        # build the 7-letter grid, then split its rows into the -ING survivors
        # (keep — plus the "…" cell, which stays to hint the -ING list also runs on)
        # and the rest (drop) as SEPARATE top-level groups. Beat f removes `drop`
        # cleanly; beat g fades only `keep`. Fading a SUBSET of one tracked container
        # (the old approach) let the dropped rows reappear at g's fade — so keep/drop
        # are distinct mobjects from the start.
        wall7 = self._word_wall(w7, cols=7,
                                region_w=7.0, region_h=7.6, cx=3.6, cy=0)
        keep = lambda w: w.endswith("ing") or w == "..."
        self.wall7_keep = VGroup(*[r for r, w in zip(wall7, w7) if keep(w)])
        self.wall7_drop = VGroup(*[r for r, w in zip(wall7, w7) if not keep(w)])

    @subscene
    def word_walls(self):
        self._setup_walls()
        # clear the 7-blank reduction demo, then the two word walls FADE in (bulk
        # reference lists, so FadeIn as groups — not chalked stroke-by-stroke)
        self.play(FadeOut(self.rules7), FadeOut(self.hang7), FadeOut(self.rev7),
                  run_time=0.6)
        self.rules7 = self.hang7 = self.hang7_parts = self.rev7 = None
        self.play(FadeIn(self.wall4), FadeIn(self.wall7_keep),
                  FadeIn(self.wall7_drop), run_time=1.2)

    # ── f : fade the right-wall words NOT ending in ING (only -ING survive) ────
    @subscene
    def erase_nonings(self):
        self.play(FadeOut(self.wall7_drop), run_time=1.5)
        self.wall7_drop = None

    # ── g : erase the board (both walls) ──────────────────────────────────────
    @subscene
    def erase_all(self):
        self.play(FadeOut(self.wall4), FadeOut(self.wall7_keep), run_time=0.8)
        self.wall4 = self.wall7_keep = None

    # ── h : play GAINING out — I·N·G·A, all hits (extras give the word away) ───
    def _setup_gaining(self):
        self.rulesG = gb.build_rules(len(WORD_G))
        self.hangG, self.hangG_parts = gb.build_gallows()
        self.revG = VGroup()

    @subscene
    def gaining(self):
        self._setup_gaining()
        self.play(LaggedStartMap(Create, self.rulesG, lag_ratio=1.0), run_time=2.0)
        self.play(LaggedStartMap(Create, self.hangG.gallows, lag_ratio=0.6),
                  run_time=1.6)
        # start with ING (as the strategy guarantees), then the leftover A — all hits
        for g in GAINING_GUESSES:
            positions = [p for p, c in enumerate(WORD_G) if c == g]
            bub = gb.bubble(g, tail="left")
            self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.7)
            for p in positions:                           # LEFT → RIGHT, one at a time
                L = gb.reveal_letter(g, self.rulesG[p])
                self.revG.add(L)
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.9)
            self.play(FadeOut(bub), run_time=0.4)

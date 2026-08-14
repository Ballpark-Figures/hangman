"""SCENE 22 — better guessing: the tier list under the improved CHOOSING strategy.

Opens with a brief CHALKBOARD callback (beat a: guess I·N·G into the last 3 of 7
blanks — the guaranteed -ING start), then the board is REMOVED and the rest of the
scene lives in the brand tier-list world:
  • two stacked "misses by starting letter" bar charts (b uniform / c best_opener,
    length 5, greedy guesser) — the same chart under the two word-choice strategies,
  • the original tier list morphing into the best_opener one (d), with the moved
    letters emphasised (e: I·N·G up, f: S·R down), then cleared (g).

Script row 22 splits on '—' → 7 beats, one @subscene each (a–g).

SOURCED DATA
  • beats b/c bar values = `assets/scene22_data.py` (committed `scene22_cache.json`):
    the greedy guesser's avg misses per FORCED opener at length 5, uniform and
    best_opener, from `strategy_view … misses_by_starting_letter()` — SORTED best-first
    (the "gradually more guesses" ramp). `best` (leftmost = true minimum) is highlighted.
    NOTHING computed at render.
  • best_opener tier ordering = `tier_list.BEST_OPENER_TIER_LETTERS`, hand-copied from
    letter_analysis `greedy_min_pairs()` (optimal / best_opener). See tier_list.py.

REUSE MAP (element → shared source)
  • chalkboard + blanks + gallows + I·N·G guess (beat a) → `assets/game_board` (gb):
    `build_rules` / `build_gallows` / `bubble` / `reveal_letter` + `chalkboard`
    (same as scene 21's reduction demo — bubble-then-write each hit).
  • bar charts (b/c) → `bpkfigures.bar_graph.get_bar_chart` (new `y_min` zoomed axis) +
    `grow_bars` entrance; ACCENT_FILL bars, ACCENT_GOLD best bar, BLACK ink (brand bg).
  • tier lists + morph (d) → `tier_list.filled_list` + `tier_list.morph_into` (the shared
    scene-17 comparison), `BEST_OPENER_TIER_LETTERS`; arrow == scene 17's.
  • emphasis (e/f) → dim the OTHER tiles (house "dim the rest"), `tier_list.tile_map`
    to find each letter's tile in both lists.

FLAGS (confirm)
  • No chart TITLES / axis titles and no tier-list TITLES — column 2 names none, so per
    the sparse-text rule they're omitted (the VO + the arrow + the differing y-ranges
    carry uniform-vs-best_opener and original-vs-improved). Say the word if you want
    labels ("Uniform" / "Improved", or "Original" → "Improved").
  • Emphasis (e/f) is opacity-only (dim the rest); the moved letters stay their vowel/
    consonant colour. Can add a gold tint if you want them to pop harder.
  • y-axis ranges from the script: b [3.9, 5.1] ticks 4/4.5/5; c [5.25, 6.5] ticks
    5.5/6/6.5 (data b [4.00,4.96], c [5.38,6.36] — no clipping).

BEAT MAP
  a ing_board   — chalkboard: 7 blanks + gallows; guess I·N·G into the last 3 blanks
  b uniform_bar — remove the board; TOP-half bar chart, misses by opener (uniform)
  c bestop_bar  — BOTTOM-half bar chart, misses by opener (best_opener) — same chart
  d tier_morph  — original tier list → arrow → the best_opener tier list (both stay)
  e emph_ing    — emphasise I·N·G on both lists (they move UP)
  f emph_sr     — emphasise S·R on both lists (they move DOWN)
  g clear       — fade both tier lists out

Render:  render 22a --fast   (…22g)   /   render 22 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.bar_graph import get_bar_chart, grow_bars
from assets.chalkboard import chalkboard, CHALK
from assets import game_board as gb
from assets import tier_list as tl
from assets import scene22_data

# ── beat a : the chalkboard reduction callback ────────────────────────────────
ING_POS = [4, 5, 6]                 # I·N·G go into the LAST 3 of 7 blanks (the -ING end)

# ── beats b/c : the two stacked bar charts (brand bg, crisp filled bars) ───────
CHART_W = 13.0
CHART_H = 2.4
TOP_CY, BOT_CY = 2.35, -2.35        # top-half (uniform) / bottom-half (best_opener)
BAR_INK = BLACK                     # brand-bg tier world uses black labels

# ── beats d–g : the tier-list comparison ──────────────────────────────────────
LIST_SCALE = 0.62
LEFT_X, RIGHT_X = -3.45, 3.45
LIST_Y = 0.0


class Scene22(HangmanScene):
    """Better guessing — the tier list under the improved choosing strategy.
    See the module docstring for the beat map, sourcing, reuse map, and flags."""

    # the chalkboard is on screen from frame 0 ("start with chalkboard on screen")
    def setup_scene(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)
        self.rules7 = self.hang7 = self.hang7_parts = self.rev7 = None
        self.top = self.bot = None
        self.left = self.right = self.arrow = None
        self.lmap = self.rmap = None

    # ── a : 7 blanks + gallows; guess I·N·G into the last 3 blanks ─────────────
    def _setup_ing_board(self):
        self.rules7 = gb.build_rules(7)
        self.hang7, self.hang7_parts = gb.build_gallows()
        self.rev7 = VGroup()

    @subscene
    def ing_board(self):
        self._setup_ing_board()
        self.play(LaggedStartMap(Create, self.rules7, lag_ratio=1.0), run_time=2.0)
        self.play(LaggedStartMap(Create, self.hang7.gallows, lag_ratio=0.6),
                  run_time=1.6)
        # bubble-then-write each of I·N·G into its blank (all hits — generic board)
        for ch, pos in zip("ing", ING_POS):
            bub = gb.bubble(ch, tail="left")
            self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.7)
            L = gb.reveal_letter(ch, self.rules7[pos])
            self.rev7.add(L)
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.9)
            self.play(FadeOut(bub), run_time=0.4)

    # ── bar-chart helper (beats b/c) ──────────────────────────────────────────
    def _bar_chart(self, key, *, cy, y_min, y_max, y_ticks):
        d = scene22_data.get()[key]
        items = [(x["letter"], x["misses"]) for x in d["letters"]]
        chart = get_bar_chart(
            items, center=[0, cy, 0], width=CHART_W, height=CHART_H,
            y_min=y_min, y_max=y_max, bar_color=ACCENT_FILL, ink_color=BAR_INK,
            highlight={d["best"]: ACCENT_GOLD}, bar_ratio=0.7,
            label_factory=lambda s: crisp_text(s, font_size=16, color=BAR_INK,
                                                weight=BOLD),
            label_buff=0.12, x_axis=True, y_axis=True, y_ticks=y_ticks,
            y_tick_factory=lambda t: crisp_text(f"{t:g}", font_size=16, color=BAR_INK),
            y_tick_buff=0.12)
        chart.rest = VGroup(chart.labels, chart.x_axis, chart.y_axis, chart.yticks)
        return chart

    def _grow_chart(self, chart, run_time):
        """Add a chart and grow its bars up from the axis while the rest fades in."""
        self.add(chart)
        chart.rest.set_opacity(0)
        grow_bars(self, chart.bars, run_time, lag=0.02,
                  extra=[chart.rest.animate.set_opacity(1)])

    # ── b : remove the board; TOP-half bar chart (uniform) ────────────────────
    @subscene
    def uniform_bar(self):
        self.play(FadeOut(self.cb, self.rules7, self.hang7, self.rev7), run_time=0.8)
        self.cb = self.rules7 = self.hang7 = self.hang7_parts = self.rev7 = None
        self.top = self._bar_chart("uniform", cy=TOP_CY, y_min=3.9, y_max=5.1,
                                   y_ticks=[4.0, 4.5, 5.0])
        self._grow_chart(self.top, 1.2)

    # ── c : BOTTOM-half bar chart (best_opener) — the same chart, harder ───────
    @subscene
    def bestop_bar(self):
        self.bot = self._bar_chart("best_opener", cy=BOT_CY, y_min=5.25, y_max=6.5,
                                   y_ticks=[5.5, 6.0, 6.5])
        self._grow_chart(self.bot, 1.2)

    # ── d : original tier list → arrow → the best_opener tier list ────────────
    @subscene
    def tier_morph(self):
        self.play(FadeOut(self.top, self.bot), run_time=0.6)
        self.top = self.bot = None
        self.left = tl.filled_list(tl.TIER_LETTERS, scale=LIST_SCALE).move_to(
            [LEFT_X, LIST_Y, 0])
        self.play(FadeIn(self.left), run_time=0.8)
        self.right = tl.filled_list(tl.BEST_OPENER_TIER_LETTERS,
                                    scale=LIST_SCALE).move_to([RIGHT_X, LIST_Y, 0])
        tl.morph_into(self, self.left, self.right, tl.TIER_LETTERS,
                      tl.BEST_OPENER_TIER_LETTERS, [0, 1, 2, 3, 4, 5, 6], 2.0)
        self.arrow = Arrow([-1.05, LIST_Y, 0], [1.05, LIST_Y, 0], buff=0.0,
                           color=BLACK, stroke_width=6)
        self.play(GrowArrow(self.arrow), run_time=0.5)
        self.lmap = tl.tile_map(self.left, tl.TIER_LETTERS)
        self.rmap = tl.tile_map(self.right, tl.BEST_OPENER_TIER_LETTERS)

    # ── emphasis helper (e/f): only `letters`' tiles stay full; the rest dim ──
    def _emphasize(self, letters, run_time):
        targets = set()
        for m in (self.lmap, self.rmap):
            for ch in letters:
                if ch in m:
                    targets.add(m[ch])
        anims = []
        for tier_list_ in (self.left, self.right):
            for cont in tier_list_.contents:
                for tile in cont:
                    anims.append(tile.animate.set_opacity(
                        1.0 if tile in targets else tl.DIM_OPACITY))
        self.play(*anims, run_time=run_time)

    # ── e : emphasise I·N·G on both lists (they move UP) ──────────────────────
    @subscene
    def emph_ing(self):
        self._emphasize("ING", 1.0)

    # ── f : emphasise S·R on both lists (they move DOWN) ──────────────────────
    @subscene
    def emph_sr(self):
        self._emphasize("SR", 1.0)

    # ── g : fade both tier lists out ──────────────────────────────────────────
    @subscene
    def clear(self):
        self.play(FadeOut(self.left, self.right, self.arrow), run_time=0.8)
        self.left = self.right = self.arrow = None

"""SCENE 16 — how to USE the tier list (walk down the tiers) + an example game.

Continues from scene 15: the COMPLETE named tier list is centred on the brand
light-blue background from frame 0. We (a) present it, (b) emphasise it tier by
tier — top, then top-two, … — to say "start at the top and move down", (c) tuck
it left, then (d) build a per-length plot on the right that looks like the tier
scenes' position-frequency views (lengths 2–10, faded cell grid) and (e–i) fill
each length's row to the AVERAGE fraction of the word done as the strategy
finishes each tier (TOP → both HIGH → MID↑ → MID↓ → LOW↑), coloured by tier.
Finally (j…) a chalkboard slides in and the near-optimal strategy plays out a
full game for BOARDS.

Script row 16, split on '—' → beats a–j (voiceover ↔ animation zip 1:1). The
game (beat j) is unrolled into per-guess subscenes (j board-in, k–q the seven
guesses, r the win) so each guess keeps its own tunable run_time — the house
gameplay pattern (see 94chalkgame / 02rules).

ALL displayed numbers are SOURCED from `assets/scene16_data.py` (committed
`scene16_cache.json`): the tier-fill fractions are `set_before_outside / length`
under optimal/uniform (letter_analysis.ipynb's method), and the BOARDS guess
order is the optimal/uniform trace. The render reads only the cache.

BEAT MAP
  a establish  — the complete tier list, centred (a soft "breath" to present it)
  b walk_down  — emphasise top tier, then top-two, … down to all lit (dim the rest)
  c to_left    — tuck the tier list to the LEFT, scaled down
  d plot       — build the faded length-2..10 plot on the right (no fill yet)
  e fill_top   — fill each row to the TOP-tier fraction (top-tier colour)
  f fill_high  — extend by both HIGH tiers (their two colours)
  g fill_mid1  — extend by MID↑
  h fill_mid2  — extend by MID↓
  i fill_low1  — extend by LOW↑  (LOW↓ never reached — word usually already done)
  j board_in   — fade the light-bg views out; chalkboard in; draw BOARDS blanks + gallows
  k guess_e    — bubble 'E' → MISS (head)                       (BOARDS has no E)
  l guess_a    — bubble 'A' → HIT  pos 3
  m guess_s    — bubble 'S' → HIT  pos 6
  n guess_r    — bubble 'R' → HIT  pos 4
  o guess_d    — bubble 'D' → HIT  pos 5
  p guess_o    — bubble 'O' → HIT  pos 2
  q guess_b    — bubble 'B' → HIT  pos 1 → BOARDS complete
  r win        — flash the board green, then clear to blank

Render:  render 16a --fast   (…16r)   /   render 16 sub  for the whole scene

TIMING / FEEL KNOBS LEFT AT A GUESS (judge from the video):
  - every run_time here is a first-pass guess (emphasis pacing, fills, guesses).
  - beat a "breath": whether scene 15 truly hands off the list centred (then this
    is a no-op present) or scene 16 should FADE it in — OPEN, ask the user.
  - the chalkboard bring-in (beat j) is a simple fade-out/slide-in — rough.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets import tier_list as tl
from assets import game_board as gb
from assets import scene16_data
from assets.chalkboard import chalkboard

# ── plot geometry (echoes the letter-view position heatmaps: left-aligned rows,
#    one cell per position, a length label to the left; here the grid is FADED and
#    a coloured bar fills the leftmost fraction) ─────────────────────────────────
CELL     = 0.36                     # one position cell (square)
ROW_GAP  = 0.12
ROW_PITCH = CELL + ROW_GAP
PLOT_LEFT_X = -1.4                  # left edge of every row (rows grow RIGHT)
PLOT_TOP_Y  = 1.95                  # top row centre y
GRID_STROKE = tl.TIER_GREY         # faded cell-border colour (tier-list neutral grey)
GRID_OP     = 0.35                  # faded grid opacity ("lines in the middle faded")

# ── tier list resting pose once tucked left (beat c) ──────────────────────────
TL_SCALE = 0.60
TL_LEFT  = [-5.0, 0.0, 0.0]

# ── the example game (beat j…): BOARDS, guess order = optimal/uniform trace ────
_EX = scene16_data.get()["example"]
WORD    = _EX["word"]                                   # "boards"
GUESSES = [g for g, _hit in _EX["trace"]]               # e a s r d o b
MISSES  = [g for g, hit in _EX["trace"] if not hit]     # e


class Scene16(HangmanScene):
    """Walk down the tiers, show the tier-fill plot, then play BOARDS. See the
    module docstring for the full beat map and sourcing."""

    # the complete named tier list is on screen from frame 0 (continues scene 15)
    def setup_scene(self):
        self._setup_tierlist()
        self.data = scene16_data.get()

    # ── builders ──────────────────────────────────────────────────────────────
    def _setup_tierlist(self):
        self.tl = tl.get_tier_list("name")
        for i in range(self.tl.n):
            tl.fill_tier(self.tl, i)                     # sourced TIER_LETTERS[i]
        self.add(self.tl)

    def _setup_plot(self):
        """The faded length-2..10 grid on the right (no fill yet). Stores per-row
        geometry in `self.prows[L]` = {cy, width, fills(VGroup)}."""
        lens = self.data["display_lengths"]
        self.prows = {}
        grid = VGroup()
        labels = VGroup()
        for i, L in enumerate(lens):
            cy = PLOT_TOP_Y - i * ROW_PITCH
            cells = VGroup()
            for k in range(L):
                sq = Square(side_length=CELL)
                sq.set_stroke(GRID_STROKE, width=1.2, opacity=GRID_OP)
                sq.set_fill(GRID_STROKE, opacity=0.08)
                sq.move_to([PLOT_LEFT_X + CELL / 2 + k * CELL, cy, 0])
                cells.add(sq)
            lab = crisp_text(str(L), font_size=24, color=BLACK)
            lab.next_to(cells, LEFT, buff=0.3)
            grid.add(cells)
            labels.add(lab)
            self.prows[L] = {"cy": cy, "width": L * CELL, "fills": VGroup()}
        self.plot = VGroup(labels, grid)
        self.plot_fills = VGroup()                       # coloured bars (added per beat)
        self.plot_labels = labels
        self.plot_grid = grid

    def _fill_segments(self, j):
        """Coloured fill rects for cache tier `j` (segment prev_frac→cur_frac of each
        display row), added BEHIND the faded grid. Returns GrowFromEdge anims."""
        tiers = self.data["tiers"]
        cur = tiers[j]
        prev = tiers[j - 1] if j > 0 else None
        color = tl.NAME_TIER_COLORS[cur["idx"]]
        anims = []
        for L, row in self.prows.items():
            a = prev["frac_by_len"][str(L)] if prev else 0.0
            b = cur["frac_by_len"][str(L)]
            if b - a < 0.005:                            # nothing new on this row
                continue
            W = row["width"]
            x0 = PLOT_LEFT_X + a * W
            rect = Rectangle(width=(b - a) * W, height=CELL)
            rect.set_stroke(width=0).set_fill(color, opacity=0.85)
            rect.move_to([x0 + (b - a) * W / 2, row["cy"], 0])
            rect.set_z_index(-1)                         # behind the grid lines
            row["fills"].add(rect)
            self.plot_fills.add(rect)
            anims.append(GrowFromEdge(rect, LEFT))
        return anims

    # ── a : present the complete tier list (soft breath) ──────────────────────
    @subscene
    def establish(self):
        # continuation from scene 15 (list already centred); a small "breath" to
        # anchor "we now have this massive tier list".  FLAG: see module docstring.
        self.play(self.tl.animate.scale(1.03), rate_func=there_and_back,
                  run_time=0.8)

    # ── b : emphasise top, then top-two, … down to all lit (dim the rest) ──────
    @subscene
    def walk_down(self):
        self.play(*tl.emphasize(self.tl, 0), run_time=0.6)     # top tier alone
        for i in range(1, self.tl.n):                          # grow the lit set down
            self.play(*tl.emphasize(self.tl, range(i + 1)), run_time=0.4)
        self.play(*tl.reset(self.tl), run_time=0.4)            # back to all full

    # ── c : tuck the tier list to the left, scaled down ───────────────────────
    @subscene
    def to_left(self):
        self.play(self.tl.animate.scale(TL_SCALE).move_to(TL_LEFT), run_time=1.0)

    # ── d : build the faded length-2..10 plot on the right ─────────────────────
    @subscene
    def plot(self):
        self._setup_plot()
        self.play(LaggedStart(*[FadeIn(r, shift=0.25 * UP) for r in self.plot_grid],
                              *[FadeIn(l) for l in self.plot_labels],
                              lag_ratio=0.12), run_time=1.4)

    # ── e : fill each row to the TOP-tier fraction ────────────────────────────
    @subscene
    def fill_top(self):
        self.play(*self._fill_segments(0), run_time=1.0)

    # ── f : extend by BOTH high tiers (their two colours) ─────────────────────
    @subscene
    def fill_high(self):
        self.play(*self._fill_segments(1), run_time=0.8)       # HIGH↑
        self.play(*self._fill_segments(2), run_time=0.8)       # HIGH↓

    # ── g : extend by MID↑ ────────────────────────────────────────────────────
    @subscene
    def fill_mid1(self):
        self.play(*self._fill_segments(3), run_time=0.9)

    # ── h : extend by MID↓ ────────────────────────────────────────────────────
    @subscene
    def fill_mid2(self):
        self.play(*self._fill_segments(4), run_time=0.9)

    # ── i : extend by LOW↑ (LOW↓ never reached) ───────────────────────────────
    @subscene
    def fill_low1(self):
        self.play(*self._fill_segments(5), run_time=0.9)

    # ── j : chalkboard in; draw BOARDS blanks + gallows ───────────────────────
    def _setup_board(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.rules = gb.build_rules(len(WORD))
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()
        self.miss_slots_x = gb.miss_slots(self.hang, MISSES)
        self.hit_marks = VGroup()                         # revealed letters (for recolour)

    @subscene
    def board_in(self):
        self._setup_board()
        # clear the light-bg views, slide the chalkboard down over them
        self.cb.shift(UP * 9)
        self.play(FadeOut(self.tl), FadeOut(self.plot), FadeOut(self.plot_fills),
                  run_time=0.6)
        self.tl = None
        self.play(self.cb.animate.shift(DOWN * 9), run_time=0.8)
        # draw the blanks one at a time, then the gallows
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=1.0), run_time=1.8)
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6),
                  run_time=1.6)

    # ── the recurring "play one guess" beat (k–q) ─────────────────────────────
    def _guess(self, i, *, rt_bubble, rt_write, rt_part, rt_out):
        g = GUESSES[i]
        positions = [p for p, c in enumerate(WORD) if c == g]
        bub = gb.bubble(g, tail="left")
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=rt_bubble)
        if positions:                                     # HIT — write each occurrence
            for p in positions:
                L = gb.reveal_letter(g, self.rules[p])
                self.hit_marks.add(L)
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=rt_write)
        else:                                             # MISS — miss row + next part
            m = gb.miss_letter(g, self.miss_slots_x[len(self.miss_row)])
            self.miss_row.add(m)
            self.play(LaggedStartMap(Create, m, lag_ratio=0.5), run_time=rt_write)
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            self.miss_n += 1
            self.play(Create(part), run_time=rt_part)
        self.play(FadeOut(bub), run_time=rt_out)

    @subscene
    def guess_e(self):
        self._guess(0, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_a(self):
        self._guess(1, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_s(self):
        self._guess(2, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_r(self):
        self._guess(3, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_d(self):
        self._guess(4, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_o(self):
        self._guess(5, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    @subscene
    def guess_b(self):
        self._guess(6, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)

    # ── r : win — flash the whole board green, then clear to blank ────────────
    @subscene
    def win(self):
        board = VGroup(self.rules, self.hang, self.miss_row, self.hit_marks)
        self.play(board.animate.set_color(LIGHT_GREEN), run_time=0.5)
        self.wait(0.5)                                    # VO
        self.play(FadeOut(board), FadeOut(self.cb), run_time=0.8)

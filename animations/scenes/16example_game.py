"""SCENE 16 — how to USE the tier list (walk down the tiers) + an example game.

Continues from scene 15: the COMPLETE named tier list is centred on the brand
light-blue background from frame 0. Beat a is a no-op (the list is already
centred — the VO "we now have this massive tier list" plays over it); (b) we
emphasise it tier by tier — top, then top-two, … — to say "start at the top and
move down"; (c) tuck it to the LEFT (the left half of the screen); then (d) build
a per-length plot on the RIGHT half that looks like the tier scenes' location-
frequency views (lengths 2–10, white boxes, black outline, grey dividers) titled
"Usage by Tier", and (e–i) fill each length's row — a bar growing from the LEFT —
to the AVERAGE fraction of the word done as the strategy finishes each tier
(TOP → both HIGH → MID↑ → MID↓ → LOW↑), coloured by tier. Finally (j) a chalkboard
comes in and the near-optimal strategy plays out a full game.

Script row 16, split on '—' → beats a–j (voiceover ↔ animation zip 1:1), ONE
@subscene per beat. The game (beat j) is a SINGLE subscene whose body plays the
whole game (board-in, blanks+gallows, the guesses, the win) — one script beat =
one subscene (see bpkfigures/CLAUDE.md "SUBSCENE COUNT MUST EQUAL BEAT COUNT").

ALL displayed numbers are SOURCED from `assets/scene16_data.py` (committed
`scene16_cache.json`): the tier-fill fractions are `set_before_outside / length`
under optimal/uniform (letter_analysis.ipynb's method), and the example guess
order is that word's optimal/uniform trace. The render reads only the cache.

BEAT MAP
  a have_list  — no-op: the complete tier list is already centred (VO over it)
  b walk_down  — emphasise top tier, then top-two, … down to all lit (dim the rest)
  c to_left    — tuck the tier list to the LEFT half, a bit smaller
  d plot       — build the white/black/grey length-2..10 grid on the right + title
  e fill_top   — grow each row's bar (from the LEFT) to the TOP-tier fraction
  f fill_high  — extend by both HIGH tiers (their two colours)
  g fill_mid1  — extend by MID↑
  h fill_mid2  — extend by MID↓
  i fill_low1  — extend by LOW↑  (LOW↓ never reached — word usually already done)
  j game       — chalkboard in; blanks + gallows; play the whole game; win (green)

Render:  render 16a --fast   (…16j)   /   render 16 sub  for the whole scene

TIMING / FEEL KNOBS LEFT AT A GUESS (judge from the video): every run_time here is
a first-pass guess. The board bring-in (beat j) is a plain fade-out + slide-in —
scene 16 is the FIRST time the chalkboard enters over a light-blue scene (01/02/
03/04/94 have it from frame 0; 11 slides it in over a matching NAVY bg), so there
is no established animation to reuse — this one is bespoke, tune freely.
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

# ── plot geometry (echoes the location-frequency views: left-aligned rows, one
#    white cell per position, a length label to the left; here a coloured bar fills
#    the leftmost fraction, grey dividers between cells, black outline around each) ─
CELL      = 0.40                    # one position cell (square)
ROW_GAP   = 0.14
ROW_PITCH = CELL + ROW_GAP
PLOT_LEFT_X = 0.4                   # left edge of every row (rows grow RIGHT), right half
PLOT_TOP_Y  = 1.7                   # top row centre y (lengths 2..10 stack downward)
TITLE_POS   = [2.4, 2.6, 0.0]       # "Usage by Tier", centred over the rows
DIVIDER_COLOR = tl.TIER_GREY        # grey lines between the individual boxes

# ── tier list resting pose once tucked left (beat c): the LEFT HALF ───────────
TL_SCALE = 0.80
TL_LEFT  = [-4.2, 0.0, 0.0]

# ── the example game (beat j): word + guess order = optimal/uniform trace ──────
_EX = scene16_data.get()["example"]
WORD    = _EX["word"]
GUESSES = [g for g, _hit in _EX["trace"]]
MISSES  = [g for g, hit in _EX["trace"] if not hit]


class Scene16(HangmanScene):
    """Walk down the tiers, show the tier-fill plot, then play the example game.
    See the module docstring for the full beat map and sourcing."""

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
        """The white/black/grey length-2..10 grid on the right (no fill yet), like the
        location-frequency views. Stores per-row geometry in `self.prows[L]`."""
        lens = self.data["display_lengths"]
        self.prows = {}
        boxes = VGroup()
        overlays = VGroup()
        labels = VGroup()
        for i, L in enumerate(lens):
            cy = PLOT_TOP_Y - i * ROW_PITCH
            W = L * CELL
            left = PLOT_LEFT_X
            bg = Rectangle(width=W, height=CELL)
            bg.set_fill(WHITE, opacity=1.0).set_stroke(width=0)
            bg.move_to([left + W / 2, cy, 0])
            outline = Rectangle(width=W, height=CELL)
            outline.set_fill(opacity=0).set_stroke(BLACK, width=1.8)
            outline.move_to([left + W / 2, cy, 0])
            dividers = VGroup(*[
                Line([left + k * CELL, cy - CELL / 2, 0],
                     [left + k * CELL, cy + CELL / 2, 0],
                     color=DIVIDER_COLOR, stroke_width=1.4)
                for k in range(1, L)])
            overlay = VGroup(outline, dividers).set_z_index(2)
            lab = crisp_text(str(L), font_size=24, color=BLACK)
            lab.next_to(bg, LEFT, buff=0.28)
            boxes.add(bg)
            overlays.add(overlay)
            labels.add(lab)
            self.prows[L] = {"cy": cy, "width": W, "left": left, "fills": VGroup()}
        self.title = crisp_text("Usage by Tier", font_size=30, color=BLACK).move_to(TITLE_POS)
        self.plot = VGroup(labels, boxes, overlays)
        self.plot_boxes = boxes
        self.plot_overlays = overlays
        self.plot_labels = labels
        self.plot_fills = VGroup()                       # coloured bars (added per beat)

    def _fill(self, j, run_time):
        """Grow each display row's bar for cache tier `j` (segment prev_frac→cur_frac)
        as a clean WIDTH-wipe from its LEFT edge, coloured by that tier."""
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
            W, left = row["width"], row["left"]
            rect = Rectangle(width=(b - a) * W, height=CELL)
            rect.set_stroke(width=0).set_fill(color, opacity=1.0)
            rect.move_to([left + (a + b) / 2 * W, row["cy"], 0]).set_z_index(1)
            rect.save_state()
            rect.stretch_to_fit_width(1e-3, about_edge=LEFT)   # collapse to its left edge
            self.add(rect)
            row["fills"].add(rect)
            self.plot_fills.add(rect)
            anims.append(Restore(rect))                  # grows rightward from the left
        self.play(*anims, run_time=run_time)

    # ── a : no-op — the tier list is already centred (VO plays over the hold) ──
    @subscene
    def have_list(self):
        pass

    # ── b : emphasise top, then top-two, … down to all lit (dim the rest) ──────
    @subscene
    def walk_down(self):
        self.play(*tl.emphasize(self.tl, 0), run_time=0.6)     # top tier alone
        for i in range(1, self.tl.n):                          # grow the lit set down
            self.play(*tl.emphasize(self.tl, range(i + 1)), run_time=0.4)
        self.play(*tl.reset(self.tl), run_time=0.4)            # back to all full

    # ── c : tuck the tier list to the left half, a bit smaller ────────────────
    @subscene
    def to_left(self):
        self.play(self.tl.animate.scale(TL_SCALE).move_to(TL_LEFT), run_time=1.0)

    # ── d : build the white/black/grey length-2..10 plot on the right + title ──
    @subscene
    def plot(self):
        self._setup_plot()
        self.play(Write(self.title), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(b, shift=0.25 * UP) for b in self.plot_boxes],
                              *[FadeIn(o) for o in self.plot_overlays],
                              *[FadeIn(l) for l in self.plot_labels],
                              lag_ratio=0.10), run_time=1.6)

    # ── e : grow each bar (from the left) to the TOP-tier fraction ────────────
    @subscene
    def fill_top(self):
        self._fill(0, 1.0)

    # ── f : extend by BOTH high tiers (their two colours) ─────────────────────
    @subscene
    def fill_high(self):
        self._fill(1, 0.8)                                     # HIGH↑
        self._fill(2, 0.8)                                     # HIGH↓

    # ── g : extend by MID↑ ────────────────────────────────────────────────────
    @subscene
    def fill_mid1(self):
        self._fill(3, 0.9)

    # ── h : extend by MID↓ ────────────────────────────────────────────────────
    @subscene
    def fill_mid2(self):
        self._fill(4, 0.9)

    # ── i : extend by LOW↑ (LOW↓ never reached) ───────────────────────────────
    @subscene
    def fill_low1(self):
        self._fill(5, 0.9)

    # ── the recurring "play one guess" beat (used inside the game subscene) ────
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

    def _setup_game(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.rules = gb.build_rules(len(WORD))
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()
        self.miss_slots_x = gb.miss_slots(self.hang, MISSES)
        self.hit_marks = VGroup()                         # revealed letters (for recolour)

    # ── j : chalkboard in; blanks + gallows; play the whole game; win ─────────
    @subscene
    def game(self):
        self._setup_game()
        # scene 16 is the first board-over-light-blue case (no established anim):
        # fade the views out, slide the chalkboard in from the top.
        self.cb.shift(UP * 9)
        self.play(FadeOut(self.tl), FadeOut(self.plot), FadeOut(self.plot_fills),
                  FadeOut(self.title), run_time=0.6)
        self.tl = None
        self.play(self.cb.animate.shift(DOWN * 9), run_time=0.8)
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=1.0), run_time=1.8)
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6), run_time=1.6)
        # play the game — the strategy's sourced guesses, one at a time (lockstep)
        for i in range(len(GUESSES)):
            self._guess(i, rt_bubble=0.7, rt_write=0.9, rt_part=0.7, rt_out=0.4)
        # win — flash the whole board green, then clear to blank
        board = VGroup(self.rules, self.hang, self.miss_row, self.hit_marks)
        self.play(board.animate.set_color(LIGHT_GREEN), run_time=0.5)
        self.wait(0.5)                                    # VO
        self.play(FadeOut(board), FadeOut(self.cb), run_time=0.8)

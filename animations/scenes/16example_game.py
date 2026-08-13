"""SCENE 16 — how to USE the tier list (walk down the tiers) + an example game.

Continues from scene 15: the COMPLETE named tier list is centred on the brand
light-blue background from frame 0. Beat a is a no-op (the list is already
centred). (b) emphasise it tier by tier — top, then top-two, … — to say "start at
the top and move down"; (c) tuck it LEFT; then (d) build a per-length plot on the
RIGHT that looks like the location-frequency views (lengths 2–10, white boxes,
black outline, grey dividers) titled "Usage by Tier", entering with the SAME title
FadeIn + row-by-row rise as the tier scenes (`tier_letter_scene.show_heat`/`_rise`);
(e–i) fill each length's row — a bar growing from the LEFT — to the average
fraction of the word done as the strategy finishes each tier (TOP → both HIGH →
MID↑ → MID↓ → LOW↑). Then (j) the chalkboard FADES in and the near-optimal
strategy plays out PLAYERS one guess per beat, ending green.

Horizontal layout: the tier list (left) and the plot (right) are placed for EQUAL
thirds — left margin == middle gap == right margin (computed from measured widths).

Script row 16, split on '—' → one @subscene per beat (see bpkfigures/CLAUDE.md
"SUBSCENE COUNT MUST EQUAL BEAT COUNT"). The script unrolls the game into a beat
per guess.

ALL displayed content is SOURCED from `assets/scene16_data.py` (committed
`scene16_cache.json`): the tier-fill fractions are `set_before_outside / length`
under optimal/uniform, and the guess order is PLAYERS' optimal/uniform trace.

⚠️ SCRIPT / TRACE MISMATCH (flagged, not silently resolved): the script lists the
guesses E S T R A L P Y (one miss, T), but PLAYERS' optimal/uniform trace is
E S T R A L **B** P Y — B is a SECOND miss between L and P (the 2nd miss the word
was chosen for). This scene plays the SOURCED trace (with B), so it has a `guess_b`
subscene the script has no beat for. Either add a "Guess B" beat to the script
(between L and P, in both columns) — recommended — or say to drop B (then remove
`guess_b` and this note). Do NOT leave them out of sync.

BEAT MAP
  a have_list  — no-op: the complete tier list is already centred (VO over it)
  b walk_down  — emphasise top tier, then top-two, … down to all lit (dim the rest)
  c to_left    — tuck the tier list left (equal-thirds layout)
  d plot       — white/black/grey length-2..10 grid on the right + "Usage by Tier"
                 title, entering with the tier-scene FadeIn + row rise
  e fill_top   — grow each row's bar (from the LEFT) to the TOP-tier fraction
  f fill_high  — extend by both HIGH tiers (their two colours)
  g fill_mid1  — extend by MID↑
  h fill_mid2  — extend by MID↓
  i fill_low1  — extend by LOW↑  (LOW↓ never reached)
  j board_in   — FADE the views out / the chalkboard in; draw blanks + gallows
  k guess_e … s guess_y — the nine guesses E S T R A L B P Y, one per beat
  t win        — turn the letters, blanks, and gallows green (per script)

Render:  render 16a --fast   (…16t)   /   render 16 sub  for the whole scene

TIMING / FEEL KNOBS LEFT AT A GUESS (judge from the video): every run_time here is
a first-pass guess. The board FADE-in (beat j) and the green win are the script's
"bring in" / "turn green". Scene END: the script's last beat is "turn green" (no
fade); scene 16 currently ends on the green board — if scene 17 follows directly
(animated, no talking head), it likely needs a fade-out. FLAGGED — confirm.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import numpy as np
from config import *
from assets import tier_list as tl
from assets import views
from assets import game_board as gb
from assets import scene16_data
from assets.chalkboard import chalkboard, chalk_phrase, chalk_letter

# ── plot geometry (echoes the location-frequency views: left-aligned rows, one
#    white cell per position, a length label to the left; a coloured bar fills the
#    leftmost fraction, grey dividers between cells, black outline around each) ────
CELL       = 0.40                   # one position cell (square)
ROW_GAP    = 0.14
ROW_PITCH  = CELL + ROW_GAP
LABEL_BUFF = 0.28                   # gap from length label to its row
# the rows' vertical placement + title y are COMPUTED per-scene (block centred on
# the tier list's centre, y=0) in _compute_layout.
DIVIDER_COLOR = BLACK               # lines between the individual boxes

TL_SCALE = 0.80                     # tier list scale once tucked left

# ── chalk game layout (beats j…): word near the BOTTOM (scene 11 / FIGURES), a
#    CHALK tier list above it, gallows unchanged on the right ────────────────────
GAME_BLANK_Y = -2.6                 # word blanks near the bottom-left (as in scene 11)
CTL_MARGIN   = 0.45                 # inset of the chalk tier list from its box
CTL_GOLD_BUFF = 0.08               # gold guess-box padding


# ── the example game (beat j…): word + guess order = optimal/uniform trace ─────
_EX = scene16_data.get()["example"]
WORD    = _EX["word"]
GUESSES = [g for g, _hit in _EX["trace"]]                # e s t r a l b p y
MISSES  = [g for g, hit in _EX["trace"] if not hit]      # t b


class Scene16(HangmanScene):
    """Walk down the tiers, show the tier-fill plot, then play the example game.
    See the module docstring for the full beat map, sourcing, and the B-miss flag."""

    # the complete named tier list is on screen from frame 0 (continues scene 15)
    def setup_scene(self):
        self._setup_tierlist()
        self.data = scene16_data.get()
        self._compute_layout()

    # ── builders ──────────────────────────────────────────────────────────────
    def _setup_tierlist(self):
        self.tl = tl.get_tier_list("name")
        for i in range(self.tl.n):
            tl.fill_tier(self.tl, i)                     # sourced TIER_LETTERS[i]
        self.add(self.tl)

    def _compute_layout(self):
        """Place the tucked tier list + the plot for EQUAL horizontal thirds:
        left margin == middle gap == right margin (from measured widths)."""
        fx = config.frame_x_radius
        w_tl = self.tl.width * TL_SCALE                  # tier list once scaled
        lens = self.data["display_lengths"]
        w_rows = max(lens) * CELL                        # widest row (L=10)
        w_lab = crisp_text(str(max(lens)), font_size=24).width + LABEL_BUFF
        w_pl = w_lab + w_rows                            # label + rows block
        g = (2 * fx - w_tl - w_pl) / 3
        self._tl_center = np.array([-fx + g + w_tl / 2, 0.0, 0.0])
        self._plot_left = -fx + 2 * g + w_tl + w_lab     # left edge of the ROWS
        self._title_x = self._plot_left + w_rows / 2     # centred over the rows
        # rows block centred on the tier list's centre (y = 0); title just above it
        n = len(lens)
        self._plot_top_y = (n - 1) / 2 * ROW_PITCH       # top row cy (block centred at 0)
        self._title_y = self._plot_top_y + CELL / 2 + 0.55

    def _setup_plot(self):
        """The white/black/grey length-2..10 grid (no fill yet), like the location-
        frequency views. `self.prows[L]` holds each row's geometry; `self.plot_rows`
        are the VGroups the `_rise` entrance lifts in."""
        lens = self.data["display_lengths"]
        self.prows = {}
        self.plot_rows = []
        left = self._plot_left
        for i, L in enumerate(lens):
            cy = self._plot_top_y - i * ROW_PITCH
            W = L * CELL
            bg = Rectangle(width=W, height=CELL)
            bg.set_fill(WHITE, opacity=1.0).set_stroke(width=0)
            bg.move_to([left + W / 2, cy, 0])
            outline = Rectangle(width=W, height=CELL)
            outline.set_fill(opacity=0).set_stroke(BLACK, width=1.8).set_z_index(2)
            outline.move_to([left + W / 2, cy, 0])
            # grey dividers sit ABOVE the coloured fill (z=10) so they READ over it —
            # they're thin lines, so they don't occlude; the black outline stays below
            # the fill (a filled rect above the fill would blank it).
            dividers = VGroup(*[
                Line([left + k * CELL, cy - CELL / 2, 0],
                     [left + k * CELL, cy + CELL / 2, 0],
                     color=DIVIDER_COLOR, stroke_width=1.4)
                for k in range(1, L)]).set_z_index(15)
            lab = crisp_text(str(L), font_size=24, color=BLACK)
            lab.next_to(bg, LEFT, buff=LABEL_BUFF)
            self.prows[L] = {"cy": cy, "width": W, "left": left}
            self.plot_rows.append(VGroup(lab, bg, outline, dividers))
        self.title = views.view_title("Usage by Tier", self._title_x, self._title_y)
        self.plot = VGroup(*self.plot_rows)
        self.plot_fills = VGroup()                       # coloured bars (top-level, tracked)

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
            # z=10 clears the opaque white box (z=0); the grid overlay (z=20) still reads
            # over it. Kept a TOP-LEVEL mobject (self.add) — a fill nested in .plot is
            # silently not rendered.
            rect.move_to([left + (a + b) / 2 * W, row["cy"], 0]).set_z_index(10)
            rect.save_state()
            rect.stretch_to_fit_width(1e-3, about_edge=LEFT)   # collapse to its left edge
            self.add(rect)
            self.plot_fills.add(rect)                    # tracked so board_in can fade it
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

    # ── c : tuck the tier list left (equal-thirds layout) ─────────────────────
    @subscene
    def to_left(self):
        self.play(self.tl.animate.scale(TL_SCALE).move_to(self._tl_center),
                  run_time=1.0)

    # ── d : white/black/grey length-2..10 plot on the right + title (rise-in) ──
    @subscene
    def plot(self):
        self._setup_plot()
        # established entrance (tier scenes' show_heat): title FadeIn + row-by-row rise
        self.play(FadeIn(self.title), views.rise(self, self.plot, self.plot_rows),
                  run_time=1.6)

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

    # ── j : FADE the views out / the chalkboard in; draw blanks, gallows, tiers ──
    def _setup_board(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.rules = gb.build_rules(len(WORD), y=GAME_BLANK_Y)   # word near the bottom
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()
        self.miss_slots_x = gb.miss_slots(self.hang, MISSES)
        self.hit_marks = VGroup()                         # revealed letters (for recolour)
        self.gold_boxes = VGroup()                        # accumulated guess boxes

    def _build_chalk_tierlist(self):
        """The named tier list in CHALK, sat in the box above the bottom word and left
        of the gallows (scene 11's grid region): each row = the tier NAME (+ arrow) in
        its tier colour, then the tier's letters in vowel-red / consonant-blue. Stores
        `self.ctl_tiles[ch]` (each letter's chalk mob) so a guess can gold-box it."""
        name_h, let_h, row_pitch, let_pitch = 0.34, 0.40, 0.60, 0.52
        self.ctl_tiles = {}
        names, letters = [], []
        for i in range(7):
            word, arrow = tl.NAME_LABELS[i]
            c = tl.NAME_TIER_COLORS[i]
            nm = chalk_phrase(word, height=name_h, color=c)
            if arrow:
                # EMPTY outline triangle drawn from lines (like everything else on the
                # chalkboard) — not a filled shape
                tri = Triangle(fill_opacity=0, stroke_color=c, stroke_width=3.0)
                tri.set_height(name_h * 0.62)
                if arrow == "down":
                    tri.rotate(PI)
                nm = VGroup(nm, tri).arrange(RIGHT, buff=0.12)
            names.append(nm)
            # letters in FIXED-WIDTH slots (each centred on k*let_pitch) so column k
            # lines up across every tier (e.g. Q under W under M)
            lets = VGroup()
            for k, ch in enumerate(tl.TIER_LETTERS[i]):
                L = chalk_letter(ch, height=let_h, color=tl.tile_color(ch))
                L.move_to([k * let_pitch, 0, 0])
                self.ctl_tiles[ch.lower()] = L           # guesses are lowercase
                lets.add(L)
            letters.append(lets)
        name_w = max(n.width for n in names)             # name column width
        letters_x = name_w + 0.5                         # where column 0 starts
        rows = VGroup()
        for i, (nm, lets) in enumerate(zip(names, letters)):
            y = -i * row_pitch
            nm.move_to([0, y, 0], aligned_edge=LEFT)                       # names left
            lets.shift(np.array([letters_x, y, 0]))     # slot 0 → letters_x (columns align)
            rows.add(VGroup(nm, lets))
        # fit into the box above the word; CENTRE it horizontally over the word
        word_cx = self.rules.get_center()[0]
        board_top = gb.BOARD_H / 2 - 0.34
        gallows_left = self.hang.get_left()[0]
        word_top = self.rules[0].get_center()[1] + gb.LETTER_BUFF + gb.LETTER_H
        # width available: word centre out to whichever edge is closer (keep clear of gallows)
        half_w = min(word_cx - (-(gb.BOARD_W / 2 - 0.34)), gallows_left - word_cx) - CTL_MARGIN
        box_w, box_h = 2 * half_w, (board_top - word_top) - 2 * CTL_MARGIN
        rows.scale(min(box_w / rows.width, box_h / rows.height, 1.0))
        rows.move_to([word_cx, (word_top + board_top) / 2, 0])
        self.chalk_tl = rows
        return rows

    @subscene
    def board_in(self):
        self._setup_board()
        # fade EVERYTHING else out first, THEN bring the chalkboard in
        self.play(FadeOut(self.tl), FadeOut(self.plot), FadeOut(self.plot_fills),
                  FadeOut(self.title), run_time=0.6)
        self.tl = None
        self.play(FadeIn(self.cb), run_time=0.8)
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=1.0), run_time=1.8)
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6), run_time=1.6)
        # then bring the chalk tier list in — a bulk reference display, so it FADES in
        # (row by row), like the other reference lists/grids (scene 04/11)
        self._build_chalk_tierlist()
        self.play(LaggedStart(*[FadeIn(r) for r in self.chalk_tl], lag_ratio=0.15),
                  run_time=1.6)

    # ── the recurring "play one guess" beat (k–s) ─────────────────────────────
    def _guess(self, i, *, rt_box, rt_write, rt_part):
        """Gold-box the guess on the tier list FIRST (the 'here's my guess' beat —
        replaces the speech bubble for this scene), THEN write the letter into its
        blank(s) on a HIT, or the miss row + next gallows part on a MISS."""
        g = GUESSES[i]
        positions = [p for p, c in enumerate(WORD) if c == g]
        # 1. gold box around this guess in the chalk tier list (accumulates)
        box = SurroundingRectangle(self.ctl_tiles[g], color=ACCENT_GOLD,
                                   buff=CTL_GOLD_BUFF, stroke_width=4).set_z_index(3)
        self.gold_boxes.add(box)
        self.play(Create(box), run_time=rt_box)
        # 2. write the letter
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

    # k–s : the nine guesses E S T R A L B P Y (B is the flagged 2nd miss)
    @subscene
    def guess_e(self):
        self._guess(0, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_s(self):
        self._guess(1, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_t(self):
        self._guess(2, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_r(self):
        self._guess(3, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_a(self):
        self._guess(4, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_l(self):
        self._guess(5, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    # q : guess B — the sourced 2nd miss the script omits (see the module flag)
    @subscene
    def guess_b(self):
        self._guess(6, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_p(self):
        self._guess(7, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    @subscene
    def guess_y(self):
        self._guess(8, rt_box=0.5, rt_write=0.9, rt_part=0.7)

    # ── t : turn the letters, blanks, and gallows green (per script) ──────────
    @subscene
    def win(self):
        # turn the letters, blanks, gallows AND the miss row (T, B) below it green
        green = VGroup(self.rules, self.hang, self.hit_marks, self.miss_row)
        self.play(green.animate.set_color(LIGHT_GREEN), run_time=0.6)

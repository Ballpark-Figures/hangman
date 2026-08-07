"""SCENE 02 — "what is hangman?": the rules, taught on the chalkboard with BALLPARK.

Structurally the chalk game (`94chalkgame`): navy chalkboard backdrop, word blanks
on the LEFT, gallows on the RIGHT, a white speech bubble per guess; a HIT is written
into its blank(s), a MISS is written below the gallows and draws the next body part.
Reuses chalkboard / chalk_letter / hangman_drawing / speech_bubble verbatim.

Word = BALLPARK.  Guess order follows the test scene's converged len-8 uniform
optimal walk (hits a·l·k·b·p·r), but re-ordered here to TEACH: a HIT first (A), then
a MISS (E), then the win/loss cases.  The letters that are NOT in ballpark
(e / i o t n d) are the misses that fill the hangman in the LOSS case.

Body-part colours (beat g's demo only) = the intro's tree-edge miss colours:
part k (1..6) → LIGHT_PALETTE[6-k]  →  head purple, torso blue, L-arm green,
R-arm yellow, L-leg orange, R-leg red.  Real misses draw in plain white chalk.

The chalkboard is on screen from frame 0 (the script's "fade in chalkboard" beat
is dropped) — so `setup_scene` holds it and the first subscene draws the blanks.

Script beat ↔ subscene (Script.md row 02, split on '—'):
  a blanks     — "chooser chooses a word, draws the blanks"         draw 8 blanks
  b gallows    — "draws a set of gallows to keep score"             draw gallows
  c guess_a    — "the guesser guesses letters one at a time"        bubble 'A'
  d fill_a     — "if in the word, chooser fills all its blanks"     write A (pos 2 & 6)
  e guess_e    — "if not in the word, draws a body part"            'E' miss → head
  f body_parts — "6 parts: head, torso, 2 arms, 2 legs"             colour demo, then revert
  g win        — "complete the word first → the guesser wins"       fill L K B P R + green sparks, reset
  h lose       — "hangman filled first → the chooser wins"          miss I O T N D + red sparks → full hangman

BEAT MAP
  blanks     — draw the 8 word blanks, one at a time
  gallows    — draw the gallows on the right
  guess_a    — pop the guesser's 'A' bubble
  fill_a     — write the two A's into their blanks, dismiss the bubble
  guess_e    — 'E' misses: write it below the gallows + draw the head (miss #1)
  body_parts — recolour the head, draw the other 5 parts in palette colours, then revert
  win        — guess L K B P R → BALLPARK complete; green chalk sparks (B & K haloes), drawn one at a time; fade word + sparks back to A's + E-miss + head
  lose       — guess I O T N D → full hangman; red chalk sparks at the 4 corners, drawn one at a time, then fade together

Render:  render 02a --fast … 02h   /   render 02 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every guess's
bubble/write/part/out run_times, the colour-demo per-part 0.5s, the win-hold /
reset run_times in `win`, and the one-at-a-time spark draw (1.5s) + DASH/ARC/CLUSTER shape.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.speech_bubble import speech_bubble
from assets.chalkboard import chalkboard, chalk_letter, CHALK
from assets.hangman_board import hangman_drawing

# ── the game (word + the letters guessed in each phase) ───────────────────────
WORD      = "ballpark"
WIN_HITS  = ["l", "k", "b", "p", "r"]     # remaining hits, test-scene order → WIN
LOSE_MISS = ["i", "o", "t", "n", "d"]     # not in ballpark → fill the hangman → LOSS
FULL_MISS = ["e", *LOSE_MISS]             # every miss in reveal order (E first, then loss)


def _part_color(k):
    """Body part k (1..6) → the intro's tree-edge miss colour for miss #k
    (= scene 01's `_miss_color(k)`): head purple … R-leg red."""
    return LIGHT_PALETTE[len(LIGHT_PALETTE) - k]


# ── layout (verbatim from 94chalkgame — same word, same board) ────────────────
BOARD_W, BOARD_H = 15.2, 8.4

BLANK_SLOT   = 0.50     # width of one underscore rule
BLANK_GAP    = 0.22     # gap between blanks
BLANK_CX     = -3.0     # blank-row centre x (left side of the board)
BLANK_Y      = -0.38    # rule baseline; a filled blank is vertically centred at y=0
BLANK_SW     = 6.0      # chalk stroke width for the rules
LETTER_H     = 0.62     # cap height of a revealed letter (drawn as strokes)
LETTER_SW    = 4.5      # chalk stroke width for a revealed letter
LETTER_BUFF  = 0.14

HANG_SCALE   = 1.2                      # gallows on the RIGHT
HANG_POS     = np.array([4.3, 0.5, 0])
HANG_SW      = 6.0
MISS_H       = 0.50                     # wrong letters, chalked below the gallows
MISS_SW      = 4.0
MISS_Y       = -2.75                    # miss-row baseline (centred x = the gallows base)
MISS_GAP     = 0.34

# the guesser is off the LEFT edge: the tail TIP sits at the screen edge and the
# bubble grows from there. Anchored by the tip — NOT move_to (its group-bbox centring
# would pull the long tail inward). Verbatim from 94chalkgame.
BUBBLE_TIP   = np.array([-7.9, 2.4, 0])
BUBBLE_FS    = 56
BUBBLE_TAIL  = 1.5

# win/loss flash: short chalk dashes DRAWN ONE AT A TIME (Create, sequential) — a
# single hand sparking the board. Green on the win, red on the loss (intro palette).
DASH_LEN     = 0.28    # length of each dash
DASH_SW      = 4.0     # dash stroke width

# WIN: two radial haloes — a left arc around the B (drawn 6→12 o'clock) and a right
# arc around the K (drawn 12→6 o'clock).
WIN_ARC_N    = 6       # dashes per arc
WIN_ARC_GAP  = 0.14    # gap from the letter to a dash's inner end

# LOSE: four small clusters, one near each corner of the drawing (gallows top-left /
# top-right, the E, the D), each a few dashes fanned outward from the drawing centre.
LOSE_CLUSTER_N      = 3     # dashes per corner
LOSE_CLUSTER_SPREAD = 0.8   # angular fan width (radians)
LOSE_CLUSTER_STAND  = 0.14  # standoff from the corner point to a dash's inner end


class Scene02(HangmanScene):
    """Teach the rules of hangman on the chalkboard, playing BALLPARK.

    chalkboard/CHALK from assets.chalkboard; gallows from
    assets.hangman_board.hangman_drawing (chalk-white); the guesser's speech bubble
    from bpkfigures.speech_bubble.

    Unlike 94chalkgame's single `_guess` beat, the guess and the fill are split
    across subscenes here (d pops the bubble, e writes the hit) to teach the
    mechanic, so the small chalk builders (_bubble / _reveal_letter / _miss_letter)
    are exposed and composed per subscene.
    """

    # the wooden chalkboard is the backdrop — on screen from frame 0
    def setup_scene(self):
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── small chalk builders (verbatim from 94chalkgame) ──────────────────────
    def _reveal_letter(self, ch, rule):
        L = chalk_letter(ch, height=LETTER_H, stroke_width=LETTER_SW, color=CHALK)
        L.next_to(rule, UP, buff=LETTER_BUFF)
        L.set_x(rule.get_center()[0])
        return L

    def _miss_letter(self, ch):
        # each miss drops into its precomputed slot (see _setup_gallows): the FULL
        # 6-miss row is laid out centred under the gallows, so the finished tally sits
        # centred (the early lone E therefore sits left of centre — a static shift, not
        # a per-miss recentre).
        L = chalk_letter(ch, height=MISS_H, stroke_width=MISS_SW, color=CHALK)
        L.move_to([self.miss_slots_x[len(self.miss_row)], MISS_Y, 0])
        self.miss_row.add(L)
        return L

    def _bubble(self, ch):
        b = speech_bubble(ch.upper(), font_size=BUBBLE_FS, tail="left",
                          tail_len=BUBBLE_TAIL)
        b.shift(BUBBLE_TIP - b.tip_dot.get_center())   # anchor the tail tip
        return b

    # ── composed guess steps ──────────────────────────────────────────────────
    def _pop_bubble(self, ch, run_time):
        """Pop the guesser's speech bubble on the right; leaves it up (self.bub)."""
        self.bub = self._bubble(ch)
        self.play(GrowFromPoint(self.bub, self.bub.tip_dot.get_center()),
                  run_time=run_time)

    def _write_hit(self, ch, run_time):
        """Write ch into every blank it occupies, LEFT→RIGHT, stroke-by-stroke.
        Records the letters under self.hits[ch] so the win-reset can fade them."""
        letters = VGroup()
        for p in [p for p, c in enumerate(WORD) if c == ch]:
            L = self._reveal_letter(ch, self.rules[p])
            letters.add(L)
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=run_time)
        self.hits[ch] = letters

    def _write_miss(self, ch, *, rt_write, rt_part):
        """A miss: write ch below the gallows, then draw the next body part (white)."""
        miss = self._miss_letter(ch)
        self.play(LaggedStartMap(Create, miss, lag_ratio=0.5), run_time=rt_write)
        part = self.hang_parts[self.miss_n]
        part.set_color(CHALK)            # reset any leftover demo colour (beat g)
        self.hang.add(part)
        self.miss_n += 1
        self.play(Create(part), run_time=rt_part)

    def _dismiss_bubble(self, run_time):
        self.play(FadeOut(self.bub), run_time=run_time)

    # ── win/loss flash: short chalk dashes, drawn one at a time ───────────────
    def _add_radial_dashes(self, group, center, r_inner, angles, color):
        """Append a radial dash for each angle in `angles` (in order), each pointing
        outward from `center`, inner end at radius `r_inner`. Order = draw order."""
        for a in angles:
            d = np.array([np.cos(a), np.sin(a), 0.0])
            inner = center + r_inner * d
            group.add(Line(inner, inner + DASH_LEN * d, stroke_color=color,
                           stroke_width=DASH_SW))

    def _add_cluster_dashes(self, group, point, outward, color):
        """Append LOSE_CLUSTER_N dashes fanned about the `outward` direction, all
        emanating from just past `point` — a little spark at one corner."""
        base = np.arctan2(outward[1], outward[0])
        n = LOSE_CLUSTER_N
        for i in range(n):
            frac = 0.0 if n == 1 else (i - (n - 1) / 2) / (n - 1)
            a = base + LOSE_CLUSTER_SPREAD * frac
            d = np.array([np.cos(a), np.sin(a), 0.0])
            inner = point + LOSE_CLUSTER_STAND * d
            group.add(Line(inner, inner + DASH_LEN * d, stroke_color=color,
                           stroke_width=DASH_SW))

    def _draw_one_at_a_time(self, dashes, run_time):
        """Create the dashes sequentially (lag_ratio=1.0) — a single hand drawing
        each in turn, in the group's order. Leaves them on screen for the caller."""
        self.play(LaggedStartMap(Create, dashes, lag_ratio=1.0), run_time=run_time)

    # ── setup helpers ─────────────────────────────────────────────────────────
    def _setup_blanks(self):
        n = len(WORD)
        total = n * BLANK_SLOT + (n - 1) * BLANK_GAP
        x0 = BLANK_CX - total / 2 + BLANK_SLOT / 2
        self.rules = VGroup()
        for k in range(n):
            x = x0 + k * (BLANK_SLOT + BLANK_GAP)
            self.rules.add(Line([x - BLANK_SLOT / 2, BLANK_Y, 0],
                                [x + BLANK_SLOT / 2, BLANK_Y, 0],
                                color=CHALK, stroke_width=BLANK_SW))
        self.hits = {}                   # guess char → VGroup of its revealed letters

    def _setup_gallows(self):
        # build with ALL parts so scale/move places them too, THEN detach them
        # (revealed one per miss); the gallows stays, drawn in subscene c.
        full = hangman_drawing(6, color=CHALK, stroke_width=HANG_SW)
        full.scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)     # 6 body parts, in draw order
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full
        self.miss_n = 0
        self.miss_row = VGroup()               # wrong letters, chalked below
        # Precompute the miss-row slots: lay the FULL miss set (E, then the loss
        # letters) left→right and CENTRE the finished row under the gallows base, so
        # each miss lands in its final slot and the completed tally is centred. Measured
        # off the base (gallows[0]) so it tracks the gallows if it moves.
        gallows_cx = self.hang.gallows[0].get_center()[0]
        tmpl = VGroup(*[chalk_letter(ch, height=MISS_H, stroke_width=MISS_SW,
                                     color=CHALK) for ch in FULL_MISS])
        tmpl.arrange(RIGHT, buff=MISS_GAP)
        tmpl.move_to([gallows_cx, MISS_Y, 0])
        self.miss_slots_x = [m.get_center()[0] for m in tmpl]

    # ══════════════════════════════════════════════════════════════════════════
    #  SUBSCENES
    # ══════════════════════════════════════════════════════════════════════════

    # a : draw the 8 word blanks, one at a time
    @subscene
    def blanks(self):
        self._setup_blanks()
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=0.8), run_time=2.2)

    # b : draw the gallows on the right
    @subscene
    def gallows(self):
        self._setup_gallows()
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6),
                  run_time=1.6)

    # c : the guesser guesses a letter — pop the 'A' bubble
    @subscene
    def guess_a(self):
        self._pop_bubble("a", 0.7)

    # d : 'A' is in the word — write it into both its blanks, dismiss the bubble
    @subscene
    def fill_a(self):
        self._write_hit("a", 0.9)
        self._dismiss_bubble(0.4)

    # e : 'E' is NOT in the word — chalk it below the gallows + draw the head
    @subscene
    def guess_e(self):
        self._pop_bubble("e", 0.7)
        self._write_miss("e", rt_write=0.9, rt_part=0.7)   # head = miss #1
        self._dismiss_bubble(0.4)

    # f : the 6 body parts — recolour the head, draw the rest in palette colours,
    #     then revert to just a white head (this was only a demo of the parts).
    @subscene
    def body_parts(self):
        head = self.hang_parts[0]
        self.play(head.animate.set_color(_part_color(1)), run_time=0.5)  # purple
        for k in range(2, 7):                    # torso, L-arm, R-arm, L-leg, R-leg
            part = self.hang_parts[k - 1]
            part.set_color(_part_color(k))
            self.hang.add(part)
            self.play(Create(part), run_time=0.5)
        # revert: head back to white, fade the other 5 parts back out
        rest = VGroup(*self.hang_parts[1:])
        self.play(head.animate.set_color(CHALK), FadeOut(rest), run_time=0.8)
        for p in self.hang_parts[1:]:
            self.hang.remove(p)

    # g : the WIN — guess the remaining hits (L K B P R) to complete BALLPARK, spark
    #     green chalk dashes (a left halo on the B, a right halo on the K) drawn one at
    #     a time, then fade the word + those dashes back to A's + E-miss + head.
    @subscene
    def win(self):
        for g in WIN_HITS:
            self._pop_bubble(g, 0.6)
            self._write_hit(g, 0.8)
            self._dismiss_bubble(0.3)
        # celebratory chalk sparks: left arc around the B (6→12 o'clock), right arc
        # around the K (12→6 o'clock) — drawn one dash at a time.
        b, k = self.hits["b"], self.hits["k"]
        self.win_dashes = VGroup()
        self._add_radial_dashes(self.win_dashes, b.get_center(),
                                max(b.width, b.height) / 2 + WIN_ARC_GAP,
                                np.linspace(3 * PI / 2, PI / 2, WIN_ARC_N), LIGHT_GREEN)
        self._add_radial_dashes(self.win_dashes, k.get_center(),
                                max(k.width, k.height) / 2 + WIN_ARC_GAP,
                                np.linspace(PI / 2, -PI / 2, WIN_ARC_N), LIGHT_GREEN)
        self._draw_one_at_a_time(self.win_dashes, 1.5)
        self.wait(0.4)                                           # VO: "…they win"
        won = VGroup(*[self.hits[g] for g in WIN_HITS])
        self.play(FadeOut(won), FadeOut(self.win_dashes),        # dashes fade WITH the word
                  run_time=0.8)                                  # reset to partial

    # h : the LOSS — guess I O T N D (all misses); each draws the next body part,
    #     filling the hangman (6 misses with the earlier E) → the chooser wins. Red
    #     chalk sparks at the four corners (gallows TL/TR, the E, the D), drawn one at a
    #     time, then all fade together.
    @subscene
    def lose(self):
        for g in LOSE_MISS:
            self._pop_bubble(g, 0.6)
            self._write_miss(g, rt_write=0.8, rt_part=0.6)
            self._dismiss_bubble(0.3)
        lost = VGroup(self.hang, self.miss_row)
        centre = lost.get_center()
        corners = [self.hang.gallows.get_corner(UL),    # top-left of the gallows
                   self.hang.gallows.get_corner(UR),    # top-right of the gallows
                   self.miss_row[0].get_center(),       # the E
                   self.miss_row[-1].get_center()]      # the D
        self.lose_dashes = VGroup()
        for pt in corners:
            out = pt - centre
            n = np.linalg.norm(out)
            self._add_cluster_dashes(self.lose_dashes, pt,
                                     out / n if n > 1e-9 else RIGHT, LIGHT_RED)
        self._draw_one_at_a_time(self.lose_dashes, 1.5)
        self.wait(0.4)                                           # VO: "…the chooser wins"
        self.play(FadeOut(self.lose_dashes), run_time=0.6)       # all fade together

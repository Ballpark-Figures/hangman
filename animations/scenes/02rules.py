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

The chalkboard fades in in the opening subscene `a` (`establish`) — the intro VO
("what is hangman… the chooser and the guesser") plays over it — then the blanks
are drawn.  So `setup_scene` holds NOTHING (blank frame 0).

Script beat ↔ subscene (Script.md row 02, split on '—'):
  a establish  — "what is hangman… the chooser and the guesser"     fade in chalkboard
  b blanks     — "chooser chooses a word, draws the blanks"         draw 8 blanks
  c gallows    — "draws a set of gallows to keep score"             draw gallows
  d guess_a    — "the guesser guesses letters one at a time"        bubble 'A'
  e fill_a     — "if in the word, chooser fills all its blanks"     write A (pos 2 & 6)
  f guess_e    — "if not in the word, draws a body part"            'E' miss → head
  g body_parts — "6 parts: head, torso, 2 arms, 2 legs"             colour demo, then revert
  h win        — "complete the word first → the guesser wins"       fill L K B P R, flash green, reset
  i lose       — "hangman filled first → the chooser wins"          miss I O T N D → full hangman, flash red

BEAT MAP
  establish  — fade in the chalkboard (intro VO plays over it)
  blanks     — draw the 8 word blanks, one at a time
  gallows    — draw the gallows on the right
  guess_a    — pop the guesser's 'A' bubble
  fill_a     — write the two A's into their blanks, dismiss the bubble
  guess_e    — 'E' misses: write it below the gallows + draw the head (miss #1)
  body_parts — recolour the head, draw the other 5 parts in palette colours, then revert
  win        — guess L K B P R → BALLPARK complete; flash every white mark green; fade the word back to A's + E-miss + head (rest returns to white)
  lose       — guess I O T N D → full hangman; flash every white mark red and back to white

Render:  render 02a --fast … 02i   /   render 02 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every guess's
bubble/write/part/out run_times, the colour-demo per-part 0.5s, the win-hold /
reset run_times in `win`, and the green/red flash time (in `win`/`lose`).
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.chalkboard import chalkboard, CHALK
from assets import game_board as gb

# ── the game (word + the letters guessed in each phase) ───────────────────────
WORD      = "ballpark"
WIN_HITS  = ["l", "k", "b", "p", "r"]     # remaining hits, test-scene order → WIN
LOSE_MISS = ["i", "o", "t", "n", "d"]     # not in ballpark → fill the hangman → LOSS
FULL_MISS = ["e", *LOSE_MISS]             # every miss in reveal order (E first, then loss)


def _part_color(k):
    """Body part k (1..6) → the intro's tree-edge miss colour for miss #k
    (= scene 01's `_miss_color(k)`): head purple … R-leg red."""
    return LIGHT_PALETTE[len(LIGHT_PALETTE) - k]


# The fixed board layout (blanks/gallows/miss row/bubble + their constants) now
# lives in assets.game_board (gb) — shared with 94chalkgame / 04greedy.

# win/loss flash: every white chalk mark on the board flashes colour — green when the
# guesser wins (returning to white as the word fades), red when they lose (LIGHT_GREEN
# / LIGHT_RED from the intro palette).


class Scene02(HangmanScene):
    """Teach the rules of hangman on the chalkboard, playing BALLPARK.

    chalkboard/CHALK from bpkfigures.chalkboard; gallows from
    assets.hangman_board.hangman_drawing (chalk-white); the guesser's speech bubble
    from bpkfigures.speech_bubble.

    Unlike 94chalkgame's single `_guess` beat, the guess and the fill are split
    across subscenes here (d pops the bubble, e writes the hit) to teach the
    mechanic, so the small chalk builders (_bubble / _reveal_letter / _miss_letter)
    are exposed and composed per subscene.
    """

    # nothing on screen at frame 0 — the chalkboard fades in in `establish` (beat a)
    def setup_scene(self):
        pass

    # ── small chalk builders (shared board layout: assets.game_board) ─────────
    def _reveal_letter(self, ch, rule):
        return gb.reveal_letter(ch, rule)

    def _miss_letter(self, ch):
        # each miss drops into its precomputed slot (see _setup_gallows): the FULL
        # 6-miss row is laid out centred under the gallows, so the finished tally sits
        # centred (the early lone E therefore sits left of centre — a static shift, not
        # a per-miss recentre).
        L = gb.miss_letter(ch, self.miss_slots_x[len(self.miss_row)])
        self.miss_row.add(L)
        return L

    def _bubble(self, ch):
        return gb.bubble(ch, tail="left")

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
            self.play(LaggedStartMap(Create, L, lag_ratio=1.0), run_time=run_time)
        self.hits[ch] = letters

    def _write_miss(self, ch, *, rt_write, rt_part):
        """A miss: write ch below the gallows, then draw the next body part (white)."""
        miss = self._miss_letter(ch)
        self.play(LaggedStartMap(Create, miss, lag_ratio=1.0), run_time=rt_write)
        part = self.hang_parts[self.miss_n]
        part.set_color(CHALK)            # reset any leftover demo colour (beat g)
        self.hang.add(part)
        self.miss_n += 1
        self.play(Create(part), run_time=rt_part)

    def _dismiss_bubble(self, run_time):
        self.play(FadeOut(self.bub), run_time=run_time)

    # ── win/loss flash: recolour every white chalk mark on the board ──────────
    def _chalk_marks(self, *, exclude=None):
        """Every white chalk mark currently on the board — blanks, revealed letters,
        the gallows + drawn body parts, and the miss row — as one flat VGroup (minus
        any handles in `exclude`). Used to flash the whole board green / red."""
        exclude = exclude or ()
        parts = [self.rules, self.hang, self.miss_row, *self.hits.values()]
        return VGroup(*[p for p in parts if p not in exclude])

    # ── setup helpers ─────────────────────────────────────────────────────────
    def _setup_blanks(self):
        self.rules = gb.build_rules(len(WORD))
        self.hits = {}                   # guess char → VGroup of its revealed letters

    def _setup_gallows(self):
        # gallows on the RIGHT with parts detached (revealed one per miss); the FULL
        # miss set (E, then the loss letters) is centred under the gallows base, so
        # each miss lands in its final slot and the completed tally is centred (the
        # early lone E sits left of centre — a static shift, not a per-miss recentre).
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()               # wrong letters, chalked below
        self.miss_slots_x = gb.miss_slots(self.hang, FULL_MISS)

    # ══════════════════════════════════════════════════════════════════════════
    #  SUBSCENES
    # ══════════════════════════════════════════════════════════════════════════

    # a : fade in the chalkboard (the intro VO — "what is hangman…" — plays over it)
    @subscene
    def establish(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.play(FadeIn(self.cb), run_time=1.0)

    # b : draw the 8 word blanks, one at a time
    @subscene
    def blanks(self):
        self._setup_blanks()
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=1.0), run_time=2.2)

    # c : draw the gallows on the right
    @subscene
    def gallows(self):
        self._setup_gallows()
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=1.0),
                  run_time=1.6)

    # d : the guesser guesses a letter — pop the 'A' bubble
    @subscene
    def guess_a(self):
        self._pop_bubble("a", 0.7)

    # e : 'A' is in the word — write it into both its blanks, dismiss the bubble
    @subscene
    def fill_a(self):
        self._write_hit("a", 0.9)
        self._dismiss_bubble(0.4)

    # f : 'E' is NOT in the word — chalk it below the gallows + draw the head
    @subscene
    def guess_e(self):
        self._pop_bubble("e", 0.7)
        self._write_miss("e", rt_write=0.9, rt_part=0.7)   # head = miss #1
        self._dismiss_bubble(0.4)

    # g : the 6 body parts — recolour the head, draw the rest in palette colours,
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
        self.play(head.animate.set_color(CHALK), FadeOut(rest), run_time=0.3)
        for p in self.hang_parts[1:]:
            self.hang.remove(p)

    # h : the WIN — guess the remaining hits (L K B P R) to complete BALLPARK; every
    #     white mark flashes GREEN, then returns to white as the word fades back to the
    #     A's + E-miss + head.
    @subscene
    def win(self):
        for g in WIN_HITS:
            self._pop_bubble(g, 0.3)
            self._write_hit(g, 0.3)
            self._dismiss_bubble(0.3)
        self.play(self._chalk_marks().animate.set_color(LIGHT_GREEN),  # flash green
                  run_time=0.3)                                       # VO: "…they win"
        won = VGroup(*[self.hits[g] for g in WIN_HITS])
        kept = self._chalk_marks(exclude=[self.hits[g] for g in WIN_HITS])
        self.play(FadeOut(won),                                  # completed word fades…
                  kept.animate.set_color(CHALK), run_time=0.3)   # …the rest back to white
        for g in WIN_HITS:
            self.hits.pop(g, None)         # only the A's remain in self.hits now

    # i : the LOSS — guess I O T N D (all misses); each draws the next body part,
    #     filling the hangman (6 misses with the earlier E) → the chooser wins. Every
    #     white mark flashes RED and back to white.
    @subscene
    def lose(self):
        for g in LOSE_MISS:
            self._pop_bubble(g, 0.3)
            self._write_miss(g, rt_write=0.3, rt_part=0.3)
            self._dismiss_bubble(0.3)
        self.play(self._chalk_marks().animate.set_color(LIGHT_RED),    # flash red…
                  run_time=0.3)

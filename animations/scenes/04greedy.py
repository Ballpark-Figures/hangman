"""SCENE 04 — the GREEDY strategy for 3-letter words, on the chalkboard.

Assume every word is equally likely; guess the letter that appears in the most
remaining candidate words (greedy). We watch a montage of finished 3-letter
games, then walk the whole greedy decision for a 3-letter word: a sorted
letter-FREQUENCY bar graph (bottom-left) drives every guess, the 3 blanks (top)
show the revealed pattern, and misses pile under the gallows (right).

All numbers are SOURCED from `assets/greedy_data.py` (committed `greedy_cache.json`,
built from `strategy.GreedyGame` / `letter_patterns`); the render reads only the
cache. See that module for provenance.

Script row 04, split on '—' → 22 beats a–v (voiceover ↔ animation zip 1:1):
  a montage     — series of finished greedy 3-letter games; win=green, loss=red
  b clear       — clear all but the gallows + 3 blanks
  c root_bars   — freq bar graph, 3-letter words, sorted by # appearances (A=186/640)
  d two_a       — blanks _AA, bars→_AA candidates, fill B → BAA (win, green)
  e ends_a      — blanks __A, bars→13 words ending in A → E (~½)
  f starts_a    — blanks A__ → E
  g mid_a       — blanks _A_ → P (~1/6)
  h absent_o    — blanks ___, A a MISS under gallows + head; bars→454 → O (~1/3)
  --- (miss chain i–n, avg-misses chart o, PIRATES p, E-combos q, len-17 t–v: TODO)

BEAT MAP (implemented so far: a–h)
  montage    — a few finished greedy games flash by, tinted green (win) / red (loss)
  clear      — everything fades but the gallows + 3 blanks
  root_bars  — the sorted letter-frequency bar graph fades in (A on top)
  two_a      — reveal _AA, morph bars to the lone BAA candidate, guess B → win
  ends_a     — reveal __A, morph bars to the 13 A-enders, guess E
  starts_a   — reveal A__, morph bars, guess E
  mid_a      — reveal _A_, morph bars, guess P
  absent_o   — A missed (under gallows + head), morph bars to the 454, guess O

Render:  render 04c --fast   (…04h)   /   render 04 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade/morph
run_time; the montage per-game hold; the bar-morph run_times in c–h.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import chalkboard, chalk_letter, CHALK
from assets.hangman_board import hangman_drawing
from assets import greedy_data

# ── data (committed cache; no solver at render) ───────────────────────────────
DATA = greedy_data.get()

# ── board layout (16×9 frame → x∈[-8,8], y∈[-4.5,4.5]) ────────────────────────
BOARD_W, BOARD_H = 15.2, 8.4

WORD_LEN   = 3
BLANK_SLOT = 0.60
BLANK_GAP  = 0.30
BLANK_CX   = 0.0        # blanks centred, near the top
BLANK_Y    = 2.55
BLANK_SW   = 6.0
LETTER_H   = 0.72
LETTER_SW  = 4.5
LETTER_BUFF = 0.16

HANG_SCALE = 0.85
HANG_POS   = np.array([5.1, -0.2, 0])
HANG_SW    = 5.0
MISS_H     = 0.46
MISS_SW    = 4.0
MISS_Y     = -2.9
MISS_GAP   = 0.30

# ── frequency bar graph (bottom-left) ─────────────────────────────────────────
BARS_UL     = np.array([-7.4, 2.2, 0])   # upper-left anchor of row 0
BARS_TOP    = 10                          # how many letters to show
BAR_MAX_W   = 3.4                         # length of the longest bar
BAR_ROW_H   = 0.34
BAR_ROW_BUFF = 0.14
BAR_LABEL_W = 0.5                         # gap from anchor to bar start (the letter)
BAR_COLOR   = ACCENT_FILL
BAR_HL      = ACCENT_GOLD                 # greedy's pick (top bar)
BAR_FS      = 26


def _freq_bars(pairs, *, top=BARS_TOP, hl_letter=None, scale_max=None):
    """A sorted horizontal letter-frequency bar graph in chalk styling.

    `pairs` = [(letter, count)] already sorted descending. Returns a VGroup with
    ``.rows`` = {letter: row VGroup(label, bar, value)} so a later beat can morph
    row-by-row as the candidate set changes. `hl_letter` (default: the top row =
    greedy's pick) is drawn in BAR_HL. Bars normalise to `scale_max` (default:
    this call's own max), so the top bar fills BAR_MAX_W."""
    shown = pairs[:top]
    if scale_max is None:
        scale_max = max((c for _, c in shown), default=1)
    if hl_letter is None and shown:
        hl_letter = shown[0][0]
    grp = VGroup()
    grp.rows = {}
    bar_x0 = BARS_UL[0] + BAR_LABEL_W
    for i, (ltr, count) in enumerate(shown):
        y = BARS_UL[1] - i * (BAR_ROW_H + BAR_ROW_BUFF)
        label = chalk_letter(ltr, height=BAR_ROW_H * 0.8, stroke_width=3.2,
                             color=CHALK)
        label.move_to([BARS_UL[0], y, 0])
        length = max(count / scale_max * BAR_MAX_W, 1e-3)
        col = BAR_HL if ltr == hl_letter else BAR_COLOR
        bar = Rectangle(width=length, height=BAR_ROW_H, fill_color=col,
                        fill_opacity=1.0, stroke_width=0)
        bar.move_to([bar_x0 + length / 2, y, 0])
        value = crisp_text(str(count), font_size=BAR_FS * 0.7, color=CHALK)
        value.next_to(bar, RIGHT, buff=0.14)
        row = VGroup(label, bar, value)
        grp.add(row)
        grp.rows[ltr] = row
    return grp


def _morph_bars(scene, old, new, run_time):
    """Morph the old bar graph into the new one, pairing rows by letter (shared
    letters slide/rescale in place, dropped letters fade out, new ones fade in)."""
    anims = []
    for ltr, row in old.rows.items():
        if ltr in new.rows:
            anims.append(ReplacementTransform(row, new.rows[ltr]))
        else:
            anims.append(FadeOut(row))
    for ltr, row in new.rows.items():
        if ltr not in old.rows:
            anims.append(FadeIn(row))
    scene.play(*anims, run_time=run_time)


class Scene04(HangmanScene):
    """Greedy on 3-letter words: the montage, then the full A-walk driven by a
    sorted letter-frequency bar graph. See module docstring for the beat map."""

    def setup_scene(self):
        self.cb = chalkboard(BOARD_W, BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── small chalk builders ──────────────────────────────────────────────────
    def _blank_rules(self, n=WORD_LEN):
        total = n * BLANK_SLOT + (n - 1) * BLANK_GAP
        x0 = BLANK_CX - total / 2 + BLANK_SLOT / 2
        rules = VGroup()
        for k in range(n):
            x = x0 + k * (BLANK_SLOT + BLANK_GAP)
            rules.add(Line([x - BLANK_SLOT / 2, BLANK_Y, 0],
                           [x + BLANK_SLOT / 2, BLANK_Y, 0],
                           color=CHALK, stroke_width=BLANK_SW))
        return rules

    def _reveal_on(self, ch, rule, color=CHALK):
        L = chalk_letter(ch, height=LETTER_H, stroke_width=LETTER_SW, color=color)
        L.next_to(rule, UP, buff=LETTER_BUFF)
        L.set_x(rule.get_center()[0])
        return L

    def _miss_letter(self, ch, slot):
        L = chalk_letter(ch, height=MISS_H, stroke_width=MISS_SW, color=CHALK)
        L.move_to([self.miss_slots_x[slot], MISS_Y, 0])
        return L

    # ── finished-game card for the montage (beat a) ───────────────────────────
    def _finished_game(self, entry, center):
        """A static finished greedy game: the (possibly partial) word above its
        rules, the gallows + drawn parts, and the missed letters below — all one
        VGroup, tinted by win/loss at the call site."""
        col = LIGHT_GREEN if entry["win"] else LIGHT_RED
        board = entry["board"]
        rules = VGroup()
        letters = VGroup()
        n = len(board)
        total = n * BLANK_SLOT + (n - 1) * BLANK_GAP
        x0 = -total / 2 + BLANK_SLOT / 2
        for k, ch in enumerate(board):
            x = x0 + k * (BLANK_SLOT + BLANK_GAP)
            rule = Line([x - BLANK_SLOT / 2, 0, 0], [x + BLANK_SLOT / 2, 0, 0],
                        color=col, stroke_width=BLANK_SW)
            rules.add(rule)
            if ch != "_":
                L = chalk_letter(ch, height=LETTER_H, stroke_width=LETTER_SW,
                                 color=col)
                L.next_to(rule, UP, buff=LETTER_BUFF)
                L.set_x(x)
                letters.add(L)
        word_grp = VGroup(rules, letters)

        hang = hangman_drawing(entry["n_parts"], color=col, stroke_width=HANG_SW)
        hang.scale(0.7)
        hang.next_to(word_grp, RIGHT, buff=0.9)

        misses = VGroup(*[chalk_letter(m, height=MISS_H, stroke_width=MISS_SW,
                                       color=col) for m in entry["shown_misses"]])
        if len(misses):
            misses.arrange(RIGHT, buff=MISS_GAP)
            misses.next_to(hang, DOWN, buff=0.35)

        game = VGroup(word_grp, hang, misses)
        game.move_to(center)
        return game

    # ── setup helpers (owners noted) ──────────────────────────────────────────
    def _setup_board(self):
        """The gallows + 3 blanks that persist through the A-walk (owner: clear)."""
        self.rules = self._blank_rules()
        full = hangman_drawing(6, color=CHALK, stroke_width=HANG_SW)
        full.scale(HANG_SCALE).move_to(HANG_POS)
        self.hang_parts = list(full.parts)
        for p in self.hang_parts:
            full.remove(p)
        self.hang = full
        self.miss_n = 0
        # centre the finished 6-miss row under the gallows base
        gallows_cx = self.hang.gallows[0].get_center()[0]
        tmpl = VGroup(*[chalk_letter(c, height=MISS_H, stroke_width=MISS_SW)
                        for c in "aoeiuy"])
        tmpl.arrange(RIGHT, buff=MISS_GAP).move_to([gallows_cx, MISS_Y, 0])
        self.miss_slots_x = [m.get_center()[0] for m in tmpl]
        self.revealed = {}     # position -> revealed chalk letter

    # ══════════════════════════════════════════════════════════════════════════
    #  SUBSCENES
    # ══════════════════════════════════════════════════════════════════════════

    # a : montage of finished greedy games — win green, loss red (ROUGH)
    @subscene
    def montage(self):
        slots = [np.array([-3.2, 1.3, 0]), np.array([3.0, 1.3, 0]),
                 np.array([-3.2, -1.8, 0]), np.array([3.0, -1.8, 0])]
        games = VGroup()
        for entry, center in zip(DATA["montage"], slots):
            g = self._finished_game(entry, center)
            games.add(g)
            self.play(FadeIn(g), run_time=0.5)
        self.wait(0.6)                                            # VO
        # a second wave, reusing the slots
        self.play(FadeOut(games), run_time=0.5)
        games2 = VGroup()
        for entry, center in zip(DATA["montage"][4:], slots):
            g = self._finished_game(entry, center)
            games2.add(g)
            self.play(FadeIn(g), run_time=0.5)
        self.wait(0.6)                                            # VO
        self.play(FadeOut(games2), run_time=0.5)

    # b : clear to just the gallows + 3 blanks
    @subscene
    def clear(self):
        self._setup_board()
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.5),
                  LaggedStartMap(Create, self.rules, lag_ratio=0.6), run_time=1.6)

    # c : the sorted letter-frequency bar graph (A on top, 186)
    @subscene
    def root_bars(self):
        pairs = [(ltr, c) for ltr, c in DATA["root"]["bars"]]
        self.bars = _freq_bars(pairs)
        self.play(LaggedStartMap(FadeIn, self.bars, lag_ratio=0.1), run_time=1.4)

    # d : two A's -> _AA, morph bars to the lone BAA candidate, guess B -> win
    @subscene
    def two_a(self):
        self._reveal_pattern("_aa")
        node = self._walk_node("_aa")
        new = _freq_bars([(l, c) for l, c in node["bars"]])
        _morph_bars(self, self.bars, new, 1.0)
        self.bars = new
        # BAA is determined: reveal the B (its remaining letter) as a win (green)
        self._fill_remaining("baa", LIGHT_GREEN)
        self.play(self.rules.animate.set_color(LIGHT_GREEN), run_time=0.5)

    # e : ends in A -> __A, guess E
    @subscene
    def ends_a(self):
        self._reset_pattern()
        self._reveal_pattern("__a")
        self._update_bars("__a")

    # f : starts with A -> A__, guess E
    @subscene
    def starts_a(self):
        self._reset_pattern()
        self._reveal_pattern("a__")
        self._update_bars("a__")

    # g : lone middle A -> _A_, guess P (~1/6)
    @subscene
    def mid_a(self):
        self._reset_pattern()
        self._reveal_pattern("_a_")
        self._update_bars("_a_")

    # h : A absent -> ___, A a MISS (under gallows + head); bars -> 454, guess O
    @subscene
    def absent_o(self):
        self._reset_pattern()
        miss = self._miss_letter("a", 0)
        self.miss_n = 1
        self.play(LaggedStartMap(Create, miss, lag_ratio=0.5), run_time=0.7)
        head = self.hang_parts[0]
        self.hang.add(head)
        self.play(Create(head), run_time=0.6)
        self._update_bars("___", missed="a")

    # ── walk helpers (used by d–h) ────────────────────────────────────────────
    def _walk_node(self, board, missed=""):
        """The cached walk node matching (board, missed)."""
        for nd in DATA["walk"]:
            if nd["board"] == board and "".join(nd["missed"]) == missed:
                return nd
        raise KeyError(f"no walk node for {board!r} missed={missed!r}")

    def _reveal_pattern(self, board):
        """Chalk the revealed A's of `board` onto the blanks (hits)."""
        for p, ch in enumerate(board):
            if ch != "_":
                L = self._reveal_on(ch, self.rules[p])
                self.revealed[p] = L
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.6)

    def _reset_pattern(self):
        """Back to a clean chalk board between the (alternative) A-outcome beats:
        fade any revealed letters AND restore the rules to chalk (a win/loss beat
        may have tinted them green/red)."""
        anims = [FadeOut(VGroup(*self.revealed.values()))] if self.revealed else []
        if any(r.get_color() != CHALK for r in self.rules):
            anims.append(self.rules.animate.set_color(CHALK))
        if anims:
            self.play(*anims, run_time=0.4)
        self.revealed = {}

    def _fill_remaining(self, word, color):
        for p, ch in enumerate(word):
            if p not in self.revealed:
                L = self._reveal_on(ch, self.rules[p], color=color)
                self.revealed[p] = L
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.6)

    def _update_bars(self, board, missed=""):
        node = self._walk_node(board, missed)
        new = _freq_bars([(l, c) for l, c in node["bars"]])
        _morph_bars(self, self.bars, new, 1.0)
        self.bars = new

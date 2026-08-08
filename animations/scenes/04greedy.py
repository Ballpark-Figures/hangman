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
  i–m miss chain— O·E·I·U·Y each miss in turn (torso…leg2); bars re-sort each time
  n reveal_nth  — one word left → NTH in the blanks; text+gallows turn red (loss)
  o avg_chart   — clear; avg greedy misses by length (peak len-3 gold, →0 at 17+)
  p pirates     — a single blank A grows AT·RAT·RATE·IRATE·PIRATE·PIRATES
  q e_combos    — E's position-patterns: 6 in 3-letter words vs 156 in 12-letter
  r bring_back  — clear E-combos, bring the avg-misses chart back
  s emphasize   — highlight lengths 17–20 (guaranteed no misses)
  t words17     — all 18 length-17 words in written font
  u emphasize_i — every i turns gold (in a different place in every word)
  v guess17     — 17 blanks; guess I → fill CONSTITUTIONALITY's i's → bubble the word

Render:  render 04c --fast   (…04v)   /   render 04 sub  for the whole scene

ROUGH — first full pass; known layout details to refine later: the montage (a) is
a placeholder 4-up grid; q's 12-letter grid overflows the right edge; v's speech
bubble clips the top; bar/chart colours + win/loss tinting are unrefined.

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade/morph/
Create run_time; the montage per-game hold; the bar-morph run_times throughout.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from bpkfigures.speech_bubble import speech_bubble
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

    def _add_miss(self, letter, *, rt_write=0.7, rt_part=0.6):
        """A wrong guess: chalk `letter` in the next miss slot, then draw the next
        body part (miss #k → part k). Grows self.miss_row + self.hang."""
        miss = self._miss_letter(letter, self.miss_n)
        self.miss_row.add(miss)
        self.play(LaggedStartMap(Create, miss, lag_ratio=0.5), run_time=rt_write)
        part = self.hang_parts[self.miss_n]
        self.hang.add(part)
        self.play(Create(part), run_time=rt_part)
        self.miss_n += 1

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
        self.miss_row = VGroup()   # the wrong-guess letters chalked below

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
        self._add_miss("a")                       # miss #1 -> head
        self._update_bars("___", missed="a")

    # i : O misses -> torso (#2); bars -> 305, guess E
    @subscene
    def miss_o(self):
        self._add_miss("o")
        self._update_bars("___", missed="ao")

    # j : E misses -> arm1 (#3); bars -> 180, guess I
    @subscene
    def miss_e(self):
        self._add_miss("e")
        self._update_bars("___", missed="aoe")

    # k : I misses -> arm2 (#4); bars -> 83, guess U
    @subscene
    def miss_i(self):
        self._add_miss("i")
        self._update_bars("___", missed="aoei")

    # l : U misses -> leg1 (#5); bars -> 17, guess Y
    @subscene
    def miss_u(self):
        self._add_miss("u")
        self._update_bars("___", missed="aoeiu")

    # m : Y misses -> leg2 (#6, full hangman); the word is now determined (nth)
    @subscene
    def miss_y(self):
        self._add_miss("y")

    # n : one word left -> NTH; turn text + gallows red (the chooser wins)
    @subscene
    def reveal_nth(self):
        self.play(FadeOut(self.bars), run_time=0.4)
        self.bars = None
        for p, ch in enumerate("nth"):
            L = self._reveal_on(ch, self.rules[p])
            self.revealed[p] = L
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.5)
        board = VGroup(self.rules, self.hang, self.miss_row,
                       *self.revealed.values())
        self.play(board.animate.set_color(LIGHT_RED), run_time=0.6)

    # o : clear the game; the avg-misses-by-length chart (greedy, uniform)
    @subscene
    def avg_chart(self):
        board = VGroup(self.rules, self.hang, self.miss_row,
                       *self.revealed.values())
        self.play(FadeOut(board), run_time=0.6)
        self.revealed = {}
        self.chart = self._avg_misses_chart()
        self.play(FadeIn(self.chart.axis), FadeIn(self.chart.labels),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in self.chart.bars],
                              lag_ratio=0.05), run_time=1.8)

    # p : PIRATES chain — a single blank A grows AT·RAT·RATE·IRATE·PIRATE·PIRATES,
    #     each new letter fading out of the alphabet pool below the gallows (ROUGH)
    @subscene
    def pirates(self):
        self.play(FadeOut(self.chart), run_time=0.5)
        pool_chars = "bcdefghijklmnopqrstuvwxyz"
        alpha = VGroup(*[chalk_letter(c, height=0.42, stroke_width=3.0, color=CHALK)
                         for c in pool_chars])
        alpha.arrange(RIGHT, buff=0.28).move_to([0, -3.3, 0])
        alpha_map = dict(zip(pool_chars, alpha))
        gal = hangman_drawing(0, color=CHALK, stroke_width=HANG_SW)
        gal.scale(0.65).move_to([5.4, 1.6, 0])
        chain = [p["word"] for p in DATA["pirates_chain"]]
        word = self._spell(chain[0])
        self.play(Create(gal.gallows), FadeIn(alpha), FadeIn(word), run_time=1.2)
        used = set(chain[0])
        for nxt in chain[1:]:
            new_word = self._spell(nxt)
            newc = (set(nxt) - used).pop()
            anims = [ReplacementTransform(word, new_word)]
            if newc in alpha_map:
                anims.append(alpha_map[newc].animate.set_opacity(0.12))
            self.play(*anims, run_time=0.8)
            word, used = new_word, set(nxt)
        self.pir_grp = VGroup(gal, alpha, word)

    # q : E's letter-combinations — few in 3-letter words, many in 12-letter (ROUGH)
    @subscene
    def e_combos(self):
        self.play(FadeOut(self.pir_grp), run_time=0.5)
        ec = DATA["e_combos"]
        left = self._combo_column("3-letter words", ec["3"]["patterns"],
                                  ec["3"]["n_patterns"])
        right = self._combo_column("12-letter words", ec["12"]["patterns"],
                                   ec["12"]["n_patterns"], grid=True)
        left.move_to([-4.0, 0, 0])
        right.move_to([3.6, 0, 0])
        self.ecombo_grp = VGroup(left, right)
        self.play(FadeIn(left), run_time=0.8)
        self.play(FadeIn(right), run_time=0.8)

    # r : clear the E-combos, bring the avg-misses chart back
    @subscene
    def bring_back_chart(self):
        self.play(FadeOut(self.ecombo_grp), run_time=0.5)
        self.chart = self._avg_misses_chart()
        self.play(FadeIn(self.chart), run_time=1.0)

    # s : emphasise lengths 17–20 (guaranteed no misses) on the chart
    @subscene
    def emphasize_long(self):
        long_bars = VGroup(*[self.chart.bar_of[L] for L in (17, 18, 19, 20)
                             if L in self.chart.bar_of])
        cx = long_bars.get_center()[0]
        cy = self.chart.axis.get_y() + 0.7
        highlight(self, [(np.array([cx, cy, 0]), 2.2, 1.6)])

    # t : clear; all 18 length-17 words in written font
    @subscene
    def words17(self):
        self.play(FadeOut(self.chart), run_time=0.5)
        self.w17 = self._word_list([e["word"] for e in DATA["len17"]["words"]])
        self.play(LaggedStartMap(FadeIn, self.w17, lag_ratio=0.06), run_time=1.6)

    # u : emphasise every i (in different places in every word)
    @subscene
    def emphasize_i(self):
        eyes = VGroup(*[ch for row in self.w17 for ch in row.i_chars])
        self.play(eyes.animate.set_color(ACCENT_GOLD), run_time=1.0)

    # v : a 17-letter game — guess I, fill CONSTITUTIONALITY's i's, then the word
    @subscene
    def guess17(self):
        self.play(FadeOut(self.w17), run_time=0.5)
        word = DATA["constitutionality"]["word"]
        rules = self._blank_rules_n(len(word), slot=0.44, gap=0.16, y=0.4)
        gal = hangman_drawing(0, color=CHALK, stroke_width=HANG_SW)
        gal.scale(0.7).move_to([0, 2.6, 0])
        self.play(Create(gal.gallows),
                  LaggedStartMap(Create, rules, lag_ratio=0.4), run_time=1.6)
        # guess I: fill every i
        i_pos = DATA["constitutionality"]["i_positions"]
        eyes = VGroup()
        for p in i_pos:
            L = chalk_letter("i", height=0.5, stroke_width=LETTER_SW, color=CHALK)
            L.next_to(rules[p], UP, buff=0.1).set_x(rules[p].get_center()[0])
            eyes.add(L)
        self.play(LaggedStartMap(FadeIn, eyes, lag_ratio=0.4), run_time=1.0)
        # speech-bubble the whole word, then fill the rest
        bub = speech_bubble(word.upper(), font_size=30, tail="bottom", tail_len=0.8)
        bub.next_to(gal, UP, buff=0.2)
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.7)
        rest = VGroup()
        for p, ch in enumerate(word):
            if p in i_pos:
                continue
            L = chalk_letter(ch, height=0.5, stroke_width=LETTER_SW, color=CHALK)
            L.next_to(rules[p], UP, buff=0.1).set_x(rules[p].get_center()[0])
            rest.add(L)
        self.play(LaggedStartMap(FadeIn, rest, lag_ratio=0.08), run_time=1.2)

    # ── walk helpers (used by d–n) ────────────────────────────────────────────
    def _walk_node(self, board, missed=""):
        """The cached walk node matching (board, missed). The cache stores `missed`
        SORTED (state() normalizes it), so match on the letter SET, not order."""
        want = set(missed)
        for nd in DATA["walk"]:
            if nd["board"] == board and set(nd["missed"]) == want:
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

    # ── components for the later beats (o–v) ──────────────────────────────────
    def _avg_misses_chart(self):
        """Vertical bar chart of avg greedy misses by word length (chalk styling,
        peak length-3 in gold). Handles: .axis .bars .labels .bar_of{L:bar}."""
        data = DATA["avg_misses_by_length"]
        lengths = sorted(int(k) for k in data)
        vals = [data[str(L)]["avg_misses"] for L in lengths]
        vmax = max(vals)
        x0, x1, base_y, height = -6.5, 6.5, -3.0, 4.4
        n = len(lengths)
        slot = (x1 - x0) / n
        axis = Line([x0, base_y, 0], [x1, base_y, 0], color=CHALK, stroke_width=4)
        bars, labels, bar_of = VGroup(), VGroup(), {}
        for i, L in enumerate(lengths):
            h = max(vals[i] / vmax * height, 1e-3)
            x = x0 + (i + 0.5) * slot
            col = ACCENT_GOLD if L == 3 else ACCENT_FILL
            bar = Rectangle(width=slot * 0.78, height=h, fill_color=col,
                            fill_opacity=1.0, stroke_width=0)
            bar.move_to([x, base_y + h / 2, 0])
            bars.add(bar)
            bar_of[L] = bar
            lab = crisp_text(str(L), font_size=18, color=CHALK)
            lab.move_to([x, base_y - 0.3, 0])
            labels.add(lab)
        grp = VGroup(axis, bars, labels)
        grp.axis, grp.bars, grp.labels, grp.bar_of = axis, bars, labels, bar_of
        return grp

    def _spell(self, word, *, height=0.7, center=(0, 0.6, 0)):
        """A word spelled out in chalk letters (row), centred at `center`."""
        letters = VGroup(*[chalk_letter(c, height=height, stroke_width=LETTER_SW,
                                        color=CHALK) for c in word])
        letters.arrange(RIGHT, buff=0.18).move_to(list(center))
        return letters

    def _pattern_text(self, pattern, *, font_size=22):
        """A position-pattern like '_e_' with the e's in gold, blanks as '_'."""
        chars = VGroup(*[crisp_text(ch.upper() if ch != "_" else "_",
                                    font_size=font_size,
                                    color=ACCENT_GOLD if ch == "e" else CHALK)
                         for ch in pattern])
        chars.arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
        return chars

    def _combo_column(self, title, patterns, total, *, grid=False):
        """A titled column of E position-patterns + a total-count caption."""
        head = crisp_text(title, font_size=26, color=CHALK, weight="BOLD")
        if grid:
            cells = VGroup(*[self._pattern_text(p, font_size=18)
                             for p, _ in patterns[:24]])
            cells.arrange_in_grid(cols=4, buff=(0.4, 0.24))
        else:
            cells = VGroup(*[self._pattern_text(p) for p, _ in patterns])
            cells.arrange(DOWN, buff=0.22)
        count = crisp_text(f"{total} combinations", font_size=22, color=ACCENT_GOLD)
        return VGroup(head, cells, count).arrange(DOWN, buff=0.4)

    def _word_list(self, words, *, font_size=17):
        """The words in written (crisp) font, in a 2-column grid; each word-row
        carries an ``.i_chars`` handle (its i glyphs) for later emphasis."""
        rows = VGroup()
        for w in words:
            chars = VGroup()
            i_chars = VGroup()
            for ch in w:
                t = crisp_text(ch.upper(), font_size=font_size, color=CHALK)
                chars.add(t)
                if ch == "i":
                    i_chars.add(t)
            chars.arrange(RIGHT, buff=0.04)
            chars.i_chars = i_chars
            rows.add(chars)
        rows.arrange_in_grid(cols=2, buff=(1.0, 0.3), aligned_edge=LEFT)
        rows.move_to(ORIGIN)
        return rows

    def _blank_rules_n(self, n, *, slot, gap, y):
        total = n * slot + (n - 1) * gap
        x0 = -total / 2 + slot / 2
        rules = VGroup()
        for k in range(n):
            x = x0 + k * (slot + gap)
            rules.add(Line([x - slot / 2, y, 0], [x + slot / 2, y, 0],
                           color=CHALK, stroke_width=BLANK_SW))
        return rules

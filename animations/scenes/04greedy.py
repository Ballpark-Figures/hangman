"""SCENE 04 — the GREEDY strategy for 3-letter words, on the chalkboard.

Assume every word is equally likely; guess the letter that appears in the most
remaining candidate words (greedy). We watch a montage of finished 3-letter
games, then walk the whole greedy decision for a 3-letter word: a sorted
letter-FREQUENCY bar graph (bottom-left, vertical bars) drives every guess, the
3 blanks show the revealed pattern, and misses pile under the gallows.

The board (blanks LEFT, gallows RIGHT, miss row centred under the gallows, speech
bubble from the left edge) is the SHARED `assets.game_board` (gb) used by 02/94.
All numbers are SOURCED from `assets/greedy_data.py` (committed cache); the render
reads only the cache.

Script row 04, split on '—' → 22 beats a–v (voiceover ↔ animation zip 1:1):
  a montage     — finished greedy 3-letter games, one at a time; win green, loss red
  b clear       — clear the last game, leaving the gallows + 3 blanks
  c root_bars   — freq bar graph, 3-letter words, sorted by # appearances (A=186/640)
  d two_a       — _AA → the lone BAA; fill B → whole word + gallows turn green
  e ends_a      — __A, bars→13 A-enders → E ;  f starts_a — A__ → E
  g mid_a       — _A_ → P (~1/6) ;  h absent_o — A missed (head); bars→454 → O (~1/3)
  i–m miss chain— O·E·I·U·Y each miss (torso…leg2); bars re-sort each time
  n reveal_nth  — one word left → NTH; text + gallows turn red (loss)
  o avg_chart   — clear; avg greedy misses by length (light bars, y-axis, →0 at 17+)
  p pirates     — single blank A grows AT·RAT·RATE·IRATE·PIRATE·PIRATES, in place
  q e_combos    — E's patterns on blanks (written font): 6 (3-letter) vs 156 (12-letter)
  r bring_back  — clear E-combos, bring the avg chart back
  s emphasize   — emphasise the 17–20 numbers (guaranteed no misses)
  t words17     — all 18 length-17 words in the written (chalk) font, equal-width grid
  u emphasize_i — every i turns gold (a different place in every word)
  v guess17     — 17 blanks; guess I → fill CONSTITUTIONALITY's i's → bubble the word

Render:  render 04c --fast   (…04v)   /   render 04 sub  for the whole scene

TIMING KNOBS LEFT AT A GUESS (feel — judge from the video): every fade/morph/
Create run_time; the montage per-game hold; the bar-morph run_times throughout.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import chalkboard, chalk_letter, CHALK
from assets import game_board as gb
from assets import greedy_data

DATA = greedy_data.get()

# ── frequency bar graph (bottom-left, VERTICAL bars, light palette) ───────────
FBARS_LEFT = -6.5          # x of the first bar's centre column (inside the board)
FBARS_BASE = -2.9          # baseline y (x-axis) — well clear of the bottom edge
FBARS_W    = 6.6           # total width across `FBARS_TOP` columns
FBARS_H    = 2.3           # height of the tallest bar
FBARS_TOP  = 10            # letters shown
FBAR_COLOR = LIGHT_BLUE    # light palette — reads on the navy board
FBAR_HL    = ACCENT_GOLD   # greedy's pick (the guessed letter)

# avg-misses chart (beat o) — a lighter single colour, no special peak
CHART_COLOR = LIGHT_BLUE


def _vbars(pairs, *, top=FBARS_TOP, hl_letter=None, scale_max=None):
    """A sorted VERTICAL letter-frequency bar graph, bottom-left. `pairs` =
    [(letter, count)] sorted descending. Returns a VGroup with ``.cols`` =
    {letter: VGroup(bar, label, value)} so a later beat can morph column-by-column
    as the candidate set narrows. `hl_letter` (default: the tallest = greedy's
    pick) is drawn in FBAR_HL. Bars normalise to `scale_max` (default: this call's
    own max)."""
    shown = pairs[:top]
    if scale_max is None:
        scale_max = max((c for _, c in shown), default=1)
    if hl_letter is None and shown:
        hl_letter = shown[0][0]
    slot = FBARS_W / top
    grp = VGroup()
    grp.cols = {}
    for i, (ltr, count) in enumerate(shown):
        x = FBARS_LEFT + (i + 0.5) * slot
        h = max(count / scale_max * FBARS_H, 1e-3)
        col = FBAR_HL if ltr == hl_letter else FBAR_COLOR
        bar = Rectangle(width=slot * 0.68, height=h, fill_color=col,
                        fill_opacity=1.0, stroke_width=0)
        bar.move_to([x, FBARS_BASE + h / 2, 0])
        label = chalk_letter(ltr, height=0.30, stroke_width=3.0, color=CHALK)
        label.move_to([x, FBARS_BASE - 0.34, 0])
        value = crisp_text(str(count), font_size=16, color=CHALK)
        value.next_to(bar, UP, buff=0.08)
        col_grp = VGroup(bar, label, value)
        grp.add(col_grp)
        grp.cols[ltr] = col_grp
    return grp


def _chalk_phrase(text, *, height=0.4, stroke_width=3.2, buff=0.10, space=0.34,
                  color=CHALK):
    """A phrase written in the chalk (written) font — one row of `chalk_letter`s,
    left→right, spaces as gaps. `chalk_letter` is CAPITALS-ONLY, so the phrase
    renders all-caps. Returns a VGroup whose submobjects are the letters."""
    grp = VGroup()
    x = 0.0
    for ch in text.upper():
        if ch == " ":
            x += space
            continue
        L = chalk_letter(ch, height=height, stroke_width=stroke_width, color=color)
        L.move_to([x + L.width / 2, 0, 0])
        grp.add(L)
        x += L.width + buff
    grp.move_to(ORIGIN)
    return grp


def _morph_vbars(scene, old, new, run_time):
    """Morph one vertical bar graph into the next, pairing columns by letter."""
    anims = []
    for ltr, col in old.cols.items():
        if ltr in new.cols:
            anims.append(ReplacementTransform(col, new.cols[ltr]))
        else:
            anims.append(FadeOut(col))
    for ltr, col in new.cols.items():
        if ltr not in old.cols:
            anims.append(FadeIn(col))
    scene.play(*anims, run_time=run_time)


class Scene04(HangmanScene):
    """Greedy on 3-letter words, on the shared game board. See module docstring."""

    def setup_scene(self):
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-10)
        self.add(self.cb)

    # ── the shared board (owner: montage) ─────────────────────────────────────
    def _setup_board(self):
        self.rules = gb.build_rules(3)
        self.hang, self.hang_parts = gb.build_gallows()
        self.miss_n = 0
        self.miss_row = VGroup()
        self.miss_slots_x = gb.miss_slots(self.hang, "aoeiuy")   # the A-walk loss
        self.revealed = {}     # position -> revealed chalk letter (A-walk)

    # ══════════════════════════════════════════════════════════════════════════
    #  a–b : montage + settle
    # ══════════════════════════════════════════════════════════════════════════

    def _show_game(self, entry):
        """Fill the fixed board with one finished greedy game, tinted by result."""
        col = LIGHT_GREEN if entry["win"] else LIGHT_RED
        letters = VGroup()
        for p, ch in enumerate(entry["board"]):
            if ch != "_":
                letters.add(gb.reveal_letter(ch, self.rules[p], color=col))
        slots = gb.miss_slots(self.hang, entry["shown_misses"])
        misses = VGroup(*[gb.miss_letter(m, slots[i], color=col)
                          for i, m in enumerate(entry["shown_misses"])])
        parts = self.hang_parts[:entry["n_parts"]]
        for p in parts:
            p.set_color(col)
            self.hang.add(p)
        self._game = VGroup(letters, misses)
        self._game_parts = parts
        self.play(FadeIn(letters), FadeIn(misses), *[FadeIn(p) for p in parts],
                  self.rules.animate.set_color(col),
                  self.hang.gallows.animate.set_color(col), run_time=0.5)

    def _clear_game(self, run_time=0.4):
        self.play(FadeOut(self._game), *[FadeOut(p) for p in self._game_parts],
                  self.rules.animate.set_color(CHALK),
                  self.hang.gallows.animate.set_color(CHALK), run_time=run_time)
        for p in self._game_parts:
            self.hang.remove(p)

    # a : the montage — finished greedy games, one at a time (win green / loss red)
    @subscene
    def montage(self):
        self._setup_board()
        # draw the blanks, THEN the gallows (not together — like scene 02)
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=0.8), run_time=2.0)
        self.play(LaggedStartMap(Create, self.hang.gallows, lag_ratio=0.6),
                  run_time=1.6)
        games = DATA["montage"]
        for i, entry in enumerate(games):
            self._show_game(entry)
            self.wait(0.5)                                       # VO
            if i < len(games) - 1:
                self._clear_game()

    # b : clear the last game, leaving the gallows + 3 blanks (already in place)
    @subscene
    def clear(self):
        self._clear_game(run_time=0.5)

    # ══════════════════════════════════════════════════════════════════════════
    #  c–n : the greedy A-walk, driven by the frequency bar graph
    # ══════════════════════════════════════════════════════════════════════════

    # c : the sorted letter-frequency bar graph (A on top, 186)
    @subscene
    def root_bars(self):
        self.bars = _vbars(DATA["root"]["bars"])
        self.play(LaggedStartMap(FadeIn, self.bars, lag_ratio=0.08), run_time=1.4)

    # d : two A's -> _AA -> the lone BAA; whole word + gallows turn green (win)
    @subscene
    def two_a(self):
        self._reveal_pattern("_aa")
        self._update_bars("_aa")
        L = gb.reveal_letter("b", self.rules[0])
        self.revealed[0] = L
        self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.7)
        won = VGroup(self.rules, self.hang, *self.revealed.values())
        self.play(won.animate.set_color(LIGHT_GREEN), run_time=0.6)   # win: all green

    # e : ends in A -> __A, guess E ;  f : starts with A -> A__, guess E
    @subscene
    def ends_a(self):
        self._reset_pattern()
        self._reveal_pattern("__a")
        self._update_bars("__a")

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

    # i–m : the miss chain — O E I U Y each miss in turn, re-sorting the bars
    @subscene
    def miss_o(self):
        self._add_miss("o")
        self._update_bars("___", missed="ao")

    @subscene
    def miss_e(self):
        self._add_miss("e")
        self._update_bars("___", missed="aoe")

    @subscene
    def miss_i(self):
        self._add_miss("i")
        self._update_bars("___", missed="aoei")

    @subscene
    def miss_u(self):
        self._add_miss("u")
        self._update_bars("___", missed="aoeiu")

    # m : Y misses (full hangman); the word is now determined — collapse the bars
    @subscene
    def miss_y(self):
        self._add_miss("y")
        self._update_bars("___", missed="aoeiuy")

    # n : one word left -> NTH; turn text + gallows red (the chooser wins)
    @subscene
    def reveal_nth(self):
        self.play(FadeOut(self.bars), run_time=0.4)
        self.bars = None
        for p, ch in enumerate("nth"):
            L = gb.reveal_letter(ch, self.rules[p])
            self.revealed[p] = L
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.5)
        lost = VGroup(self.rules, self.hang, self.miss_row, *self.revealed.values())
        self.play(lost.animate.set_color(LIGHT_RED), run_time=0.6)

    # ══════════════════════════════════════════════════════════════════════════
    #  o–v : the by-length chart, PIRATES, E-combos, the length-17 story
    # ══════════════════════════════════════════════════════════════════════════

    # o : clear the game; the avg-misses-by-length chart (light bars, y-axis)
    @subscene
    def avg_chart(self):
        board = VGroup(self.rules, self.hang, self.miss_row,
                       *self.revealed.values())
        self.play(FadeOut(board), run_time=0.6)
        self.revealed = {}
        self.chart = self._avg_chart()
        self._write_letters(self.chart.title, run_time=2.6)     # write the title on
        self.play(FadeIn(self.chart.axes), FadeIn(self.chart.labels),
                  FadeIn(self.chart.yticks),
                  LaggedStart(*[GrowFromEdge(b, DOWN) for b in self.chart.bars],
                              lag_ratio=0.04), run_time=1.8)

    # p : the PIRATES chain — a single blank A grows in place, used letters fading
    @subscene
    def pirates(self):
        self.play(FadeOut(self.chart), run_time=0.5)
        gal, _ = gb.build_gallows()
        # the whole alphabet, in rows UNDER the gallows; A starts already faded
        # (it's the letter we begin the word with)
        pool_chars = "abcdefghijklmnopqrstuvwxyz"
        alpha_letters = [chalk_letter(c, height=0.30, stroke_width=3.0, color=CHALK)
                         for c in pool_chars]
        alpha = VGroup(*alpha_letters)
        alpha.arrange_in_grid(cols=9, buff=(0.24, 0.20))
        alpha.next_to(gal.gallows.get_bottom(), DOWN, buff=0.3)
        alpha.set_x(gal.gallows.get_center()[0])
        alpha_map = dict(zip(pool_chars, alpha_letters))
        alpha_map["a"].set_stroke(opacity=0.15)              # A is used from the start
        self.play(LaggedStartMap(Create, gal.gallows, lag_ratio=0.5),
                  FadeIn(alpha), run_time=1.2)

        chain = [p["word"] for p in DATA["pirates_chain"]]   # a, at, …, pirates
        spacing = gb.BLANK_SLOT + gb.BLANK_GAP
        xs = [gb.BLANK_CX]                                   # current letter x's L→R
        cell0 = self._blank_with("a", gb.BLANK_CX)           # A starts on its blank
        board = VGroup(cell0)
        self.play(Create(cell0[0]), run_time=0.3)            # the blank
        self._write_letters([cell0[1]], run_time=0.5)        # write the A
        prev = "a"
        for nxt in chain[1:]:
            if nxt[1:] == prev:                              # inserted at the START
                newc, x = nxt[0], xs[0] - spacing
                xs.insert(0, x)
            else:                                            # inserted at the END
                newc, x = nxt[-1], xs[-1] + spacing
                xs.append(x)
            cell = self._blank_with(newc, x)                 # in place — nothing moves
            board.add(cell)
            self.play(Create(cell[0]),
                      alpha_map[newc].animate.set_stroke(opacity=0.15), run_time=0.35)
            self._write_letters([cell[1]], run_time=0.5)     # write the new letter
            prev = nxt
        self.pir_grp = VGroup(gal, alpha, board)

    # q : E's letter-combinations on blanks (written font) — 6 vs 156
    @subscene
    def e_combos(self):
        self.play(FadeOut(self.pir_grp), run_time=0.5)
        ec = DATA["e_combos"]
        left = VGroup(*[self._mini_board(p, slot=0.32, gap=0.10, height=0.44)
                        for p, _ in ec["3"]["patterns"]])
        left.arrange(DOWN, buff=0.32)
        right = VGroup(*[self._mini_board(p, slot=0.14, gap=0.045, height=0.26)
                         for p, _ in ec["12"]["patterns"]])
        right.arrange_in_grid(rows=26, cols=6, buff=(0.32, 0.13))   # 26×6 = 156
        right.scale(min(9.4 / right.width, 7.5 / right.height, 1.0))
        right.move_to([1.9, 0, 0])
        # the 3-letter column sits halfway between the board's left inner edge and
        # the left end of the 12-letter grid
        board_left = -(gb.BOARD_W / 2 - 0.34)
        left.move_to([(board_left + right.get_left()[0]) / 2, 0, 0])
        self.ecombo_grp = VGroup(left, right)
        self.play(FadeIn(left), run_time=0.7)
        self.play(FadeIn(right), run_time=0.9)

    # r : clear the E-combos, bring the avg-misses chart back
    @subscene
    def bring_back_chart(self):
        self.play(FadeOut(self.ecombo_grp), run_time=0.5)
        self.chart = self._avg_chart()
        self.play(FadeIn(self.chart), run_time=1.0)

    # s : draw a yellow box around the 17–20 numbers (guaranteed no misses)
    @subscene
    def emphasize_long(self):
        grp = VGroup(*[self.chart.bar_of[L] for L in (17, 18, 19, 20)],
                     *[self.chart.label_of[L] for L in (17, 18, 19, 20)])
        self.long_box = SurroundingRectangle(grp, color=ACCENT_GOLD, buff=0.18,
                                             stroke_width=4)
        self.play(Create(self.long_box), run_time=0.9)

    # t : all 18 length-17 words in the written (chalk) font, equal-width grid
    @subscene
    def words17(self):
        self.play(FadeOut(self.chart), FadeOut(self.long_box), run_time=0.5)
        self.w17 = self._word_grid([e["word"] for e in DATA["len17"]["words"]])
        self.play(LaggedStartMap(FadeIn, self.w17, lag_ratio=0.05), run_time=1.6)

    # u : emphasise every i (a different place in every word)
    @subscene
    def emphasize_i(self):
        eyes = VGroup(*[ch for row in self.w17 for ch in row.i_chars])
        self.play(eyes.animate.set_color(ACCENT_GOLD), run_time=1.0)

    # v : a 17-letter game (INDISTINGUISHABLE) — guess I (bubble → write), then
    #     guess the whole word; every letter is WRITTEN one at a time
    @subscene
    def guess17(self):
        self.play(FadeOut(self.w17), run_time=0.5)
        word = DATA["demo17"]["word"]
        gal, _ = gb.build_gallows()
        # centre the blanks between the board's left inner edge and the gallows
        board_left = -(gb.BOARD_W / 2 - 0.34)
        cx = (board_left + gal.gallows.get_left()[0]) / 2
        rules = gb.build_rules(len(word), slot=0.40, gap=0.10, cx=cx)
        self.play(LaggedStartMap(Create, gal.gallows, lag_ratio=0.5), run_time=1.2)
        self.play(LaggedStartMap(Create, rules, lag_ratio=1.0), run_time=2.6)  # one at a time
        i_pos = DATA["demo17"]["i_positions"]
        # guess I: bubble, THEN write every i (one at a time)
        ibub = gb.bubble("i", tail="left")
        self.play(GrowFromPoint(ibub, ibub.tip_dot.get_center()), run_time=0.6)
        self._write_letters([gb.reveal_letter("i", rules[p]) for p in i_pos],
                            run_time=1.8)
        self.play(FadeOut(ibub), run_time=0.4)
        # guess the whole word: bubble the word, then write the rest one at a time (fast)
        wbub = gb.bubble(word.upper(), tail="left", font_size=30)
        self.play(GrowFromPoint(wbub, wbub.tip_dot.get_center()), run_time=0.7)
        self._write_letters([gb.reveal_letter(ch, rules[p])
                             for p, ch in enumerate(word) if p not in i_pos],
                            run_time=3.2)
        self.play(FadeOut(wbub), run_time=0.4)

    # ── A-walk helpers (c–n) ──────────────────────────────────────────────────
    def _add_miss(self, letter, *, rt_write=0.7, rt_part=0.6):
        L = gb.miss_letter(letter, self.miss_slots_x[self.miss_n])
        self.miss_row.add(L)
        self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=rt_write)
        part = self.hang_parts[self.miss_n]
        part.set_color(CHALK)            # reset any leftover montage tint (a)
        self.hang.add(part)
        self.play(Create(part), run_time=rt_part)
        self.miss_n += 1

    def _write_letters(self, letters, *, run_time, lag=1.0):
        """WRITE chalk letters on as strokes (Create), ONE STROKE AT A TIME — the
        hand-written look, simulating a person writing on the board (no two strokes,
        hence no two letters, drawn at once). `lag=1.0` = a stroke finishes before
        the next begins; `letters` is an iterable of chalk_letter VGroups."""
        strokes = VGroup(*[s for L in letters for s in L])
        self.play(LaggedStartMap(Create, strokes, lag_ratio=lag), run_time=run_time)

    def _walk_node(self, board, missed=""):
        want = set(missed)
        for nd in DATA["walk"]:
            if nd["board"] == board and set(nd["missed"]) == want:
                return nd
        raise KeyError(f"no walk node for {board!r} missed={missed!r}")

    def _reveal_pattern(self, board):
        for p, ch in enumerate(board):
            if ch != "_":
                L = gb.reveal_letter(ch, self.rules[p])
                self.revealed[p] = L
                self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.6)

    def _reset_pattern(self):
        """Clean chalk board between the (alternative) A-outcome beats: fade the
        revealed letters and restore rules + gallows to chalk (a win tinted them)."""
        anims = [FadeOut(VGroup(*self.revealed.values()))] if self.revealed else []
        if any(r.get_color() != CHALK for r in self.rules):
            anims.append(self.rules.animate.set_color(CHALK))
            anims.append(self.hang.animate.set_color(CHALK))
        if anims:
            self.play(*anims, run_time=0.4)
        self.revealed = {}

    def _update_bars(self, board, missed=""):
        node = self._walk_node(board, missed)
        new = _vbars(node["bars"])
        _morph_vbars(self, self.bars, new, 1.0)
        self.bars = new

    # ── components for o–v ────────────────────────────────────────────────────
    def _avg_chart(self):
        """Vertical bar chart of avg greedy misses by word length — one light
        colour (no special peak) + a y-axis with ticks. Handles: .axes .bars
        .labels .yticks .bar_of{L} .label_of{L}."""
        data = DATA["avg_misses_by_length"]
        lengths = sorted(int(k) for k in data)
        vals = [data[str(L)]["avg_misses"] for L in lengths]
        x0, x1, base, height, ytop = -6.0, 6.0, -3.2, 4.5, 7   # plot centred at x=0
        n = len(lengths)
        slot = (x1 - x0) / n
        xaxis = Line([x0, base, 0], [x1, base, 0], color=CHALK, stroke_width=3)
        yaxis = Line([x0, base, 0], [x0, base + height, 0], color=CHALK,
                     stroke_width=3)
        bars, labels, bar_of, label_of = VGroup(), VGroup(), {}, {}
        for i, L in enumerate(lengths):
            h = max(vals[i] / ytop * height, 1e-3)
            x = x0 + (i + 0.5) * slot
            bar = Rectangle(width=slot * 0.75, height=h, fill_color=CHART_COLOR,
                            fill_opacity=1.0, stroke_width=0)
            bar.move_to([x, base + h / 2, 0])
            bars.add(bar)
            bar_of[L] = bar
            lab = crisp_text(str(L), font_size=17, color=CHALK)
            lab.move_to([x, base - 0.3, 0])
            labels.add(lab)
            label_of[L] = lab
        yticks = VGroup()
        for t in range(0, ytop + 1, 2):
            y = base + t / ytop * height
            tick = Line([x0 - 0.12, y, 0], [x0, y, 0], color=CHALK, stroke_width=2)
            tl = crisp_text(str(t), font_size=15, color=CHALK)
            tl.next_to(tick, LEFT, buff=0.1)
            yticks.add(tick, tl)
        # title in the written (chalk) font — one row, centred over the plot
        # (chalk is capitals-only, so it reads ALL-CAPS)
        title = _chalk_phrase("Average Misses by Word Length", height=0.38)
        title.move_to([(x0 + x1) / 2, base + height + 0.7, 0])
        grp = VGroup(xaxis, yaxis, bars, labels, yticks, title)
        grp.axes = VGroup(xaxis, yaxis)
        grp.bars, grp.labels, grp.yticks, grp.title = bars, labels, yticks, title
        grp.bar_of, grp.label_of = bar_of, label_of
        return grp

    def _blank_with(self, ch, x, *, y=None):
        """One blank rule at x with a chalk letter written above it (for PIRATES)."""
        y = gb.BLANK_Y if y is None else y
        rule = Line([x - gb.BLANK_SLOT / 2, y, 0], [x + gb.BLANK_SLOT / 2, y, 0],
                    color=CHALK, stroke_width=gb.BLANK_SW)
        L = gb.reveal_letter(ch, rule)
        return VGroup(rule, L)

    def _mini_board(self, pattern, *, slot=0.12, gap=0.04, height=0.20):
        """A small blanked board for one position-pattern: rules per slot, the
        pattern's letters written on (chalk / written font). Centred at origin."""
        n = len(pattern)
        total = n * slot + (n - 1) * gap
        x0 = -total / 2 + slot / 2
        grp = VGroup()
        for k, ch in enumerate(pattern):
            x = x0 + k * (slot + gap)
            grp.add(Line([x - slot / 2, 0, 0], [x + slot / 2, 0, 0],
                         color=CHALK, stroke_width=2.0))
            if ch != "_":
                L = chalk_letter(ch, height=height, stroke_width=2.0, color=CHALK)
                L.next_to([x, 0, 0], UP, buff=0.03).set_x(x)
                grp.add(L)
        return grp

    def _word_grid(self, words, *, cell_w=0.32, height=0.34):
        """The words in the written (chalk) font, monospaced so every word is the
        same width, in a 2-column grid. Each row carries `.i_chars` (its i glyphs)."""
        rows = VGroup()
        for w in words:
            row = VGroup()
            row.i_chars = VGroup()
            for j, ch in enumerate(w):
                L = chalk_letter(ch, height=height, stroke_width=2.4, color=CHALK)
                L.move_to([j * cell_w, 0, 0])
                row.add(L)
                if ch == "i":
                    row.i_chars.add(L)
            rows.add(row)
        rows.arrange_in_grid(cols=2, buff=(0.9, 0.34), aligned_edge=LEFT)
        rows.move_to(ORIGIN)
        return rows

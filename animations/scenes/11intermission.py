"""SCENE 11 — the intermission (the shift from pattern-hunting to word-hunting).

Two halves on a NAVY background:
  • beats a–d: a PIE that partitions all 34,483 words by how the top-3-tier "backbone"
    opening (A E I N O R S T) resolves them — the sections fan in ONE AT A TIME
    (pie_chart.fan_sectors): only-tier words → uniquely-pinned → the rest of the 0-miss
    words → then the 1/2/3-miss tail all at once. Numbers SOURCED from
    `assets/scene11_data` (the committed `scene11_cache.json`, produced by
    `math/tier_backbone.py` — an OPTIMAL-strategy computation).
  • beats e–h: the wooden CHALKBOARD slides back in (the REVERSE of scene 04/01's
    board→navy dissolve — its navy slate == this scene's navy bg, so it just contracts
    out of the full frame while the frame slides in), with 7 blanks near the BOTTOM, a
    gallows, and "WORDS REMAINING: 5541" across the top. FIGURES is played out (sourced
    trace: e·s·i hit, p·t miss, g·f·u·r hit — 2 misses): first up to & incl. the I with
    the count ticking down (5541→1166→231→21), then the count is erased, the 21 remaining
    words are written out, and the rest of the game crosses them off. Then the chalkboard
    is removed to a blank frame.

Reuse: `assets.game_board` (gb) for the board/blanks/gallows/guessing (canonical
gameplay layout, as 02/04/94); `bpkfigures.pie_chart` for the fanning pie; the navy
bg follows scene 08.

The pie is titled "After High Tier Letters" and split into 5 LABELLED sections (name +
%), the ≥2-miss tail collapsed into one; sections fan in one at a time (b/c, then "No
more misses"), then "1 more miss" + "2+ more misses" fan out TOGETHER from one origin.

BEAT MAP
  a to_navy     — turn the background navy (scene-08 `_navy` rect)
  b only_tier   — title + "Word Finished" section (only backbone letters)
  c single_opt  — "Word Known" section (narrowed to a single option)
  d miss_dist   — "No more misses", then "1 more miss" + "2+ more misses" (fan_group)
  e chalk_in    — chalkboard reverse-in; blanks (bottom); gallows; WORDS REMAINING: 5541
  f figures     — play FIGURES up to & incl. the I (e·s·i); count ticks 5541→1166→231→21
  g figures_words — erase count; write the 21 remaining words; play the rest crossing off
  h chalk_out   — remove the chalkboard (ends blank, next scene is animated)

STATUS — ROUGH first pass, TIMING + PIE LAYOUT are guesses (judge from the video):
  • The pie proportions/labels are unverified until `scene11_cache.json` exists
    (run `math/tier_backbone.py`); sector COLOURS (good→bad green→red) + inside-%
    labels are placeholders to tune against the real distribution.
  • Beat e is the TRANSITION SEAM (the risky part, per our transition rule) — feel is
    unverified; judge the board-contract timing from the video.
  • The FIGURES trace uses the committed L7 tree (the ~0.5% suboptimal one — see
    scene11_data's caveat); it still wins.

Render:  render 11a --fast (…11g)  /  render 11 sub  for the whole scene
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config import *
from assets.chalkboard import chalkboard, chalk_phrase, chalk_number, BOARD_NAVY, CHALK
from assets import game_board as gb
from assets import scene11_data
from bpkfigures.pie_chart import get_pie_chart

PIE_R = 2.2                     # pie radius (room above for the title, around for labels)
PIE_CENTER = [0.0, -0.35, 0.0]  # nudged down so the title clears the top slice's label
SCALE_UP = 5.0                  # chalkboard scale at which its slate fills the frame

# ── chalkboard-game layout (beats e–h) ───────────────────────────────────────
BLANK_BOTTOM_Y = -3.0           # the 7 blanks sit near the BOTTOM, centred
COUNT_Y = 3.35                  # "WORDS REMAINING:" row across the top
COUNT_X0 = -7.1                 # left edge of the count label
COUNT_H = 0.40                  # chalk height of the count text/numbers
GRID_CENTER = [-1.3, 0.35, 0]   # centre of the remaining-words grid (left of the gallows)
GRID_COLS = 3
GRID_CW, GRID_RH = 2.7, 0.62    # grid column / row spacing
GRID_H = 0.32                   # chalk height of a grid word
                                # (matches scene 04's board→navy dissolve, reversed)

# Sector colours: a good→bad sequence. The three 0-miss sub-sections are green
# (backbone resolves the word cleanly), the miss tail ramps gold→red as misses grow.
# PLACEHOLDER scheme — tune once the real distribution is in scene11_cache.json.
ZERO_MISS_GREENS = [ACCENT_GREEN,
                    interpolate_color(ACCENT_GREEN, WHITE, 0.30),
                    interpolate_color(ACCENT_GREEN, WHITE, 0.55)]


class Scene11(HangmanScene):
    """The intermission. See the module docstring for the beat map."""

    def setup_scene(self):
        self.data = scene11_data.get()             # {"dist": …, "figures": …} (cached)
        self.navy_rect = None
        self.pie = None
        self.pie_title = None
        self.cb = None
        self.rules = self.hang = self.hang_parts = None
        self.miss_slots_x = None
        self.miss_n = 0

    # ── helpers ───────────────────────────────────────────────────────────────
    def _navy(self):
        r = Rectangle(width=config.frame_width, height=config.frame_height,
                      fill_color=BOARD_NAVY, fill_opacity=1.0, stroke_width=0)
        r.set_z_index(-10)
        return r

    def _sections(self, dist):
        """The 5 pie sections (values, colours, headings) in reveal order. The whole
        ≥2-miss tail is collapsed into one "2+ more misses" section so the pie reads as
        five labelled categories that sum to 100%:
          Word Finished  — the word uses ONLY backbone letters (revealed outright)
          Word Known     — uniquely pinned by the backbone pattern (0 more misses)
          No more misses — solvable with 0 additional misses, not yet known
          1 more miss    — exactly one additional miss
          2+ more misses — two or more additional misses (the tail)."""
        md = dist["miss_dist"]
        maxm = dist["max_misses"]
        two_plus = sum(int(md[str(k)]) for k in range(2, maxm + 1))
        headings = ["Word Finished", "Word Known", "No more misses",
                    "1 more miss", "2+ more misses"]
        values = [dist["only_tier"], dist["single_option"], dist["rest_zero_miss"],
                  int(md["1"]), two_plus]
        colors = [*ZERO_MISS_GREENS, ACCENT_GOLD, ACCENT_RED]
        return values, colors, headings

    def _setup_pie(self):
        dist = self.data["dist"]
        if dist is None:
            raise RuntimeError("scene11_cache.json missing — run `python3 "
                               "math/tier_backbone.py` to source the pie numbers.")
        values, colors, headings = self._sections(dist)
        self.pie = get_pie_chart(values, colors=colors, labels=headings,
                                 radius=PIE_R, center=PIE_CENTER, label_mode="callout",
                                 show_percent=True, label_color=WHITE,
                                 label_font_size=22, label_buff=0.25, stroke_color=WHITE)
        self.pie.hide_all()                        # incremental build across b/c/d
        self.add(self.pie)
        self.pie_title = crisp_text("After High Tier Letters", font_size=34,
                                    color=WHITE, weight=BOLD)
        self.pie_title.move_to([PIE_CENTER[0], PIE_CENTER[1] + PIE_R + 1.4, 0])

    def _setup_board(self):
        """Chalkboard SCALED UP (its navy slate fills the frame == the navy bg), plus the
        7 blanks (near the BOTTOM, centred) and the gallows. The count header + word grid
        are built in their beats. Also records the phase cut (guesses up to & incl. I)."""
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-9)                    # above the navy rect, below the chalk
        self.cb.scale(SCALE_UP, about_point=ORIGIN)   # slate fills frame, frame off-screen
        fig = self.data["figures"]
        if fig is None:
            raise RuntimeError("scene11_figures_cache.json missing — run "
                               "`python3 assets/scene11_data.py`.")
        self.rules = gb.build_rules(len(fig["word"]), cx=0.0, y=BLANK_BOTTOM_Y)
        self.hang, self.hang_parts = gb.build_gallows()
        misses = "".join(g["letter"] for g in fig["guesses"] if not g["hit"])
        self.miss_slots_x = gb.miss_slots(self.hang, misses)
        self.miss_n = 0
        self.i_cut = [g["letter"] for g in fig["guesses"]].index("i") + 1  # e·s·i
        self.count_group = VGroup()                # label + numbers + strikes (fade as one)
        self.count_nums = []                       # the running counts, left→right
        self.word_cells = {}                       # remaining word → its chalk mobject

    @staticmethod
    def _strokes(mob):
        """Leaf chalk strokes of a phrase/number/word, for stroke-by-stroke Create."""
        return mob.family_members_with_points()

    def _write(self, mob, run_time, *, lag=1.0):
        """Draw a chalk mobject ONE STROKE AT A TIME — a single hand (CLAUDE.md)."""
        self.play(LaggedStartMap(Create, VGroup(*self._strokes(mob)), lag_ratio=lag),
                  run_time=run_time)

    def _guess(self, letter, hit, run_time):
        """Canonical guess: bubble from the left → WRITE (fill each blank on a HIT / miss
        row + the next gallows part on a MISS) → dismiss the bubble. Scales with run_time."""
        r = run_time
        bub = gb.bubble(letter, tail="left")
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.5 * r)
        if hit:
            word = self.data["figures"]["word"]
            Ls = [gb.reveal_letter(letter, self.rules[p])
                  for p, c in enumerate(word) if c == letter]
            self._write(VGroup(*Ls), 0.9 * r)      # each blank's letter, one at a time
        else:
            L = gb.miss_letter(letter, self.miss_slots_x[self.miss_n])
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.6 * r)
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            self.play(Create(part), run_time=0.5 * r)
            self.miss_n += 1
        self.play(FadeOut(bub), run_time=0.3 * r)

    def _draw_count(self, run_time):
        """'WORDS REMAINING:' + the initial count (# of 7-letter words) across the top."""
        label = chalk_phrase("WORDS REMAINING:", height=COUNT_H)
        label.move_to([COUNT_X0, COUNT_Y, 0], aligned_edge=LEFT)
        n0 = chalk_number(self.data["figures"]["total"], height=COUNT_H)
        n0.next_to(label, RIGHT, buff=0.45)
        self.count_nums = [n0]
        self.count_group.add(label, n0)
        self._write(VGroup(label, n0), run_time)

    def _update_count(self, new_count, run_time):
        """Strike the current count and write the new one to its RIGHT — the countdown
        trail 5541 → 1166 → 231 → 21."""
        cur = self.count_nums[-1]
        strike = Line(cur.get_left(), cur.get_right(), color=CHALK,
                      stroke_width=4).set_z_index(1)
        new = chalk_number(new_count, height=COUNT_H).next_to(cur, RIGHT, buff=0.5)
        self.count_nums.append(new)
        self.count_group.add(strike, new)
        self.play(Create(strike), run_time=0.4 * run_time)
        self._write(new, 0.6 * run_time)

    def _word_grid(self, words):
        """Lay the remaining `words` into a chalk grid left of the gallows; fills
        `self.word_cells` (word → mobject) for the cross-offs. Returns the VGroup."""
        cols, n = GRID_COLS, len(words)
        rows = (n + cols - 1) // cols
        x0 = GRID_CENTER[0] - (cols - 1) / 2 * GRID_CW
        y0 = GRID_CENTER[1] + (rows - 1) / 2 * GRID_RH
        grid = VGroup()
        for k, w in enumerate(words):
            r_, c_ = divmod(k, cols)
            cell = chalk_phrase(w.upper(), height=GRID_H)
            cell.move_to([x0 + c_ * GRID_CW, y0 - r_ * GRID_RH, 0])
            self.word_cells[w] = cell
            grid.add(cell)
        return grid

    def _cross_off(self, words, run_time):
        """Strike through each of `words` in the grid (a chalk line, one at a time)."""
        strikes = VGroup(*[Line(self.word_cells[w].get_left(), self.word_cells[w].get_right(),
                                color=CHALK, stroke_width=3).set_z_index(1)
                           for w in words if w in self.word_cells])
        if len(strikes):
            self.play(LaggedStartMap(Create, strikes, lag_ratio=1.0), run_time=run_time)

    # ── beats ─────────────────────────────────────────────────────────────────
    # a : turn the background navy
    @subscene
    def to_navy(self):
        self.navy_rect = self._navy()
        self.play(FadeIn(self.navy_rect), run_time=0.8)

    # b : title + "Word Finished" — words using ONLY backbone (top-3-tier) letters
    @subscene
    def only_tier(self):
        self._setup_pie()
        self.play(FadeIn(self.pie_title), run_time=0.6)
        self.pie.fan_sectors(self, [0], 0.9)

    # c : "Word Known" — narrowed to a single option using only those letters
    @subscene
    def single_opt(self):
        self.pie.fan_sectors(self, [1], 0.9)

    # d : "No more misses", THEN 1-more-miss + 2+-more-misses fanning out from one point
    @subscene
    def miss_dist(self):
        self.pie.fan_sectors(self, [2], 0.9)                       # No more misses
        self.pie.fan_group(self, [3, 4], 1.2)                      # 1 + 2+ from one origin

    # e : chalkboard reverse-in; 7 blanks at the BOTTOM; gallows; WORDS REMAINING: 5541
    @subscene
    def chalk_in(self):
        self.play(FadeOut(self.pie), FadeOut(self.pie_title), run_time=0.5)
        self.pie = None
        self.pie_title = None
        self._setup_board()
        self.add(self.cb)                                          # navy slate covers the frame
        self.remove(self.navy_rect)                               # (hidden behind the slate)
        self.navy_rect = None
        # REVERSE dissolve: the slate contracts out of the full frame, the wooden frame
        # sliding in from off-screen, revealing the light-blue surround.
        self.play(self.cb.animate.scale(1.0 / SCALE_UP, about_point=ORIGIN),
                  run_time=1.4, rate_func=smooth)
        self._write(self.rules, 1.4)                              # blanks, one at a time (L→R)
        self.play(Create(self.hang), run_time=0.8)                # the gallows
        self._draw_count(1.6)                                     # WORDS REMAINING: 5541

    # f : play FIGURES up to & incl. the I (e·s·i hits); count ticks 5541→1166→231→21
    @subscene
    def figures(self):
        for st in self.data["figures"]["steps"][:self.i_cut]:     # e, s, i (all hits)
            self._guess(st["letter"], st["hit"], 1.0)
            self._update_count(st["count"], 1.0)

    # g : erase the count, write out the remaining words, play the rest crossing them off
    @subscene
    def figures_words(self):
        self.play(FadeOut(self.count_group), run_time=0.5)
        steps = self.data["figures"]["steps"]
        remaining = steps[self.i_cut - 1]["words"]                # the words after the I
        self._write(self._word_grid(remaining), 2.6)
        prev = set(remaining)
        for st in steps[self.i_cut:]:                             # p, t, g, f, u, r
            self._guess(st["letter"], st["hit"], 1.0)
            cur = set(st["words"])
            self._cross_off([w for w in remaining if w in prev and w not in cur], 0.9)
            prev = cur

    # h : remove the chalkboard — ends on a blank frame (next scene is animated)
    @subscene
    def chalk_out(self):
        self.play(*[FadeOut(m) for m in list(self.mobjects)], run_time=0.8)

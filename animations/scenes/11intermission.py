"""SCENE 11 — the intermission (the shift from pattern-hunting to word-hunting).

Two halves on a NAVY background:
  • beats a–d: a PIE that partitions all 34,483 words by how the top-3-tier "backbone"
    opening (A E I N O R S T) resolves them — the sections fan in ONE AT A TIME
    (pie_chart.fan_sectors): only-tier words → uniquely-pinned → the rest of the 0-miss
    words → then the 1/2/3-miss tail all at once. Numbers SOURCED from
    `assets/scene11_data` (the committed `scene11_cache.json`, produced by
    `math/tier_backbone.py` — an OPTIMAL-strategy computation).
  • beats e–g: the wooden CHALKBOARD slides back in (the REVERSE of scene 04/01's
    board→navy dissolve — its navy slate == this scene's navy bg, so it just contracts
    out of the full frame while the frame slides in), gets 7 blanks + a gallows, and the
    optimal strategy is PLAYED OUT on FIGURES (sourced trace: e·s·i hit, p·t miss,
    g·f·u·r hit — 2 misses). Then the chalkboard is removed to a blank frame.

Reuse: `assets.game_board` (gb) for the board/blanks/gallows/guessing (canonical
gameplay layout, as 02/04/94); `bpkfigures.pie_chart` for the fanning pie; the navy
bg follows scene 08.

BEAT MAP
  a to_navy     — turn the background navy (scene-08 `_navy` rect)
  b only_tier   — pie section 0: % of words using only backbone letters
  c single_opt  — pie section 1: % narrowed to a single option
  d miss_dist   — pie section 2 (rest of 0-miss), then the 1/2/3-miss tail all at once
  e chalk_in    — chalkboard reverse-in + 7 blanks + gallows
  f figures     — play out the optimal strategy on FIGURES (bubble → write)
  g chalk_out   — remove the chalkboard (ends blank, next scene is animated)

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
from assets.chalkboard import chalkboard, BOARD_NAVY, CHALK
from assets import game_board as gb
from assets import scene11_data
from bpkfigures.pie_chart import get_pie_chart

PIE_R = 2.4                     # big pie, centred
PIE_CENTER = ORIGIN
SCALE_UP = 5.0                  # chalkboard scale at which its slate fills the frame
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

    def _sector_values(self, dist):
        """(values, colours) for the pie sectors, in reveal order:
        only_tier, single_option, rest-of-0-miss, then 1-miss, 2-miss, … (the tail)."""
        md = dist["miss_dist"]
        vals = [dist["only_tier"], dist["single_option"], dist["rest_zero_miss"]]
        colors = list(ZERO_MISS_GREENS)
        maxm = dist["max_misses"]
        for k in range(1, maxm + 1):
            vals.append(int(md[str(k)]))
            t = (k - 1) / max(maxm - 1, 1)         # 0 at 1 miss → 1 at max misses
            colors.append(interpolate_color(ACCENT_GOLD, ACCENT_RED, t))
        return vals, colors

    def _setup_pie(self):
        dist = self.data["dist"]
        if dist is None:
            raise RuntimeError("scene11_cache.json missing — run `python3 "
                               "math/tier_backbone.py` to source the pie numbers.")
        vals, colors = self._sector_values(dist)
        self.pie = get_pie_chart(vals, colors=colors, radius=PIE_R, center=PIE_CENTER,
                                 label_mode="inside", label_font_size=20,
                                 inner_frac=0.62, inner_frac_spread=0.5,
                                 stroke_color=WHITE)
        self.pie.hide_all()                        # incremental build across b/c/d
        self.add(self.pie)

    def _setup_board(self):
        """Build the chalkboard SCALED UP so its navy slate fills the frame (visually ==
        the navy bg), plus the (not-yet-drawn) 7 blanks + gallows at normal size."""
        self.cb = chalkboard(gb.BOARD_W, gb.BOARD_H)
        self.cb.set_z_index(-9)                    # above the navy rect, below the chalk
        self.cb.scale(SCALE_UP, about_point=ORIGIN)   # slate fills frame, frame off-screen
        word = self.data["figures"]["word"] if self.data["figures"] else "figures"
        self.rules = gb.build_rules(len(word))
        self.hang, self.hang_parts = gb.build_gallows()
        misses = "".join(g["letter"] for g in self.data["figures"]["guesses"]
                         if not g["hit"]) if self.data["figures"] else "pt"
        self.miss_slots_x = gb.miss_slots(self.hang, misses)   # centre by the real misses

    def _play_guess(self, letter, hit, run_time):
        """One guess, the canonical two-step: a speech bubble pops from the left, THEN
        the letter is WRITTEN ON (Create strokes) — into its blanks on a HIT, or into
        the miss row + the next gallows body part on a MISS — then the bubble dismisses.
        `run_time` scales the whole guess (bubble 0.25·r, write 0.5·r, part 0.25·r)."""
        r = run_time / 1.0
        bub = gb.bubble(letter, tail="left")
        self.play(GrowFromPoint(bub, bub.tip_dot.get_center()), run_time=0.5 * r)
        if hit:
            word = self.data["figures"]["word"]
            Ls = [gb.reveal_letter(letter, self.rules[p])
                  for p, c in enumerate(word) if c == letter]
            strokes = VGroup(*[s for L in Ls for s in L])
            self.play(LaggedStartMap(Create, strokes, lag_ratio=1.0), run_time=0.9 * r)
        else:
            L = gb.miss_letter(letter, self.miss_slots_x[self.miss_n])
            self.play(LaggedStartMap(Create, L, lag_ratio=0.5), run_time=0.6 * r)
            part = self.hang_parts[self.miss_n]
            self.hang.add(part)
            self.play(Create(part), run_time=0.5 * r)
            self.miss_n += 1
        self.play(FadeOut(bub), run_time=0.3 * r)

    # ── beats ─────────────────────────────────────────────────────────────────
    # a : turn the background navy
    @subscene
    def to_navy(self):
        self.navy_rect = self._navy()
        self.play(FadeIn(self.navy_rect), run_time=0.8)

    # b : pie section — % of words using ONLY backbone (top-3-tier) letters
    @subscene
    def only_tier(self):
        self._setup_pie()
        self.pie.fan_sectors(self, [0], 0.9)

    # c : pie section — % narrowed to a SINGLE option using only those letters
    @subscene
    def single_opt(self):
        self.pie.fan_sectors(self, [1], 0.9)

    # d : the rest of the 0-additional-miss words, THEN the 1/2/3-miss tail all at once
    @subscene
    def miss_dist(self):
        self.pie.fan_sectors(self, [2], 0.9)                       # rest of 0-miss
        tail = list(range(3, len(self.pie.sectors)))
        self.pie.fan_sectors(self, tail, 1.2)                      # 1,2,3-miss together

    # e : the chalkboard slides back in (reverse of the board→navy dissolve) + blanks + gallows
    @subscene
    def chalk_in(self):
        self.play(FadeOut(self.pie), run_time=0.5)
        self.pie = None
        self._setup_board()
        self.add(self.cb)                                          # navy slate covers the frame
        self.remove(self.navy_rect)                               # (hidden behind the slate)
        self.navy_rect = None
        # REVERSE dissolve: the slate contracts out of the full frame, the wooden frame
        # sliding in from off-screen, revealing the light-blue surround.
        self.play(self.cb.animate.scale(1.0 / SCALE_UP, about_point=ORIGIN),
                  run_time=1.4, rate_func=smooth)
        # write the 7 blanks, then draw the gallows (body parts come one-per-miss in f)
        self.play(LaggedStartMap(Create, self.rules, lag_ratio=0.3), run_time=0.8)
        self.play(Create(self.hang), run_time=0.8)

    # f : play out the OPTIMAL strategy on FIGURES (e·s·i hit, p·t miss, g·f·u·r hit)
    @subscene
    def figures(self):
        for g in self.data["figures"]["guesses"]:
            self._play_guess(g["letter"], g["hit"], 1.0)

    # g : remove the chalkboard — ends on a blank frame (next scene is animated)
    @subscene
    def chalk_out(self):
        content = list(self.mobjects)
        self.play(*[FadeOut(m) for m in content], run_time=0.8)

"""Shared base for the tier-list letter scenes (07 top · 09/10 high · the rest).

Walks ONE tier's letters with the recurring visual: the letter fills into its tier
row, the tier list tucks ×TL_SHRINK to the top-left, and a big COPY of the letter
slides ↙ recolouring white→brand blue; the next letter removes the on-screen views,
sends the corner copy back AS it fades into the tier, then sends its own copy down.
Each letter shows the position-frequency heatmap + n-gram views (Position Frequencies
/ Top N-grams) and — where the script calls for it — a leading common-uses list.

A subclass sets three class attributes:
    TIER_IDX   int          the tier being populated (0 = TOP, 1 = HIGH↑, …)
    LETTERS    [str]        that tier's letters, in order (lowercase)
    FILLED     [(idx, str)] the tiers ABOVE, already populated (shown from frame 0)
calls ``self.build_board(on_screen=…)`` in ``setup_scene`` (on_screen=False for a
blank start that later fades the list in), and defines its own @subscene beats from
the inherited helpers:
    enter_centered(rt)               blank start: fade the centred list in
    intro_letter(i, rt)              first letter: fill + tuck + copy ↙
    intro_letter_views(i, ch, rt_fill, rt)  first letter: fill, then tuck + copy ↙ with
                                     the heatmap + n-gram rising in BEHIND the tuck
    advance_letter(i, rt_ret, rt_dn) later letters: clear views, return+appear, copy ↙
    show_heat(ch, rt) / add_ngram(ch, rt)
    show_views(ch, rt)               heatmap + n-gram rise in TOGETHER in one beat
    show_common(rows, rt)            only if the tier has a common-uses beat
    clear_views(rt)
    recenter_board(rt)               tuck → centre (hand off to the next tier scene)
    close_all(rt)                    fade everything out (end on a blank screen)
Scenes 07 (common-uses, ends blank) / 09 (blank start, ends centred) / 10 (centred
start, ends centred) are the three shapes. @subscene beats MUST live in the scene
file (the render tooling AST-scans it), so this base holds ONLY plain helpers.
"""
from config import *
from assets import tier_list as tl
from assets import views
from assets.common_uses import common_uses
from assets.letter_heatmaps import letter_heatmaps
from assets.letter_ngrams import letter_ngrams

# tuck + big-letter geometry
TL_SHRINK   = 0.7
TL_TOP_BUFF = 0.5
BIG_GROW    = 5.5                                  # big letter = grid-base × 5.5

# view region (right of the tucked tier list)
HEAT_CENTER = np.array([1.6, -0.4, 0.0])
NG_X        = 6.0
TITLE_Y     = 3.2
CU_CENTER_X = 3.0                                  # common-uses list centred here


class TierLetterScene(HangmanScene):
    """See module docstring. Subclasses set TIER_IDX / LETTERS / FILLED + the beats."""

    TIER_IDX = 0
    LETTERS  = []
    FILLED   = []

    # ── setup ───────────────────────────────────────────────────────────────────
    def build_board(self, *, on_screen):
        """Build the named tier list with the FILLED tiers populated (visible) and
        this scene's tier pre-placed INVISIBLE (revealed one per intro beat). Tiles
        are children of the list, so they travel with it when it tucks. `on_screen`
        adds it centred from frame 0 (a continuation); False leaves it off (a blank
        start that `enter_centered` fades in)."""
        self.tl = tl.get_tier_list("name")
        for idx, letters in self.FILLED:
            tl.fill_tier(self.tl, idx, letters)
        self.tier_tiles = tl.fill_tier(self.tl, self.TIER_IDX,
                                       "".join(self.LETTERS).upper())
        for t in self.tier_tiles:
            t.set_opacity(0)
        if on_screen:
            self.add(self.tl)
        self._tl_full_h = self.tl.height
        self._tl_full_w = self.tl.width
        self._big_h = crisp_text("A", font_size=48).height * BIG_GROW
        self.corner = self.corner_home = None                  # the big ↙ copy
        self.corner_char = None                                # its letter (→ ink/tile)
        self.common = self.cu_title = None
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None

    # ── the tier list: enter / tuck / recentre ──────────────────────────────────
    def enter_centered(self, run_time):
        """Blank-start scenes: fade the (centred) tier list in."""
        self.play(FadeIn(self.tl), run_time=run_time)

    def _corner_target(self, tile):
        """Bottom-left rest pose for the big letter copy: centred under the tucked
        tier list, vertically centred in the gap below it."""
        fx, fy = config.frame_x_radius, config.frame_y_radius
        tier_cx = -fx + TL_TOP_BUFF + (self._tl_full_w * TL_SHRINK) / 2
        final_bottom = (fy - TL_TOP_BUFF) - self._tl_full_h * TL_SHRINK
        cy = (final_bottom + -fy) / 2
        return [tier_cx, cy, 0]

    def intro_letter(self, i, run_time):
        """First letter of the tier: fill tile `i`, tuck the list ↖, send a copy ↙
        recoloured to its dark ink colour (vowel dark-red / consonant blue)."""
        self.play(self.tier_tiles[i].animate.set_opacity(1), run_time=0.6)
        copy = self.tier_tiles[i].copy()
        self.add(copy)
        ch = self.LETTERS[i]
        self.play(self.tl.animate.scale(TL_SHRINK).to_corner(UL, buff=TL_TOP_BUFF),
                  copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(tl.ink_color(ch)),
                  run_time=run_time)
        self.corner, self.corner_home, self.corner_char = copy, self.tier_tiles[i], ch

    def intro_letter_views(self, i, ch, run_time_fill, run_time):
        """`intro_letter` with the views RISING IN BEHIND the tuck: fill tile `i`, then
        in ONE play tuck the list ↖, send the copy ↙, AND rise the heatmap + n-gram in
        TOGETHER — so the Position/N-gram views come in from BEHIND the leftward-moving
        tier list and big letter (both are z-raised so they stay in front). Leaves the
        views up (as `show_views` would), so a following `rapid_letter` can morph them.
        Use for a first letter whose views should establish DURING the intro rather than
        in a separate beat."""
        self.play(self.tier_tiles[i].animate.set_opacity(1), run_time=run_time_fill)
        copy = self.tier_tiles[i].copy()
        self.add(copy)
        # keep the tier list + big letter IN FRONT so the views rise in behind them
        self.tl.set_z_index(1)
        copy.set_z_index(1)
        # build the views up-front so they can rise in the SAME play as the tuck
        new_heat = letter_heatmaps(ch, center=HEAT_CENTER, high_color=tl.heat_color(ch))
        heat_title = self._title1("Position Frequencies", HEAT_CENTER[0])
        top_y = new_heat.heatmaps[0].get_top()[1]
        bot_y = new_heat.heatmaps[-1].get_bottom()[1]
        new_ng = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y,
                               letter_color=tl.ink_color(ch))
        ng_title = self._title1("Top N-grams", NG_X)
        self.play(self.tl.animate.scale(TL_SHRINK).to_corner(UL, buff=TL_TOP_BUFF),
                  copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(tl.ink_color(ch)),
                  FadeIn(heat_title), FadeIn(ng_title),
                  self._rise(new_heat, self._heat_rows(new_heat)),
                  self._rise(new_ng, new_ng.rows),
                  run_time=run_time)
        self.corner, self.corner_home, self.corner_char = copy, self.tier_tiles[i], ch
        self.heat, self.loc_title = new_heat, heat_title
        self.ngram, self.ng_title = new_ng, ng_title

    def _send_copy_down(self, tile, ch, run_time):
        copy = tile.copy()
        self.add(copy)
        self.play(copy.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(copy)).set_color(tl.ink_color(ch)),
                  run_time=run_time)
        self.corner, self.corner_home, self.corner_char = copy, tile, ch

    def _return_next(self, i, run_time):
        """One play: the corner copy returns to its tier slot (recolouring to its bright
        TILE colour) WHILE the next tile fades into the tier; then the copy is dropped."""
        reveal = self.tier_tiles[i].animate.set_opacity(1)
        if self.corner is None:
            self.play(reveal, run_time=run_time)
            return
        c, tile = self.corner, self.corner_home
        self.play(c.animate.scale_to_fit_height(tile.height).move_to(tile.get_center())
                  .set_color(tl.tile_color(self.corner_char)),
                  reveal, run_time=run_time)
        self.remove(c)
        self.corner = self.corner_home = None

    def switch_letter(self, i, run_time_return, run_time_down):
        """Letter switch WITHOUT touching the views: return the corner copy AS tile
        `i` fades into the tier, then send tile `i`'s copy ↙."""
        self._return_next(i, run_time_return)
        self._send_copy_down(self.tier_tiles[i], self.LETTERS[i], run_time_down)

    def advance_letter(self, i, run_time_return, run_time_down):
        """Later letters (normal): remove the current views, THEN switch to tile `i`."""
        self.clear_views()
        self.switch_letter(i, run_time_return, run_time_down)

    def rapid_letter(self, i, ch, run_time):
        """Rapid-succession switch for a group of similar letters shown back-to-back, all
        in ONE play: the OUTGOING corner copy returns to its tier slot WHILE the INCOMING
        copy of tile `i` slides ↙ to the corner AT THE SAME TIME (the two big letters
        cross paths), tile `i` fades into the tier, and the heatmap MORPHS + the n-gram
        CROSSFADES to `ch` (views are not removed and rebuilt). Titles persist. Requires
        the views to be up already."""
        new_heat = letter_heatmaps(ch, center=HEAT_CENTER, high_color=tl.heat_color(ch))
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        new_ng = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y,
                               letter_color=tl.ink_color(ch))
        c, tile = self.corner, self.corner_home
        # incoming: a copy of the new tile starts AT its slot (full opacity, in front)
        # and slides down as the outgoing copy returns — both move together
        down = self.tier_tiles[i].copy()
        down.set_opacity(1)
        down.set_z_index(1)
        self.add(down)
        self.play(c.animate.scale_to_fit_height(tile.height).move_to(tile.get_center())
                  .set_color(tl.tile_color(self.corner_char)),
                  self.tier_tiles[i].animate.set_opacity(1),
                  down.animate.scale_to_fit_height(self._big_h)
                  .move_to(self._corner_target(down)).set_color(tl.ink_color(ch)),
                  ReplacementTransform(self.heat, new_heat),
                  FadeOut(self.ngram), FadeIn(new_ng),
                  run_time=run_time)
        self.remove(c)
        self.heat, self.ngram = new_heat, new_ng
        self.corner, self.corner_home, self.corner_char = down, self.tier_tiles[i], ch

    def recenter_board(self, run_time):
        """Clear the views + big letter and send the tier list back to CENTRE (hand
        off to the next tier scene)."""
        outs = [v for v in (self.corner, self.heat, self.loc_title, self.ngram,
                            self.ng_title, self.common, self.cu_title) if v]
        self.play(*[FadeOut(m) for m in outs],
                  self.tl.animate.scale(1 / TL_SHRINK).move_to(ORIGIN),
                  run_time=run_time)
        self.corner = self.corner_home = None

    def close_all(self, run_time):
        """Fade EVERYTHING (tier list included) out — end on a blank screen."""
        outs = [self.tl] + [v for v in (self.corner, self.heat, self.loc_title,
                                        self.ngram, self.ng_title, self.common,
                                        self.cu_title) if v]
        self.play(*[FadeOut(m) for m in outs], run_time=run_time)

    # ── views: heatmap + n-gram + (optional) common-uses, 96-style row rise ──────
    # Titles + the row-by-row rise now live in the shared `assets.views` (so any
    # scene reuses the SAME motion — e.g. scene 16's usage plot); these delegate.
    def _title(self, l1, l2, x):
        return views.view_title2(l1, l2, x, TITLE_Y)

    def _title1(self, text, x):
        return views.view_title(text, x, TITLE_Y)

    def _rise(self, parent, rows, *, lag_ratio=views.RISE_LAG, shift=views.RISE_SHIFT):
        """96's entrance (shared `views.rise`): add `parent`, preset each row low +
        transparent, return the LaggedStart lifting them in (caller sets run_time)."""
        return views.rise(self, parent, rows, lag_ratio=lag_ratio, shift=shift)

    def _heat_rows(self, heat):
        return [VGroup(lab, hm) for lab, hm in zip(heat.labels, heat.heatmaps)]

    def _cu_rows(self, cu):
        return [VGroup(lab, row) for lab, row in zip(cu.labels, cu.rows)]

    def _fade_current(self):
        """FadeOuts for every view currently up, resetting their handles — so a new
        view can REPLACE them in one play (a swap). Empty when nothing is showing."""
        fades = [FadeOut(v) for v in (self.common, self.cu_title, self.heat,
                                      self.loc_title, self.ngram, self.ng_title) if v]
        self.common = self.cu_title = None
        self.heat = self.loc_title = None
        self.ngram = self.ng_title = None
        return fades

    def show_heat(self, ch, run_time):
        """Rise the heatmap in, fading whatever's currently up out in the SAME play
        (so a common-uses view swaps straight into the heatmap; a no-op fade when the
        views were already cleared)."""
        new = letter_heatmaps(ch, center=HEAT_CENTER, high_color=tl.heat_color(ch))
        title = self._title1("Position Frequencies", HEAT_CENTER[0])
        fades = self._fade_current()
        self.play(*fades, FadeIn(title),
                  self._rise(new, self._heat_rows(new)), run_time=run_time)
        self.heat, self.loc_title = new, title

    def add_ngram(self, ch, run_time):
        """ADD the n-gram view beside the heatmap (additive — does not touch it)."""
        top_y = self.heat.heatmaps[0].get_top()[1]
        bot_y = self.heat.heatmaps[-1].get_bottom()[1]
        self.ngram = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y,
                                   letter_color=tl.ink_color(ch))
        self.ng_title = self._title1("Top N-grams", NG_X)
        self.play(FadeIn(self.ng_title),
                  self._rise(self.ngram, self.ngram.rows), run_time=run_time)

    def show_views(self, ch, run_time):
        """Rise the position-frequency heatmap AND the n-gram view in TOGETHER, in one
        play (both appear at once — not heat-then-add-ngram over two beats). Fades
        whatever's currently up out in the SAME play (a no-op fade when already clear).
        The n-gram is aligned to the heatmap's row band, computed from the built heat
        mobject before it animates."""
        new_heat = letter_heatmaps(ch, center=HEAT_CENTER, high_color=tl.heat_color(ch))
        heat_title = self._title1("Position Frequencies", HEAT_CENTER[0])
        top_y = new_heat.heatmaps[0].get_top()[1]
        bot_y = new_heat.heatmaps[-1].get_bottom()[1]
        new_ng = letter_ngrams(ch, center_x=NG_X, top_y=top_y, bottom_y=bot_y,
                               letter_color=tl.ink_color(ch))
        ng_title = self._title1("Top N-grams", NG_X)
        fades = self._fade_current()
        self.play(*fades, FadeIn(heat_title), FadeIn(ng_title),
                  self._rise(new_heat, self._heat_rows(new_heat)),
                  self._rise(new_ng, new_ng.rows), run_time=run_time)
        self.heat, self.loc_title = new_heat, heat_title
        self.ngram, self.ng_title = new_ng, ng_title

    def show_common(self, rows, run_time):
        """The common-uses list (blank/partly-played boards + red misses), swapping in
        over any current views. Centred at CU_CENTER_X and vertically between its title
        and the screen bottom."""
        new = common_uses(list(rows))
        new.set_x(CU_CENTER_X)
        title = self._title1("Example Uses", CU_CENTER_X)
        new.set_y((title.get_bottom()[1] + -config.frame_y_radius) / 2)
        fades = self._fade_current()
        self.play(*fades, FadeIn(title),
                  self._rise(new, self._cu_rows(new)), run_time=run_time)
        self.common, self.cu_title = new, title

    def clear_views(self, run_time=0.6):
        """Fade the common-uses / heatmap / n-gram (and titles) out — the views are
        removed BEFORE the next letter comes on."""
        fades = self._fade_current()
        if fades:
            self.play(*fades, run_time=run_time)

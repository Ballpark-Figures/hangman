"""Letter grid — the 26 letters in ragged, left-aligned rows, for an upcoming view.

Rows: ABCD / EFGH / IJKLMN / OPQRST / UVWX / YZ  (4/4/6/6/4/2 = 26). Columns are
left-aligned — column 0 shares an x across rows, right edges are ragged. The
first column (A E I O U Y) is blue; every other letter is black.

`letter_grid()` (or `LetterGrid(...)`) builds it; handles for later animation:
  .letters    {char: Text}     every letter by name
  .rows        [VGroup, …]     one VGroup per row (top → bottom)
  .first_col   VGroup          the blue first-column letters
Animations (asset methods, each a single run_time-scaled play):
  .slide_in(scene)             standard entrance from off the left edge
  .choose(scene, letter)       grid shrinks → top-left, chosen letter grows → bottom
  .swap(scene, new_letter)     send the chosen letter back, `new_letter` takes over
  .restore(scene)              send the chosen letter back AND grid → its home

`choose` detaches the chosen letter and leaves an invisible placeholder copy in
its slot; the placeholder rides every later grid transform, so `swap`/`restore`
just animate the letter back onto its placeholder — exactly where the slot is now.
"""
from config import *

GRID_ROWS = ["ABCD", "EFGH", "IJKLMN", "OPQRST", "UVWX", "YZ"]

# NOTE: user-specified literal colours for this asset — plain black letters with
# a blue first column (ACCENT_FILL is the brand blue).
FIRST_COL_COLOR = ACCENT_FILL
LETTER_COLOR = BLACK


class LetterGrid(VGroup):
    """The alphabet in ragged left-aligned rows (see module docstring)."""

    def __init__(self, *, font_size=48, col_w=0.85, row_h=0.85, **kwargs):
        super().__init__(**kwargs)
        self.letters = {}
        self.rows = []
        self.first_col = VGroup()
        for r, row in enumerate(GRID_ROWS):
            row_group = VGroup()
            for c, ch in enumerate(row):
                first = c == 0
                t = crisp_text(ch, font_size=font_size,
                               color=FIRST_COL_COLOR if first else LETTER_COLOR)
                t.move_to([c * col_w, -r * row_h, 0])   # centered on its grid point
                self.add(t)
                self.letters[ch] = t
                row_group.add(t)
                if first:
                    self.first_col.add(t)
            self.rows.append(row_group)

        self._base_letter_h = self.letters["A"].height   # unscaled letter height
        self._home_center = None      # grid center before choose (set in choose)
        self._applied_scale = 1.0     # grid scale relative to home
        self._chosen = None           # the standalone grown letter (or None)
        self._chosen_char = None
        self._placeholder = None      # invisible slot-holder riding the grid

    # ── entrance ──────────────────────────────────────────────────────────────
    def slide_in(self, scene, *, from_dir=LEFT, dist=None, run_time=1.0, play=True):
        """Standard entrance: shift the grid fully off-screen in `from_dir`
        (default LEFT), add it, then animate back to the home position it
        currently sits at. Position the grid at its home FIRST, then call this.
        `play=False` returns the move animation for the caller to compose."""
        d = np.array(from_dir, dtype=float)
        n = np.linalg.norm(d)
        if n:
            d = d / n
        home = self.get_center().copy()
        if dist is None:
            fx, fy, margin = config.frame_x_radius, config.frame_y_radius, 0.4
            if abs(d[0]) >= abs(d[1]):                     # horizontal slide
                dist = (home[0] if d[0] < 0 else -home[0]) + self.width / 2 + fx
            else:                                          # vertical slide
                dist = (home[1] if d[1] < 0 else -home[1]) + self.height / 2 + fy
            dist += margin
        self.shift(d * dist)
        scene.add(self)
        move = self.animate.move_to(home)
        if not play:
            return move
        scene.play(move, run_time=run_time)
        return self

    # ── internals ──────────────────────────────────────────────────────────────
    def _detach(self, scene, char, grow, corner_buff, final_bottom_y):
        """Pull `char` out of the grid: leave an invisible placeholder in its slot,
        add the letter to the scene on its own, and build the grow-to-bottom
        animation. Returns (grow_anim, letter, placeholder)."""
        letter = self.letters[char]
        ph = letter.copy().set_opacity(0)      # rides the grid in the letter's slot
        self.remove(letter)
        self.add(ph)
        scene.add(letter)
        grown_h = self._base_letter_h * grow                  # absolute target size
        target_w = letter.width * grown_h / letter.height
        x_left = -config.frame_x_radius + corner_buff
        cy = (final_bottom_y + -config.frame_y_radius) / 2    # equal gaps above/below
        anim = letter.animate.scale_to_fit_height(grown_h).move_to(
            [x_left + target_w / 2, cy, 0])
        return anim, letter, ph

    def _return_anim(self, letter, ph, *, scale=1.0, tp=None):
        """Animate `letter` back onto placeholder `ph`. `tp` maps ph's current
        world center to its post-move center (for when the grid moves this beat);
        `scale` is the grid's scale change this beat (ph's height scales with it)."""
        center = ph.get_center() if tp is None else tp(ph.get_center())
        return letter.animate.scale_to_fit_height(ph.height * scale).move_to(center)

    # ── select a letter ───────────────────────────────────────────────────────
    def choose(self, scene, letter, *, grow=5.5, shrink=0.8, corner_buff=1.0,
               run_time=1.2, play=True):
        """Pick `letter`: the grid shrinks ×`shrink` as it moves up to the
        top-left corner, while the chosen letter detaches, grows ×`grow`, and
        settles at the left — vertically centered in the space below the grid so
        the gap above it (to the grid) equals the gap below it (to the frame
        bottom). Returns the (standalone, enlarged) chosen letter mobject.
        `play=False` returns (grid_move, pick_move, chosen) to compose."""
        self._home_center = self.get_center().copy()
        self._applied_scale = shrink

        top_buff = 0.5
        # grid's final bottom: top edge (fy - buff) minus the shrunk height
        final_bottom_y = (config.frame_y_radius - top_buff) - self.height * shrink
        # detach FIRST (swap the letter for its placeholder), THEN build the grid
        # animation, so the animate target matches self's post-detach structure
        pick_move, chosen, ph = self._detach(scene, letter, grow, corner_buff,
                                             final_bottom_y)
        grid_move = self.animate.scale(shrink).to_corner(UL, buff=top_buff)
        if not play:
            return grid_move, pick_move, chosen
        scene.play(grid_move, pick_move, run_time=run_time)
        self._chosen, self._chosen_char, self._placeholder = chosen, letter, ph
        return chosen

    def swap(self, scene, new_letter, *, grow=5.5, corner_buff=1.0, run_time=1.2,
             play=True):
        """Send the current chosen letter back to its slot in the (top-left) grid
        while `new_letter` detaches and takes its place at the bottom. The grid
        itself stays put. Returns the new standalone letter."""
        assert self._chosen is not None, "swap() needs a prior choose()"
        old_letter, old_ph = self._chosen, self._placeholder
        return_anim = self._return_anim(old_letter, old_ph)   # grid static → in place
        pick_anim, new_mob, new_ph = self._detach(
            scene, new_letter, grow, corner_buff, self.get_bottom()[1])
        # state bookkeeping — the anims have already captured their positions, so do
        # it BEFORE the play; this way it holds whether WE play or the caller does
        # (play=False), not just on the play=True path.
        self.remove(old_ph)              # old letter rejoins the grid…
        self.add(old_letter)
        self._chosen, self._chosen_char, self._placeholder = new_mob, new_letter, new_ph
        if not play:
            return return_anim, pick_anim, new_mob
        scene.play(return_anim, pick_anim, run_time=run_time)
        return new_mob

    def restore(self, scene, *, run_time=1.2, play=True):
        """Send the current chosen letter back to its slot AND return the grid to
        its original (pre-choose) home position and full size, together."""
        assert self._chosen is not None, "restore() needs a prior choose()"
        s = 1.0 / self._applied_scale
        C0 = self.get_center().copy()
        home = self._home_center
        tp = lambda p: home + s * (np.array(p, dtype=float) - C0)   # grid's move
        grid_move = self.animate.scale(s).move_to(home)
        return_anim = self._return_anim(self._chosen, self._placeholder,
                                        scale=s, tp=tp)
        if not play:
            return grid_move, return_anim, self._chosen
        scene.play(grid_move, return_anim, run_time=run_time)
        self.remove(self._placeholder)
        self.add(self._chosen)
        self._applied_scale = 1.0
        self._chosen = self._chosen_char = self._placeholder = None
        return self


def letter_grid(**kwargs):
    """Factory (mirrors yahtzee's get_scorecard): build a LetterGrid."""
    return LetterGrid(**kwargs)

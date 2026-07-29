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
  .choose(scene, letter)       grid → top-left, chosen letter grows → bottom-left
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

    # ── select a letter ───────────────────────────────────────────────────────
    def choose(self, scene, letter, *, grow=5.5, shrink=0.8, corner_buff=1.0,
               run_time=1.2, play=True):
        """Pick `letter`: the grid shrinks ×`shrink` as it moves up to the
        top-left corner, while the chosen letter detaches, grows ×`grow`, and
        settles at the left — vertically centered in the space below the grid so
        the gap above it (to the grid) equals the gap below it (to the frame
        bottom). Returns the (standalone, enlarged) chosen letter mobject.
        `play=False` returns (grid_move, pick_move, chosen) to compose."""
        chosen = self.letters[letter]
        self.remove(chosen)              # detach from the grid group…
        scene.add(chosen)                # …and keep it in the scene on its own
        grid_move = self.animate.scale(shrink).to_corner(UL, buff=0.5)

        # centre the grown letter between the grid's final bottom and the frame
        # bottom → equal gaps above/below (independent of the letter's height)
        grid_bottom = self.copy().scale(shrink).to_corner(UL, buff=0.5).get_bottom()[1]
        cy = (grid_bottom + -config.frame_y_radius) / 2
        x_left = -config.frame_x_radius + corner_buff
        pick_move = chosen.animate.scale(grow).move_to(
            [x_left + chosen.width * grow / 2, cy, 0])
        if not play:
            return grid_move, pick_move, chosen
        scene.play(grid_move, pick_move, run_time=run_time)
        return chosen


def letter_grid(**kwargs):
    """Factory (mirrors yahtzee's get_scorecard): build a LetterGrid."""
    return LetterGrid(**kwargs)

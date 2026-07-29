"""Letter grid — the 26 letters in ragged, left-aligned rows, for an upcoming view.

Rows: ABCD / EFGH / IJKLMN / OPQRST / UVWX / YZ  (4/4/6/6/4/2 = 26). Columns are
left-aligned — column 0 shares an x across rows, right edges are ragged. The
first column (A E I O U Y) is blue; every other letter is black.

`letter_grid()` returns a VGroup with handles for later animation:
  .letters    {char: Text}     every letter by name
  .rows       [VGroup, …]      one VGroup per row (top → bottom)
  .first_col  VGroup           the blue first-column letters
"""
from config import *

GRID_ROWS = ["ABCD", "EFGH", "IJKLMN", "OPQRST", "UVWX", "YZ"]

# NOTE: user-specified literal colours for this asset — plain black letters with
# a blue first column (ACCENT_FILL is the brand blue).
FIRST_COL_COLOR = ACCENT_FILL
LETTER_COLOR = BLACK


def letter_grid(*, font_size=48, col_w=0.85, row_h=0.85):
    """Build the alphabet grid. Each letter is centered on its (col, row) point,
    so columns line up flush-left with ragged right edges."""
    grid = VGroup()
    grid.letters = {}
    grid.rows = []
    grid.first_col = VGroup()
    for r, row in enumerate(GRID_ROWS):
        row_group = VGroup()
        for c, ch in enumerate(row):
            first = c == 0
            t = crisp_text(ch, font_size=font_size,
                           color=FIRST_COL_COLOR if first else LETTER_COLOR)
            t.move_to([c * col_w, -r * row_h, 0])
            grid.add(t)
            grid.letters[ch] = t
            row_group.add(t)
            if first:
                grid.first_col.add(t)
        grid.rows.append(row_group)
    return grid

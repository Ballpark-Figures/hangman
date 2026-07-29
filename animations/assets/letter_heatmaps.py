"""Letter-view position heatmaps — a stack of 1×k heatmaps, one per word length
k = 2..10, for a chosen letter.

Cell (length k, position i) = fraction of length-k words with the letter at that
position (UNWEIGHTED — each word counts once), read from the committed
`letter_heat_cache.json` (built by `letter_heat_data`, sourced from the wordlist).
All nine heatmaps share ONE colour scale: white = 0, red = this letter's MAX over
every length/position. Rows are left-aligned (position 1 lines up), each labeled
with its length, and the whole block is centered in the horizontal middle.
"""
from config import *
from bpkfigures.heatmap import get_heatmap
from assets import letter_heat_data as lhd


def letter_heatmaps(letter, *, cell_size=0.42, row_gap=0.14, label_buff=0.3,
                    label_font_size=26, center=ORIGIN):
    """Build the length-2..10 heatmap stack for `letter`. Returns a VGroup with
    `.heatmaps` (the get_heatmap groups, top→bottom) and `.labels`."""
    data = lhd.get(letter)
    vmax = data["vmax"]

    heatmaps = VGroup()
    labels = VGroup()
    pitch = cell_size + row_gap
    for i, L in enumerate(data["lengths"]):
        hm = get_heatmap(data["rows"][L], cell_size=cell_size,
                         vmin=0.0, vmax=vmax, stroke_width=1.0, high_color=CRIMSON)
        hm.move_to([hm.width / 2, -i * pitch, 0])          # left edge at x = 0
        lab = crisp_text(str(L), font_size=label_font_size, color=BLACK)
        lab.next_to(hm, LEFT, buff=label_buff)
        heatmaps.add(hm)
        labels.add(lab)

    group = VGroup(labels, heatmaps)
    group.move_to(center)                                   # into the middle
    group.heatmaps = heatmaps
    group.labels = labels
    return group

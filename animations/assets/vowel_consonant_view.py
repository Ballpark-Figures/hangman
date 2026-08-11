"""Vowel/consonant position-frequency view — the letter position heatmaps aggregated
BY CLASS: for each word length 2..10, a 1×k row whose cell (position i) is coloured by
its VOWEL FRACTION on a consonant-blue → vowel-red scale (0 = all consonant = blue,
1 = all vowel = red). Mirrors `assets/letter_heatmaps.py`; numbers come from the
committed `vowel_consonant_cache.json` (built by `vowel_consonant_data`). Lives on the
scene-08 NAVY background, so labels default to light ink.
"""
from config import *
from bpkfigures.heatmap import get_heatmap
from assets import vowel_consonant_data as vcd


def vowel_consonant_heatmaps(*, cell_size=0.42, row_gap=0.14, label_buff=0.3,
                             label_font_size=26, center=ORIGIN,
                             vowel_color=LIGHT_RED, consonant_color=LIGHT_BLUE,
                             label_color=WHITE):
    """Build the length-2..10 vowel-fraction heatmap stack. Returns a VGroup with
    `.heatmaps` (top→bottom) and `.labels` (the length numbers), like letter_heatmaps."""
    data = vcd.get()
    grid, lengths = data["grid"], data["grid_lengths"]

    heatmaps, labels = VGroup(), VGroup()
    pitch = cell_size + row_gap
    for i, L in enumerate(lengths):
        hm = get_heatmap(grid[L], cell_size=cell_size, vmin=0.0, vmax=1.0,
                         low_color=consonant_color, high_color=vowel_color,
                         stroke_width=1.0)
        hm.move_to([hm.width / 2, -i * pitch, 0])          # left edge at x = 0
        lab = crisp_text(str(L), font_size=label_font_size, color=label_color)
        lab.next_to(hm, LEFT, buff=label_buff)
        heatmaps.add(hm)
        labels.add(lab)

    group = VGroup(labels, heatmaps).move_to(center)
    group.heatmaps = heatmaps
    group.labels = labels
    return group

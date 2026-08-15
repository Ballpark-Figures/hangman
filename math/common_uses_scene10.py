"""Provenance / sourcing for SCENE 10's common-uses views (N and O).

Scene 10's script (animations/Script.md, row 10) adds two common-uses beats:
  - N: "Add common uses view with first 6 examples from the table"
  - O: "Add common uses view with first 6 examples from table"

"the table" = letter_analysis.ipynb's `guesses_of_letter_all_lengths(<letter>)` at
STRATEGY=optimal / WEIGHTING=uniform, sorted by n_words DESCENDING (the scene-09
display sort; under uniform weighting freq_words is proportional to n_words, so the
two orders coincide). "first N examples" = that sorted table's .head(N).

Reuses the VERBATIM-from-notebook helpers in common_uses_scene09.py (no new math),
so this reproduces exactly the rows the user reads in the notebook.

Run:  .venv/bin/python math/common_uses_scene10.py
It prints, for N and O, the (length, board, missed) rows to hard-code into the scene.
"""
from common_uses_scene09 import dump

if __name__ == "__main__":
    dump("n", 6)
    dump("o", 6)

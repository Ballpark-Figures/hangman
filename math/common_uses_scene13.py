"""Provenance / sourcing for SCENE 13's common-uses view (U).

Scene 13's script (animations/Script.md, row 13) is the MID↓ tier (P, U, G, M, B, H).
Per the user's request we add common-uses beats:
  • U — the TOP 6 cases from the table for U.
  • G — the TOP 6 cases whose board ENDS IN "in_" (i.e. the guessed G completes an
    ING at the word's end — G's signature use, per the voiceover: "a vast majority of
    G's common uses come after the I and N have already been filled in").

"the table" = letter_analysis.ipynb's `guesses_of_letter_all_lengths(<letter>)` at
STRATEGY=optimal / WEIGHTING=uniform, displayed sorted by n_words DESCENDING (the
notebook's display sort). "top 6 cases" = that sorted table's .head(6) (after the
optional board-suffix filter for G).

Same pipeline as `common_uses_scene12.py` — `guesses_of_letter` /
`guesses_of_letter_all_lengths` are copied VERBATIM from letter_analysis.ipynb (no
new math), so this reproduces exactly the rows the user reads in the notebook.

Run:  .venv/bin/python math/common_uses_scene13.py
It prints, for U, the (length, board, missed) rows to hard-code into the scene.
"""
from pathlib import Path
import sys


def find_math_dir():
    cwd = Path(__file__).resolve().parent
    for c in (cwd, cwd.parent, cwd / "math", cwd.parent / "math"):
        if (c / "strategy.py").exists():
            return c
    raise FileNotFoundError("Could not find strategy.py.")


math_dir = find_math_dir()
if str(math_dir) not in sys.path:
    sys.path.insert(0, str(math_dir))

import pandas as pd
import strategy_view as sview

STRATEGY, WEIGHTING, BUDGET, FILL_CAPPED = "optimal", "uniform", 5, True


# ── copied verbatim from letter_analysis.ipynb ───────────────────────────────
def guesses_of_letter(letters, length, *, strategy=STRATEGY, weighting=WEIGHTING,
                      budget=BUDGET, fill_capped=FILL_CAPPED, max_level=40,
                      verbose=True):
    letterset = {c for c in letters.lower() if c.isalpha()}
    cols = ['level', 'letter', 'board', 'missed', 'n_words', 'freq_words', 'sample', 'hit_sample']
    s = sview.make_strategy(strategy, length, weighting=weighting, budget=budget,
                            fill_capped=fill_capped)
    if not s.available:
        if verbose:
            print('not available:', s.note)
        return pd.DataFrame(columns=cols)
    total = float(s.word_freq().sum())
    scale = (s.g.N / total) if total else 0.0
    rows = []
    for level in range(max_level + 1):
        nodes = s.states_at_depth(level)
        if not nodes:
            break
        for st in nodes:
            if st['determined'] or st['guess'] not in letterset or st['fmass'] == 0.0:
                continue
            g_letter = st['guess']
            missed = ''.join(st['missed'])
            cand = s.state(st['board'], missed).get('candidates', [])
            hit = [w for w in cand if g_letter in w]
            rows.append({'level': level, 'letter': g_letter, 'board': st['board'],
                         'missed': missed, 'n_words': st['n'],
                         'freq_words': st['fmass'] * scale,
                         'sample': ' '.join(st['sample'][:5]),
                         'hit_sample': ' '.join(hit[:5])})
    if not rows:
        return pd.DataFrame(columns=cols)
    return (pd.DataFrame(rows)
              .sort_values(['level', 'freq_words'], ascending=[True, False])
              .reset_index(drop=True))


def guesses_of_letter_all_lengths(letters, lengths=range(1, 21), *,
                                  strategy=STRATEGY, weighting=WEIGHTING,
                                  budget=BUDGET, fill_capped=FILL_CAPPED):
    cols = ['level', 'length', 'letter', 'board', 'missed', 'n_words', 'freq_words',
            'sample', 'hit_sample']
    parts = []
    for L in lengths:
        df = guesses_of_letter(letters, L, strategy=strategy, weighting=weighting,
                               budget=budget, fill_capped=fill_capped, verbose=False)
        if len(df):
            df.insert(1, 'length', L)
            parts.append(df)
    if not parts:
        return pd.DataFrame(columns=cols)
    return (pd.concat(parts, ignore_index=True)
              .sort_values(['level', 'length', 'freq_words'],
                           ascending=[True, True, False])
              .reset_index(drop=True))
# ─────────────────────────────────────────────────────────────────────────────


def dump(letter, n, *, exclude_missing=None, board_suffix=None):
    """Print the table's first `n` rows (n_words desc), optionally excluding rows
    whose `missed` contains `exclude_missing` or keeping only rows whose `board` ENDS
    IN `board_suffix`. Prints the (length, board, missed) tuples to hard-code, plus
    context columns for the provenance record."""
    tbl = guesses_of_letter_all_lengths(letter).sort_values(by="n_words", ascending=False)
    if exclude_missing:
        tbl = tbl[~tbl["missed"].str.contains(exclude_missing)]
    if board_suffix:
        tbl = tbl[tbl["board"].str.endswith(board_suffix)]
    tbl = tbl.reset_index(drop=True).head(n)
    filt = []
    if exclude_missing:
        filt.append(f"excluding missed containing {exclude_missing!r}")
    if board_suffix:
        filt.append(f"board ends in {board_suffix!r}")
    note = f"  ({', '.join(filt)})" if filt else ""
    print(f"\n=== {letter.upper()}: first {n} rows of "
          f"guesses_of_letter_all_lengths({letter!r}) [optimal/uniform], n_words desc{note} ===")
    with pd.option_context('display.max_colwidth', None, 'display.width', None):
        print(tbl[['level', 'length', 'letter', 'board', 'missed', 'n_words',
                   'freq_words', 'hit_sample']].to_string())
    print("\n  tuples -> [(length, board, missed_list), ...]:")
    for _, r in tbl.iterrows():
        print(f"    ({r['length']}, {r['board']!r}, {list(r['missed'])}),")


if __name__ == "__main__":
    dump("u", 6)
    dump("g", 6, board_suffix="in_")

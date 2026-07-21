# hangman video — specifics

hangman-only conventions. The shared cross-video rules live in
`bpkfigures/CLAUDE.md` (auto-loaded since bpkfigures is always in the workspace).

## Script
- `animations/Script.md` is the video script. Scenes become
  `scenes/NN<name>.py`. (Fill in this video's script/scene conventions.)

## Math / data
- `math/data/wordlist_master.txt` — the curated frequency wordlist
  (`word<TAB>zipf`, built by `math/build_wordlist.py`: wordfreq → hunspell
  filter → zipf floor). Load it via `math/wordlist.py` (default cutoff
  `zipf >= 2.5`); explore in `math/notebooks/wordlist_explorer.ipynb`.
- Data lives in `math/`, NOT `animations/assets/`. Source inputs
  (`wordlist_master.txt`, `allowlist.txt`, `blocklist.txt`) sit at `math/data/`.
- **Solver outputs are split by git status:**
  - `math/data/shared/<solver>/` — **committed**: final trees + csv results,
    meant to sync between machines (`shared/optimal/`, `shared/winprob/`).
  - `math/data/local/<solver>/` — **gitignored**: resume checkpoints / memo
    pickles (regenerable, can be GBs; `.ckpt` for optimal, `.memo.pkl` for
    winprob). The whole `math/data/local/` tree is in `.gitignore`.

## Gameplay layout
- (Describe this video's on-screen layout and the assets in `animations/assets/`.)

## Style
- Uses `bpkfigures` style + the local `config.py` for colors/fonts.

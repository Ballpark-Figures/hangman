#!/bin/bash
# Run winprob at n=6 for one length, memory- and time-capped.
L=$1
OUT=$2
ulimit -v 3500000 2>/dev/null          # ~3.5 GB per process; runaway dies cleanly
timeout 400 python -u /home/pliscio/projects/ballpark-figures/hangman/math/winprob.py "$L" 6 \
    > "$OUT/n6_len$L.txt" 2>&1
echo "len$L exit=$? $(date +%H:%M:%S)"

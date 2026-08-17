"""Reproduce the wordlist-building pipeline and report the word count remaining
after each step, for scene 03 (the "Total words:" counter).

Anchors (post-wordfreq-cutoff / post-non-letter / post-hunspell / final) are
EXACT and independent of how we bucket removals. The video narrates the curated
removals as categories -- abbreviations, single letters, initialisms, roman
numerals, interjections, profanity, greek letters -- and ends with a combined
"things I disagreed with the spellchecker about" beat (counter goes UP for
add-backs, then DOWN for manual removals). The blocklist is ONE merged list, so
mapping it onto those categories is a judgment call: the CATEGORY sets below are
that mapping, kept explicit so they can be reviewed / edited before any number
goes on screen. The clean sets (single letters / greek / interjections /
profanity) come straight from the blocklist's own section headers; ROMAN,
INITIALISM and PROPER are hand-assigned; everything else in the pool is an
ABBREVIATION.

    .venv/bin/python math/wordlist_steps.py
"""
from __future__ import annotations

from pathlib import Path

from spylls.hunspell import Dictionary
from wordfreq import get_frequency_dict, zipf_frequency

DATA = Path(__file__).resolve().parent / "data"
CUTOFF = 2.5  # the game cutoff (wordlist.DEFAULT_ZIPF); "~1 per 3M" ~= zipf 2.52
WORDLIST = "large"

# --- hand-assigned category sets (EDIT THESE) ---------------------------------
# True roman numerals only (unit symbols cc/cl/cm/ml/mm/dc that happen to be
# valid numerals live in INITIALISM instead).
ROMAN = set("""
ii iii iv ix vi vii viii xi xii xiii xiv xix xv xvi xvii xviii xx xxi xxii
xxiii xxiv xxx
""".split())

# Acronyms, technical letter-abbreviations, and metric unit symbols.
INITIALISM = set("""
ac aka asap bf bpm bps cc cg cl cm cw db dc dds dpi emf fps ftp gm hf hp jg kc
kg kl km kph kw lb lbs mg mks ml mm mp mpg mph ms oz pm ppm rpm rps tb vb vhf
""".split())

# Proper nouns (brands / places / teams / people) + foreign-name residue +
# stray slang -- the stuff hunspell wrongly KEPT that gets removed by hand.
# This is the "down" half of the final disagreed-with-spellchecker beat.
PROPER = set("""
airbus avengers balboa bally baptist baptists bates bolivar calumet cavaliers
chamberlain cheerios christian colleen corvettes degas dodgers droid dunning
emirates everglades freemasonry gillies graham hamburg jaguars lassie mahatma
maria mayflower medicaid medicare midlands monsieur morocco nickelodeon oeuvres
panama politburo protestants redskins riviera rogers schilling smurfs snider
somerset sputnik vela waldo twink
""".split())


def load_sections(path: Path) -> list[tuple[str, list[str]]]:
    """Parse a curated list into (section-header, [words]) in file order."""
    sections: list[tuple[str, list[str]]] = []
    header, words = "(preamble)", []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("# ----"):
            if words:
                sections.append((header, words))
            header, words = s.strip("# -"), []
            continue
        s = s.split("#", 1)[0].strip()
        if s:
            words.append(s)
    if words:
        sections.append((header, words))
    return sections


def compute() -> dict:
    """Reproduce the pipeline and return the scene-03 counter data as a dict:

        {cutoff, anchors:{start,non_letter,hunspell,final},
         deltas:{non_letter,hunspell},
         categories:[{name,count,members}, ...  in video (removal) order],
         addbacks:[...], proper_down:{count,members}}

    `categories` are the NAMED removal steps (abbreviations, single letters,
    initialisms, roman numerals, interjections, profanity, greek letters);
    proper_down / addbacks are the two halves of the final "disagreed with the
    spellchecker" beat (down / up). Reconciles: hunspell - sum(categories) -
    proper_down + addbacks == final == 34,483.
    """
    speller = Dictionary.from_files("en_US")
    freqs = get_frequency_dict("en", wordlist=WORDLIST)
    zf = lambda w: zipf_frequency(w, "en", wordlist=WORDLIST)

    # --- anchors (independent of the removal buckets) ---
    at_cutoff = [w for w in freqs if zf(w) >= CUTOFF]
    alpha = [w for w in at_cutoff if w.isascii() and w.isalpha() and w.islower()]
    hunspell_kept = {w for w in alpha if speller.lookup(w)}
    n0, n1, n2 = len(at_cutoff), len(alpha), len(hunspell_kept)

    # --- classify every in-scope blocklist word into a video category ---
    sections = load_sections(DATA / "blocklist.txt")
    def in_scope(hdr_key):
        return [w for hdr, ws in sections if hdr_key in hdr
                for w in ws if w in hunspell_kept]
    single = in_scope("length 1")
    greek = in_scope("Greek letter")
    interj = in_scope("interjections")
    prof = in_scope("profanity")
    named_clean = set(single) | set(greek) | set(interj) | set(prof)

    pool = [w for hdr, ws in sections for w in ws
            if w in hunspell_kept and w not in named_clean]
    roman = [w for w in pool if w in ROMAN]
    initial = [w for w in pool if w in INITIALISM]
    proper = [w for w in pool if w in PROPER]
    abbrev = [w for w in pool if w not in ROMAN | INITIALISM | PROPER]

    # sanity: partition must cover the pool exactly, no overlaps
    assert len(roman) + len(initial) + len(proper) + len(abbrev) == len(pool)

    # --- allowlist add-backs: hunspell REJECTED but >= cutoff ---
    allow = [w for _, ws in load_sections(DATA / "allowlist.txt") for w in ws]
    addbacks = [w for w in allow if w not in hunspell_kept and zf(w) >= CUTOFF
                and w.isascii() and w.isalpha() and w.islower()]

    # named removal steps, in the video's narrated order
    categories = [
        {"name": "abbreviations", "count": len(abbrev), "members": sorted(abbrev)},
        {"name": "single letters", "count": len(single), "members": sorted(single)},
        {"name": "initialisms", "count": len(initial), "members": sorted(initial)},
        {"name": "roman numerals", "count": len(roman), "members": sorted(roman)},
        {"name": "interjections", "count": len(interj), "members": sorted(interj)},
        {"name": "profanity", "count": len(prof), "members": sorted(prof)},
        {"name": "greek letters", "count": len(greek), "members": sorted(greek)},
    ]
    final = n2 - sum(c["count"] for c in categories) - len(proper) + len(addbacks)
    assert final == 34483, f"reconcile failed: {final}"
    return {
        "cutoff": CUTOFF,
        "anchors": {"start": n0, "non_letter": n1, "hunspell": n2, "final": final},
        "deltas": {"non_letter": n0 - n1, "hunspell": n1 - n2},
        "categories": categories,
        "addbacks": sorted(addbacks),
        "proper_down": {"count": len(proper), "members": sorted(proper)},
    }


def main() -> None:
    d = compute()
    a = d["anchors"]
    print(f"cutoff zipf >= {d['cutoff']}  (wordlist={WORDLIST!r})\n")
    n = a["start"]
    print(f"  start  wordfreq @ cutoff        {n:>7,}")

    def line(label, delta, up=False):
        nonlocal n
        n += delta if up else -delta
        print(f"  {label:<28}{'+' if up else '−'}{delta:<6,} {n:>7,}")

    line("drop non-letter chars", d["deltas"]["non_letter"])
    line("hunspell spellcheck", d["deltas"]["hunspell"])
    for c in d["categories"]:
        line(c["name"], c["count"])
    print(f"    (narrative: fake −1 for pi, then +1 pi -> back to {n:,})")
    print("  disagreed w/ spellchecker:")
    line("  add-backs (up)", len(d["addbacks"]), up=True)
    line("  proper nouns/misc (down)", d["proper_down"]["count"])
    print(f"\n  FINAL {n:,}   (target 34,483 -> {'OK' if n == 34483 else 'MISMATCH'})")

    print("\n--- category members (edit ROMAN/INITIALISM/PROPER at top of file) ---")
    groups = [(c["name"], c["members"]) for c in d["categories"]]
    groups += [("proper/misc (disagreements down)", d["proper_down"]["members"]),
               ("add-backs (disagreements up)", d["addbacks"])]
    for name, ws in groups:
        print(f"\n[{len(ws)}] {name}:")
        for i in range(0, len(ws), 14):
            print("   " + " ".join(ws[i:i + 14]))


if __name__ == "__main__":
    main()

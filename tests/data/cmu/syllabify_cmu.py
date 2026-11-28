"""Syllabify the CMU Pronouncing Dictionary with Kyle Gorman's syllabifier.

Writes a CSV with one row per dictionary entry:

    word, pronunciation, syllabification

``word`` is the dictionary headword; ``pronunciation`` is the unsyllabified
ARPABET string; ``syllabification`` is the output of ``syllabify.pprint``,
where syllables are separated by ``.`` and each syllable is written
``onset-nucleus-coda`` (e.g. ``M-IH1-N.S T R-AH0-L`` for MINSTREL). Entries
the syllabifier cannot handle (e.g. pronunciations with no vowel) get an
empty syllabification.

Alternate pronunciations: CMUdict lists extra pronunciations of a word as
separate entries with a numbered marker (``A  AH0``, ``A(1)  EY1``). The
marker is stripped from ``word``, and each pronunciation keeps its own row,
so a word with alternates appears on several rows that differ only in
``pronunciation`` and ``syllabification``::

    A,AH0,-AH0-
    A,EY1,-EY1-

Rows stay in dictionary order, so the original variant number can be
recovered from a word's position among its rows.

Usage:
    python syllabify_cmu.py [--dict cmudict_0.7b.txt] [--output cmudict_syllabified.txt]
                            [--no-alaska-rule]
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from syllabify import pprint, syllabify

HERE = Path(__file__).resolve().parent
VARIANT_RE = re.compile(r"\(\d+\)$")


def read_cmudict(path):
    """Yield (word, phones) pairs from a CMUdict file, skipping comments."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";;;"):
                continue
            word, _, pron = line.partition("  ")
            yield VARIANT_RE.sub("", word), pron.split()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dict", default=HERE / "cmudict_0.7b.txt", type=Path)
    parser.add_argument("--output", default=HERE / "cmudict_syllabified.txt", type=Path)
    parser.add_argument(
        "--no-alaska-rule",
        action="store_true",
        help="Disable the 'Alaska rule' (s after a lax vowel goes to the coda).",
    )
    args = parser.parse_args()

    n_rows = 0
    failures = []
    with open(args.output, "w") as out:
        # Line terminator set to \n on purpose
        # The default is otherwise CRLF (rather than OS default)
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["word", "pronunciation", "syllabification"])
        for word, phones in read_cmudict(args.dict):
            try:
                syllabified = pprint(syllabify(phones, alaska_rule=not args.no_alaska_rule))
            except ValueError:
                syllabified = ""
                failures.append((word, " ".join(phones)))
            writer.writerow([word, " ".join(phones), syllabified])
            n_rows += 1

    print(f"Wrote {n_rows} entries to {args.output}", file=sys.stderr)
    if failures:
        print(f"{len(failures)} entries could not be syllabified:", file=sys.stderr)
        for word, pron in failures:
            print(f"  {word}\t{pron}", file=sys.stderr)


if __name__ == "__main__":
    main()

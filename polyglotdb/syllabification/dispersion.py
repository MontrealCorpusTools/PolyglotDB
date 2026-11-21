"""Complexity rankings of demisyllables, following Clements (1990, sec. 17.5).

A syllable is split into two overlapping demisyllables: the initial demisyllable
(onset + peak) and the final demisyllable (peak + coda). The dispersion of a
demisyllable is

    D = sum(1 / d_i ** 2)

where each d_i is the distance in sonority rank between one pair of its segments,
including nonadjacent pairs (ex. 16, p. 304). The preferred initial demisyllable
minimizes D and the preferred final demisyllable maximizes D (ex. 19).

Demisyllables are compared only within a cohort: those with the same position, the
same peak class, and the same length. Within a cohort, the complexity rank is the
position of a demisyllable's D among the cohort's distinct values of D, ordered
ascending for initial and descending for final demisyllables (ex. 20). Demisyllables
with equal D share a rank, and the next rank is one higher (Tables 17.1, 17.3, 17.4).

A demisyllable consisting of the peak alone has no D. It is ranked as part of the
length-2 cohort: one above the most complex two-member demisyllable if initial, and
0 if final (Table 17.2, p. 306). Clements states this only for vowel peaks; applying
it to syllabic consonant peaks is an extension made here.

Only core demisyllables are ranked: those whose margin rises strictly in sonority
toward the peak (initial) or falls strictly away from it (final), with every margin
segment lower in sonority than the peak. Since there are only finitely many of them,
they are all ranked once, in `COMPLEXITY`.
"""

from collections import defaultdict
from collections.abc import Iterator, Mapping
from enum import Enum, auto
from fractions import Fraction
from itertools import combinations
from typing import NamedTuple

from typing_extensions import override

from polyglotdb.syllabification.sonority import SonorityClass


class Position(Enum):
    """Position of a demisyllable within its syllable."""

    INITIAL = auto()
    FINAL = auto()


class Cohort(NamedTuple):
    """A set of demisyllables whose complexity ranks are comparable."""

    position: Position
    peak: SonorityClass
    length: int


class Demisyllable(NamedTuple):
    """A demisyllable, described by the sonority classes of its segments.

    `peak` is the class of the syllabic peak, whose rank is its class value plus one.
    `margin` holds the classes of the nonsyllabic segments in word order: the onset
    of an initial demisyllable or the coda of a final one.
    """

    position: Position
    peak: SonorityClass
    margin: tuple[SonorityClass, ...]

    @property
    def length(self) -> int:
        return len(self.margin) + 1

    @property
    def cohort(self) -> Cohort:
        # A peak alone is ranked as part of the length-2 cohort (Table 17.2)
        return Cohort(self.position, self.peak, max(self.length, 2))

    @property
    def ranks(self) -> tuple[int, ...]:
        """Sonority rank of each segment, in word order."""
        margin = tuple(int(cls) for cls in self.margin)
        peak = int(self.peak) + 1
        if self.position is Position.INITIAL:
            return (*margin, peak)
        return (peak, *margin)

    @override
    def __str__(self) -> str:
        peak = "V" if self.peak is SonorityClass.VOCOID else str(self.peak) + "̩"
        margin = "".join(str(cls) for cls in self.margin)
        if self.position is Position.INITIAL:
            return margin + peak
        return peak + margin


def dispersion(demisyllable: Demisyllable) -> Fraction:
    """Return the dispersion D of a demisyllable (ex. 16).

    D is computed exactly so that demisyllables with equal D compare equal.

    Raises
    ------
    ValueError
        If D is undefined: the demisyllable is a peak alone, or two of its segments
        have the same sonority rank.
    """
    if demisyllable.length < 2:
        raise ValueError(f"D is undefined for {demisyllable}: peak alone")
    total = Fraction(0)
    for a, b in combinations(demisyllable.ranks, 2):
        if a == b:
            raise ValueError(f"D is undefined for {demisyllable}: sonority plateau")
        total += Fraction(1, (a - b) ** 2)
    return total


def _core_demisyllables() -> Iterator[Demisyllable]:
    """Yield every core demisyllable, for every position and peak class."""
    for peak in SonorityClass:
        # Nonsyllabic classes ranking lower than the syllabic peak
        below = [cls for cls in SonorityClass if cls <= peak]
        for length in range(len(below) + 1):
            for margin in combinations(below, length):
                yield Demisyllable(Position.INITIAL, peak, margin)
                yield Demisyllable(Position.FINAL, peak, margin[::-1])


def _rank_core_demisyllables() -> dict[Demisyllable, int]:
    cohorts: defaultdict[Cohort, list[Demisyllable]] = defaultdict(list)
    for demisyllable in _core_demisyllables():
        cohorts[demisyllable.cohort].append(demisyllable)

    complexity: dict[Demisyllable, int] = {}
    for cohort, members in cohorts.items():
        ranked = [d for d in members if d.length >= 2]
        values = sorted(
            {dispersion(d) for d in ranked},
            reverse=cohort.position is Position.FINAL,
        )
        for d in ranked:
            complexity[d] = values.index(dispersion(d)) + 1

        for d in members:
            if d.length == 1:
                if cohort.position is Position.INITIAL:
                    complexity[d] = max(complexity[r] for r in ranked) + 1
                else:
                    complexity[d] = 0

    return complexity


COMPLEXITY: Mapping[Demisyllable, int] = _rank_core_demisyllables()
"""Complexity rank of every core demisyllable."""

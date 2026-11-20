from collections.abc import Callable, Sequence
from enum import Enum, auto

from typing_extensions import override

from polyglotdb.syllabification.sonority import SonorityClass
from polyglotdb.types import Syllabifier, Syllable, Word


class _Constituent(Enum):
    ONSET = auto()
    NUCLEUS = auto()
    CODA = auto()


class SonoritySyllabifier(Syllabifier):
    to_syllabicity: Callable[[Word], Sequence[bool]]
    to_sonority: Callable[[Word], Sequence[SonorityClass]]

    # TODO: Add dispersion principle
    def __init__(
        self,
        to_syllabicity: Callable[[Word], Sequence[bool]],
        to_sonority: Callable[[Word], Sequence[SonorityClass]],
    ):
        self.to_syllabicity = to_syllabicity
        self.to_sonority = to_sonority

    # TODO: What happens when there are no syllabics?
    @override
    def syllabify(self, word: Word) -> list[Syllable]:
        if not word:
            return []

        syllabicity = self.to_syllabicity(word)
        sonority = self.to_sonority(word)

        if len(syllabicity) != len(word) or len(sonority) != len(word):
            raise ValueError(
                "Sequences returned by to_syllabicity and to_sonority must have the same length as the word"
            )

        # Sonority value adjusted to account for syllabicity
        sonority_adjusted = [
            s.value + 1 if syllabicity[i] else s.value for i, s in enumerate(sonority)
        ]

        # Step 1: Assign NUCLEUS to syllabics
        constituents = [_Constituent.NUCLEUS if s else None for s in syllabicity]

        # Step 2: Adjoin lower sonority segments to the left
        for i in range(len(constituents) - 1, 0, -1):
            if constituents[i - 1] is _Constituent.NUCLEUS:
                continue
            # Special CV rule (p. 300)
            if constituents[i] is _Constituent.NUCLEUS:
                constituents[i - 1] = _Constituent.ONSET
            # Regular sonority rule
            elif (
                constituents[i] is _Constituent.ONSET
                and sonority_adjusted[i] > sonority_adjusted[i - 1]
            ):
                constituents[i - 1] = _Constituent.ONSET

        # Step 3: Adjoin lower sonority segments to the right
        for i in range(1, len(constituents)):
            if constituents[i] is not None:
                continue
            if constituents[i - 1] is not None and sonority_adjusted[i] < sonority_adjusted[i - 1]:
                constituents[i] = _Constituent.CODA

        # Create syllables list
        syllables: list[Syllable] = []
        cur_syllable_onset_start = 0
        cur_syllable_onset_end = 0

        for i in range(len(constituents)):
            # Syllable end
            if (
                constituents[i] is _Constituent.NUCLEUS or constituents[i] is _Constituent.CODA
            ) and (i == len(constituents) - 1 or constituents[i + 1] is not _Constituent.CODA):
                syllables.append(
                    Syllable(
                        onset=(cur_syllable_onset_start, cur_syllable_onset_end),
                        nucleus=(cur_syllable_onset_end, cur_syllable_onset_end + 1),
                        coda=(cur_syllable_onset_end + 1, i + 1),
                    )
                )

            if i == len(constituents) - 1:
                break

            # Syllable start
            if (
                constituents[i + 1] is _Constituent.NUCLEUS
                or constituents[i + 1] is _Constituent.ONSET
            ) and constituents[i] is not _Constituent.ONSET:
                cur_syllable_onset_start = i + 1
                cur_syllable_onset_end = i + 1

            # Syllable onset end
            if (
                constituents[i] is _Constituent.ONSET
                and constituents[i + 1] is _Constituent.NUCLEUS
            ):
                cur_syllable_onset_end = i + 1

        return syllables

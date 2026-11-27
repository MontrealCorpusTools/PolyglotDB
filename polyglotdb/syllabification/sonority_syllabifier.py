from collections.abc import Callable, Mapping, Sequence
from enum import Enum, auto

from typing_extensions import override

from polyglotdb.syllabification.dispersion import Demisyllable, PeakLimits, Position
from polyglotdb.syllabification.sonority import SonorityClass
from polyglotdb.types import Syllabifier, Syllable, Word


class _Constituent(Enum):
    ONSET = auto()
    NUCLEUS = auto()
    CODA = auto()


class SonoritySyllabifier(Syllabifier):
    """Syllabify words following the Core Syllabification Principle of Clements (1990).

    The syllabifier works only with the syllabicity and sonority class of each phone,
    both of which are supplied by the caller. Given a word, it:

    1. makes each syllabic phone the nucleus of its own syllable;
    2. extends each onset leftward from its nucleus, one phone at a time, as long as
       each new phone is lower in sonority than the phone after it;
    3. extends each coda rightward, one phone at a time, as long as each new phone
       has not been syllabified yet and is lower in sonority than the phone before it.

    A syllabic phone ranks one above its sonority class, so a vowel outranks a glide,
    and a syllabic liquid ranks the same as a glide.

    If `dispersion_limits` is given, a phone is adjoined in step 2 or 3 only if the
    resulting demisyllable (onset + nucleus, or nucleus + coda) is within the limits
    for its peak. Once a phone is rejected, the onset or coda stops growing.

    Phones that cannot be adjoined, such as the first of two obstruents in a sonority
    plateau (the [s] in [s k aɪ]), belong to no syllable: they fall in the gaps between
    the spans of the returned syllables. A word without syllabic phones has no
    syllables.

    Parameters
    ----------
    to_syllabicity :
        A callable object that returns, for each phone of a word, whether it is syllabic.
        It receives the whole word so that syllabicity can depend on context.
    to_sonority :
        A callable object that returns the sonority class of each phone of a word.
    dispersion_limits : Mapping[SonorityClass, PeakLimits], optional
        Limits on permisseble onsets and codas following the dispersion principle.
        Limits are specified per demisyllables type (i.e., unique combination of peak class
        and position).
    """

    to_syllabicity: Callable[[Word], Sequence[bool]]
    to_sonority: Callable[[Word], Sequence[SonorityClass]]
    dispersion_limits: Mapping[SonorityClass, PeakLimits] | None

    def __init__(
        self,
        to_syllabicity: Callable[[Word], Sequence[bool]],
        to_sonority: Callable[[Word], Sequence[SonorityClass]],
        dispersion_limits: Mapping[SonorityClass, PeakLimits] | None = None,
    ):
        self.to_syllabicity = to_syllabicity
        self.to_sonority = to_sonority
        self.dispersion_limits = dispersion_limits

    def _permits(self, demisyllable: Demisyllable) -> bool:
        """Return whether a demisyllable is within the dispersion limits, if any."""
        if self.dispersion_limits is None:
            return True
        if demisyllable.peak not in self.dispersion_limits:
            raise ValueError(f"No dispersion limits for peaks of class {demisyllable.peak.name}")
        limits = self.dispersion_limits[demisyllable.peak]
        if demisyllable.position is Position.INITIAL:
            return limits.initial.permits(demisyllable)
        return limits.final.permits(demisyllable)

    @override
    def syllabify(self, word: Word) -> list[Syllable]:
        """Divide a word into syllables.

        Returns
        -------
        list[Syllable]
            The syllables of the word, in order. Phones that belong to no syllable are
            not covered by any syllable's span.

        Raises
        ------
        ValueError
            If `to_syllabicity` or `to_sonority` does not return one value per phone,
            or if `dispersion_limits` has no entry for a peak class in the word.
        """
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
        peak = 0
        for i in range(len(constituents) - 1, 0, -1):
            if constituents[i] is _Constituent.NUCLEUS:
                peak = i
            if constituents[i - 1] is _Constituent.NUCLEUS:
                continue
            if (
                constituents[i] is not None and sonority_adjusted[i] > sonority_adjusted[i - 1]
            ) and self._permits(
                Demisyllable(Position.INITIAL, sonority[peak], tuple(sonority[i - 1 : peak]))
            ):
                constituents[i - 1] = _Constituent.ONSET

        # Step 3: Adjoin lower sonority segments to the right
        peak = 0
        for i in range(1, len(constituents)):
            if constituents[i - 1] is _Constituent.NUCLEUS:
                peak = i - 1
            if constituents[i] is not None:
                continue
            if (
                constituents[i - 1] is not None
                and sonority_adjusted[i] < sonority_adjusted[i - 1]
                and self._permits(
                    Demisyllable(Position.FINAL, sonority[peak], tuple(sonority[peak + 1 : i + 1]))
                )
            ):
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

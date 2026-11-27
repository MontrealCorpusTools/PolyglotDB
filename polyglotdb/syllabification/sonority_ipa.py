"""Default sonority classes of IPA segments."""

import unicodedata
from collections.abc import Iterable, Mapping

from polyglotdb.syllabification.sonority import SonorityClass

# Changing this would break the special rule for diphthongs below
_NORMAL_FORM = "NFC"


def _normalize(segment: str) -> str:
    return unicodedata.normalize(_NORMAL_FORM, segment)


def _normalize_keys(pairs: Iterable[tuple[str, SonorityClass]]) -> dict[str, SonorityClass]:
    """Build a mapping keyed by normalized segments, rejecting duplicate segments."""
    normalized: dict[str, SonorityClass] = {}
    for segment, cls in pairs:
        key = _normalize(segment)
        if key in normalized:
            raise ValueError(f"Duplicate entries for normalized segment {key!r}")
        normalized[key] = cls
    return normalized


# fmt: off
_DEFAULT_SEGMENTS: dict[SonorityClass, tuple[str, ...]] = {
    SonorityClass.OBSTRUENT: (
        # Plosives
        "p", "b", "t", "d", "ʈ", "ɖ", "c", "ɟ", "k", "g", "ɡ", "q", "ɢ", "ʡ",
        # Implosives
        "ɓ", "ɗ", "ᶑ", "ʄ", "ɠ", "ʛ",
        # Clicks
        "ʘ", "ǀ", "ǃ", "ǂ", "ǁ",
        # Fricatives ([ʁ] is listed as a fricative here; override it for languages
        # where it patterns as a liquid)
        "ɸ", "β", "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ", "ʂ", "ʐ", "ç", "ʝ",
        "x", "ɣ", "χ", "ʁ", "ħ", "ʕ", "ʜ", "ʢ", "ɕ", "ʑ", "ɧ",
        # Lateral fricatives
        "ɬ", "ɮ", "ꞎ",
        # Affricates
        "p͡f", "b͡v", "t͡θ", "d͡ð", "t͡s", "d͡z", "t͡ʃ", "d͡ʒ", "ʈ͡ʂ", "ɖ͡ʐ",
        "t͡ɕ", "d͡ʑ", "c͡ç", "ɟ͡ʝ", "k͡x", "q͡χ", "t͡ɬ", "d͡ɮ",
        # Affricates without a tie bar
        "pf", "bv", "tθ", "dð", "ts", "dz", "tʃ", "dʒ", "ʈʂ", "ɖʐ",
        "tɕ", "dʑ", "cç", "ɟʝ", "kx", "qχ", "tɬ", "dɮ",
        # Affricate ligatures (non-standard but widely used)
        "ʦ", "ʣ", "ʧ", "ʤ", "ʨ", "ʥ",
        # Doubly articulated plosives
        "k͡p", "ɡ͡b",
    ),
    SonorityClass.NASAL: (
        # [ȵ] is a common non-IPA symbol for the alveolo-palatal nasal
        "m", "ɱ", "n", "ɳ", "ɲ", "ȵ", "ŋ", "ɴ", "ŋ͡m",
    ),
    SonorityClass.LIQUID: (
        # Laterals (approximants and flap; [ɫ] is the velarized l)
        "l", "ɭ", "ʎ", "ʟ", "ɫ", "ɺ",
        # Rhotics (trills, taps/flaps, approximants)
        "r", "ɾ", "ɽ", "ɹ", "ɻ", "ʀ",
    ),
    SonorityClass.VOCOID: (
        # Glides ([ʍ] is turbulent only because it is voiceless, so it counts as an
        # approximant under Clements' definition, p. 293)
        "j", "w", "ɥ", "ɰ", "ʋ", "ʍ",
        # Vowels
        "i", "y", "ɨ", "ʉ", "ɯ", "u", "ɪ", "ʏ", "ʊ", "ᵻ", "ᵿ",
        "e", "ø", "ɘ", "ɵ", "ɤ", "o", "ə", "ɛ", "œ", "ɜ", "ɞ", "ʌ", "ɔ",
        "æ", "ɐ", "a", "ɶ", "ä", "ɑ", "ɒ", "ɚ", "ɝ",
    ),
}
# fmt: on

IPA_SONORITY_CLASSES: Mapping[str, SonorityClass] = _normalize_keys(
    (segment, cls) for cls, segments in _DEFAULT_SEGMENTS.items() for segment in segments
)
"""Default sonority class of each IPA segment, keyed by normalized segment."""

AMBIGUOUS_SEGMENTS: frozenset[str] = frozenset(
    _normalize(segment)
    for segment in (
        # Laryngeals do not pattern uniformly across languages (Clements 1990, sec. 17.7.2)
        "h", "ɦ", "ʔ",
        # Non-lingual trills/flaps fit none of the classes under their usual definitions
        "ʙ", "ⱱ",
    )
)  # fmt: skip
"""Segments with no default sonority class; they need an explicit override."""


def get_sonority_class(
    segment: str, overrides: Mapping[str, SonorityClass] | None = None
) -> SonorityClass:
    """Return the Clements (1990) sonority class of an IPA segment.

    The segment and the keys of `overrides` are normalized, then the segment is
    matched as a whole string, first against `overrides` and then against
    `IPA_SONORITY_CLASSES`. Diacritics are not stripped: ``"tʰ"`` must be in the
    overrides to be recognized.

    Parameters
    ----------
    segment : str
        An IPA segment.
    overrides : Mapping[str, SonorityClass], optional
        Classes that take precedence over the defaults. Required for any segment in
        `AMBIGUOUS_SEGMENTS` and for segments missing from `IPA_SONORITY_CLASSES`.

    Returns
    -------
    SonorityClass
        The sonority class of the segment.

    Raises
    ------
    ValueError
        If two keys of `overrides` normalize to the same segment, or if the segment
        matches neither `overrides` nor `IPA_SONORITY_CLASSES`.
    """
    key = _normalize(segment)

    if overrides:
        normalized_overrides = _normalize_keys(overrides.items())
        if key in normalized_overrides:
            return normalized_overrides[key]

    if key in IPA_SONORITY_CLASSES:
        return IPA_SONORITY_CLASSES[key]

    # Special rule for diphthongs, triphthongs, etc.
    if len(key) >= 2 and all(
        IPA_SONORITY_CLASSES.get(part) == SonorityClass.VOCOID for part in key
    ):
        return SonorityClass.VOCOID

    if key in AMBIGUOUS_SEGMENTS:
        raise ValueError(
            f"{segment!r} has no default sonority class; provide one through `overrides`"
        )
    raise ValueError(f"No sonority class for segment {segment!r}; provide one through `overrides`")

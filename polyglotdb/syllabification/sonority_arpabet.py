"""Default sonority classes of symbols in (the case-insensitive version of) ARPABET."""

from collections.abc import Mapping

from polyglotdb.syllabification import sonority_ipa
from polyglotdb.syllabification.sonority import SonorityClass

ARPABET_TO_IPA: Mapping[str, str] = {
    # Vowels
    "AA": "ɑ",  # Wikipedia gives ɑ ~ ɒ
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔ",
    "AW": "aʊ",
    "AX": "ə",
    "AXR": "ɚ",
    "AY": "aɪ",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "IH": "ɪ",
    "IX": "ɨ",
    "IY": "i",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "UH": "ʊ",
    "UW": "u",
    "UX": "ʉ",
    # Consonants
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "DX": "ɾ",
    "EL": "l",  # l̩
    "EM": "m",  # m̩
    "EN": "n",  # n̩
    "F": "f",
    "G": "ɡ",
    "H": "h",  # no default class: ambiguous laryngeal
    "HH": "h",  # no default class: ambiguous laryngeal
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    # Wikipedia lists NX both as a variant of NG and as the TIMIT nasal flap; CMUdict
    # uses NG, so NX is taken in its TIMIT sense here
    "NX": "ɾ̃",  # no default class: nasalization diacritic
    "P": "p",
    "Q": "ʔ",  # no default class: ambiguous laryngeal
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "V": "v",
    "W": "w",
    "WH": "ʍ",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
    # TIMIT additions
    "AX-H": "ə",  # ə̥
    "BCL": "b",  # b̚
    "DCL": "d",  # d̚
    "ENG": "ŋ",  # ŋ̍
    "GCL": "ɡ",  # ɡ̚
    "HV": "ɦ",  # no default class: ambiguous laryngeal
    "KCL": "k",  # k̚
    "PCL": "p",  # p̚
    "TCL": "t",  # t̚
}
"""IPA equivalent of each ARPABET symbol. Follows https://en.wikipedia.org/wiki/ARPABET.

The fact that AXR is mapped to ɚ instead of /ɹ̩/ implies that it is assigned
`SonorityClass.VOCOID` rather than `SonorityClass.LIQUID`.

Some symbols (e.g., EL, BCL) are mapped to the base IPA symbols without diacritics if
the diacritics do not affect the class to which they are assigned. Note that syllabicity
is considered separately. In these cases, the original symbol is denoted in the trailing
comment.
"""


def _normalize(symbol: str) -> str:
    return symbol.upper().rstrip("0123456789")


def _normalize_keys(overrides: Mapping[str, SonorityClass]) -> dict[str, SonorityClass]:
    normalized: dict[str, SonorityClass] = {}
    for symbol, cls in overrides.items():
        key = _normalize(symbol)
        if key in normalized:
            raise ValueError(f"Duplicate overrides for normalized ARPABET symbol {key!r}")
        normalized[key] = cls
    return normalized


def arpabet_to_ipa(symbol: str) -> str:
    """Return the IPA equivalent of an ARPABET symbol.

    Raises
    ------
    ValueError
        If the symbol is not in `ARPABET_TO_IPA`.
    """
    key = _normalize(symbol)
    if key not in ARPABET_TO_IPA:
        raise ValueError(f"Unknown ARPABET symbol {symbol!r}")
    return ARPABET_TO_IPA[key]


def get_sonority_class(
    symbol: str, overrides: Mapping[str, SonorityClass] | None = None
) -> SonorityClass:
    """Return the Clements (1990) sonority class of an (case-insensitive) ARPABET symbol.

    With the exception of explicitly provided overrides, each ARPABET symbol is converted
    to IPA (see `ARPABET_TO_IPA`), and its sonority class is then looked up through
    `sonority_ipa.get_sonority_class`. Stress and auxiliary symbols are ignored.

    Some symbols map to IPA segments that have no default class in `sonority_ipa`
    (diphthongs, segments with diacritics, and laryngeals); they need an override.

    Raises
    ------
    ValueError
        If two keys of `overrides` normalize to the same symbol, or if the symbol is
        not overridden and is unknown or has no default class.
    """
    key = _normalize(symbol)

    if overrides:
        normalized_overrides = _normalize_keys(overrides)
        if key in normalized_overrides:
            return normalized_overrides[key]

    ipa = arpabet_to_ipa(symbol)
    try:
        return sonority_ipa.get_sonority_class(ipa)
    except ValueError as e:
        raise ValueError(
            f"ARPABET symbol {symbol!r} (IPA {ipa!r}) has no default sonority class; "
            "provide one through `overrides`"
        ) from e

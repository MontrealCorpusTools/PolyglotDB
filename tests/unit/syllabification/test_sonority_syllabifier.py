from collections.abc import Callable, Sequence

import pytest

from polyglotdb.syllabification.dispersion import DemisyllableLimits, PeakLimits
from polyglotdb.syllabification.sonority import SonorityClass
from polyglotdb.syllabification.sonority_syllabifier import SonoritySyllabifier
from polyglotdb.types import Syllable, Word

# The syllabic diacritic, as in "L̩".
_SYLLABIC = "\u0329"


def _to_sonority(word: Word) -> Sequence[SonorityClass]:
    return [
        SonorityClass.VOCOID if phone == "G" else SonorityClass.from_letter(phone[0])
        for phone in word
    ]


def _to_syllabicity(word: Word) -> Sequence[bool]:
    return [phone == "V" or phone.endswith(_SYLLABIC) for phone in word]


@pytest.fixture
def algo() -> SonoritySyllabifier:
    return SonoritySyllabifier(to_syllabicity=_to_syllabicity, to_sonority=_to_sonority)


@pytest.mark.parametrize(
    "word, expected",
    [
        pytest.param([], [], id="empty"),
        pytest.param(["O", "N", "L", "L", "N"], [], id="no_syllabics"),
        # Cases without consonant clusters
        pytest.param(
            ["V"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1))],
            id="v",
        ),
        pytest.param(
            ["O", "V"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2))],
            id="ov",
        ),
        pytest.param(
            ["V", "O"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2))],
            id="vo",
        ),
        pytest.param(
            ["O", "V", "N"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 3))],
            id="ovn",
        ),
        pytest.param(
            ["V", "O", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 2), nucleus=(2, 3), coda=(3, 3)),
            ],
            id="v.ov",
        ),
        pytest.param(
            ["O", "V", "L", "V"],
            [
                Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="ov.lv",
        ),
        pytest.param(
            ["O", "V", "V", "O"],
            [
                Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 2), nucleus=(2, 3), coda=(3, 4)),
            ],
            id="ov.vo",
        ),
        pytest.param(
            ["V", "V", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 2), nucleus=(2, 3), coda=(3, 3)),
            ],
            id="v.v.v",
        ),
        # Cases with consonant clusters that rise toward the nucleus and fall after it
        pytest.param(
            ["O", "L", "V"],
            [Syllable(onset=(0, 2), nucleus=(2, 3), coda=(3, 3))],
            id="olv",
        ),
        pytest.param(
            ["O", "N", "L", "V"],
            [Syllable(onset=(0, 3), nucleus=(3, 4), coda=(4, 4))],
            id="onlv",
        ),
        pytest.param(
            ["V", "L", "O"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 3))],
            id="vlo",
        ),
        pytest.param(
            ["O", "L", "V", "L", "N", "O"],
            [Syllable(onset=(0, 2), nucleus=(2, 3), coda=(3, 6))],
            id="olvlno",
        ),
        # Intervocalic clusters: onsets are maximized as far as sonority allows
        pytest.param(
            ["V", "O", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="v.olv",
        ),
        pytest.param(
            ["V", "N", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="v.nlv",
        ),
        pytest.param(
            ["V", "L", "O", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="vl.ov",
        ),
        pytest.param(
            ["V", "N", "O", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 4), nucleus=(4, 5), coda=(5, 5)),
            ],
            id="vn.olv",
        ),
        pytest.param(
            ["O", "V", "L", "N", "O", "L", "V", "O"],
            [
                Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 4)),
                Syllable(onset=(4, 6), nucleus=(6, 7), coda=(7, 8)),
            ],
            id="ovln.olvo",
        ),
        # Cases that CSP cannot handle out of the box, i.e. sonority plateaus and reversals
        pytest.param(
            ["O", "O", "V"],
            [Syllable(onset=(1, 2), nucleus=(2, 3), coda=(3, 3))],
            id="initial_plateau",
        ),
        pytest.param(
            ["V", "O", "O"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2))],
            id="final_plateau",
        ),
        pytest.param(
            ["L", "O", "V"],
            [Syllable(onset=(1, 2), nucleus=(2, 3), coda=(3, 3))],
            id="initial_reversal",
        ),
        pytest.param(
            ["V", "O", "L"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2))],
            id="final_reversal",
        ),
        pytest.param(
            ["V", "O", "O", "O", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(3, 4), nucleus=(4, 5), coda=(5, 5)),
            ],
            id="medial_plateau",
        ),
    ],
)
def test_syllabify_simple(algo: SonoritySyllabifier, word: Word, expected: list[Syllable]):
    assert algo.syllabify(word) == expected


@pytest.mark.parametrize(
    "to_syllabicity, to_sonority",
    [
        pytest.param(lambda word: [True], _to_sonority, id="syllabicity"),
        pytest.param(_to_syllabicity, lambda word: [SonorityClass.VOCOID], id="sonority"),
    ],
)
def test_syllabify_length_mismatch(
    to_syllabicity: Callable[[Word], Sequence[bool]],
    to_sonority: Callable[[Word], Sequence[SonorityClass]],
):
    algo = SonoritySyllabifier(to_syllabicity=to_syllabicity, to_sonority=to_sonority)
    with pytest.raises(ValueError):
        _ = algo.syllabify(["O", "V"])


# Dispersion limits for vowel peaks: (initial, final)
_MAX_LENGTH_2 = PeakLimits(DemisyllableLimits(2, (4,)), DemisyllableLimits(2, (4,)))
_ONLY_OLV = PeakLimits(DemisyllableLimits(3, (4, 1)), DemisyllableLimits(3, (4, 4)))
_NO_GV = PeakLimits(DemisyllableLimits(2, (3,)), DemisyllableLimits(2, (4,)))
_NO_VN = PeakLimits(DemisyllableLimits(2, (4,)), DemisyllableLimits(2, (2,)))
_NO_CODAS = PeakLimits(DemisyllableLimits(2, (4,)), DemisyllableLimits(2, (0,)))


@pytest.mark.parametrize(
    "limits, word, expected",
    [
        # Maximal length
        pytest.param(
            _MAX_LENGTH_2,
            ["V", "O", "N", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="max_length_2:vo.nv",
        ),
        pytest.param(
            _MAX_LENGTH_2,
            ["V", "O", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="max_length_2:vo.lv",
        ),
        pytest.param(
            _MAX_LENGTH_2,
            ["O", "L", "V", "L", "O"],
            [Syllable(onset=(1, 2), nucleus=(2, 3), coda=(3, 4))],
            id="max_length_2:o(lvl)o",
        ),
        pytest.param(
            _MAX_LENGTH_2,
            ["V", "L", "O", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(3, 4), nucleus=(4, 5), coda=(5, 5)),
            ],
            id="max_length_2:(vl)o(lv)",
        ),
        # Maximal complexity of initial demisyllables
        pytest.param(
            _ONLY_OLV,
            ["V", "O", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="only_olv:v.olv",
        ),
        pytest.param(
            _ONLY_OLV,
            ["V", "O", "N", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="only_olv:vo.nv",
        ),
        pytest.param(
            _ONLY_OLV,
            ["V", "N", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="only_olv:vn.lv",
        ),
        pytest.param(
            _NO_GV,
            ["V", "G", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 2), nucleus=(2, 3), coda=(3, 3)),
            ],
            id="no_gv:vg.v",
        ),
        pytest.param(
            _NO_GV,
            ["V", "L", "V"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 2), nucleus=(2, 3), coda=(3, 3)),
            ],
            id="no_gv:v.lv",
        ),
        # Maximal complexity of final demisyllables
        pytest.param(
            _NO_VN,
            ["V", "L"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2))],
            id="no_vn:vl",
        ),
        pytest.param(
            _NO_VN,
            ["V", "N"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1))],
            id="no_vn:(v)n",
        ),
        pytest.param(
            _NO_CODAS,
            ["O", "V", "G"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2))],
            id="no_codas:(ov)g",
        ),
    ],
)
def test_syllabify_dispersion_limits(limits: PeakLimits, word: Word, expected: list[Syllable]):
    algo = SonoritySyllabifier(
        to_syllabicity=_to_syllabicity,
        to_sonority=_to_sonority,
        dispersion_limits={SonorityClass.VOCOID: limits},
    )
    assert algo.syllabify(word) == expected


@pytest.mark.parametrize(
    "word, expected",
    [
        pytest.param(
            ["O", "L\u0329"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2))],
            id="ol",
        ),
        pytest.param(
            ["N", "L\u0329"],
            [Syllable(onset=(1, 1), nucleus=(1, 2), coda=(2, 2))],
            id="n(l)",
        ),
    ],
)
def test_syllabify_dispersion_limits_by_peak(word: Word, expected: list[Syllable]):
    # Syllabic liquids allow only OL̩ onsets; vowels allow any CV
    algo = SonoritySyllabifier(
        to_syllabicity=_to_syllabicity,
        to_sonority=_to_sonority,
        dispersion_limits={
            SonorityClass.VOCOID: _MAX_LENGTH_2,
            SonorityClass.LIQUID: PeakLimits(
                DemisyllableLimits(2, (1,)), DemisyllableLimits(2, (3,))
            ),
        },
    )
    assert algo.syllabify(word) == expected


def test_syllabify_dispersion_limits_missing_peak():
    algo = SonoritySyllabifier(
        to_syllabicity=_to_syllabicity,
        to_sonority=_to_sonority,
        dispersion_limits={SonorityClass.VOCOID: _MAX_LENGTH_2},
    )
    with pytest.raises(ValueError):
        _ = algo.syllabify(["O", "L\u0329"])

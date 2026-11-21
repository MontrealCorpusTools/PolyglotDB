from collections.abc import Callable, Sequence

import pytest

from polyglotdb.syllabification.sonority import SonorityClass
from polyglotdb.syllabification.sonority_syllabifier import SonoritySyllabifier
from polyglotdb.types import Syllable, Word


def _to_sonority(word: Word) -> Sequence[SonorityClass]:
    return [SonorityClass.from_letter(phone) for phone in word]


def _to_syllabicity(word: Word) -> Sequence[bool]:
    return [phone == "V" for phone in word]


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

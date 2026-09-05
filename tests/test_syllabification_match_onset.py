import pytest

from polyglotdb.syllabification.match_onset import MatchOnset
from polyglotdb.types import Syllable, Word


@pytest.fixture
def algo() -> MatchOnset:
    return MatchOnset(
        onsets={("k",), ("s", "k"), ("s", "k", "r")},
        syllabics={"iy", "aa"},
    )


@pytest.mark.parametrize(
    "word, expected",
    [
        pytest.param([], [], id="empty"),
        # Cases without consonant clusters
        pytest.param(
            ["iy"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1))],
            id="v",
        ),
        pytest.param(
            ["k", "iy"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2))],
            id="cv",
        ),
        pytest.param(
            ["iy", "t"],
            [Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2))],
            id="vc",
        ),
        pytest.param(
            ["k", "iy", "t"],
            [Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 3))],
            id="cvc",
        ),
        pytest.param(
            ["k", "iy", "k", "aa"],
            [
                Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="cvcv",
        ),
        pytest.param(
            ["k", "iy", "aa", "t"],
            [
                Syllable(onset=(0, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 2), nucleus=(2, 3), coda=(3, 4)),
            ],
            id="cvvc",
        ),
        pytest.param(
            ["iy", "aa", "iy"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 1), nucleus=(1, 2), coda=(2, 2)),
                Syllable(onset=(2, 2), nucleus=(2, 3), coda=(3, 3)),
            ],
            id="vvv",
        ),
        # Cases with consonant clusters
        pytest.param(
            ["s", "k", "iy"],
            [Syllable(onset=(0, 2), nucleus=(2, 3), coda=(3, 3))],
            id="ccv",
        ),
        pytest.param(
            ["s", "k", "r", "iy"],
            [Syllable(onset=(0, 3), nucleus=(3, 4), coda=(4, 4))],
            id="cccv",
        ),
        pytest.param(
            ["aa", "s", "k", "iy"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 1)),
                Syllable(onset=(1, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="v.ccv",
        ),
        pytest.param(
            ["aa", "r", "t", "iy"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 3)),
                Syllable(onset=(3, 3), nucleus=(3, 4), coda=(4, 4)),
            ],
            id="vcc.v",
        ),
        pytest.param(
            ["aa", "t", "s", "k", "iy"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 2)),
                Syllable(onset=(2, 4), nucleus=(4, 5), coda=(5, 5)),
            ],
            id="vc.ccv",
        ),
        pytest.param(
            ["aa", "s", "k", "r"],
            [
                Syllable(onset=(0, 0), nucleus=(0, 1), coda=(1, 4)),
            ],
            id="vccc",
        ),
        # Degenerate syllables
        pytest.param(
            ["k"],
            [Syllable(onset=(0, 1), nucleus=(1, 1), coda=(1, 1))],
            id="degenerate_onset_only",
        ),
        pytest.param(
            ["t"],
            [Syllable(onset=(0, 0), nucleus=(0, 0), coda=(0, 1))],
            id="degenerate_coda_only",
        ),
        pytest.param(
            ["s", "k", "t"],
            [Syllable(onset=(0, 2), nucleus=(2, 2), coda=(2, 3))],
            id="degenerate_onset_coda",
        ),
    ],
)
def test_syllabify_simple(algo: MatchOnset, word: Word, expected: list[Syllable]):
    assert algo.syllabify(word) == expected


@pytest.mark.parametrize(
    "word",
    [
        pytest.param(["t", "iy"], id="cv"),
        pytest.param(["k", "t", "iy"], id="ccv"),
    ],
)
def test_syllabify_impermissible_onset(algo: MatchOnset, word: Word):
    with pytest.raises(ValueError):
        algo.syllabify(word)

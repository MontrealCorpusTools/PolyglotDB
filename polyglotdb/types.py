"""Some type definitions.

This file is currently WIP. Definitions in this file are only used in new code
related to syllabification. However, since we should move towards adopting an OGM,
many of these types will eventually be rewritten.
"""
from typing import NamedTuple, Protocol

type Phone = str
type Word = list[Phone]


class Syllable(NamedTuple):
    """The boundaries of a syllable in a word.

    Each of `onset`, `nucleus`, and `coda` is a pair of start/end indices indicating
    the slice of the word's phone sequence that corresponds to the syllable constituent.
    For example, for the word ['k', 'ae', 't', 's'], we would have the following values:

    - `onset`: (0, 1)
    - `nucleus`: (1, 2)
    - `coda`: (2, 4)

    For now, for any well-formed syllable, we assume that `onset[1] == nucleus[0]`
    and `nucleus[1] == coda[0]`. Following existing code, we also assume that the
    nucleus has either zero or one phone. Note that these are preconditions that
    the syllabification algorithm must verify by itself.
    """

    onset: tuple[int, int]
    nucleus: tuple[int, int]
    coda: tuple[int, int]


class SyllabificationAlgo(Protocol):
    def syllabify(self, word: Word) -> list[Syllable]:
        ...

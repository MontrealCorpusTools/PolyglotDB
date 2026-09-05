from typing import LiteralString, cast

from polyglotdb.corpus.context import CorpusContext
from polyglotdb.types import Phone, SyllabificationAlgo, Syllable, Word


class MatchOnset(SyllabificationAlgo):
    """Syllabify by matching against a set of onsets, choosing the longest match.

    The algorithm is initialized with a set of permissible onsets and a set of syllabic
    segments. Upon calling `syllabify()` given a word, for each list of segments between
    two syllabic segments, the algorithm tries to find the longest suffix that is a
    permissible onset. All remaining segments before the suffix are syllabified as
    a coda.

    The list of segments before the first syllabic segment is syllabified as an onset
    if it is permissible. Otherwise, a `ValueError` is raised. The list of segments
    after the last syllabic segment is always syllabified as a coda.

    If no syllabic segments are found, the algorithm will try to find the longest
    prefix that is a permissible onset and syllabify the remaining segments as a coda.
    If no onset is found, the algorithm will syllabify the entire word as a coda.
    """

    onsets: set[tuple[Phone, ...]]
    syllabics: set[Phone]

    def __init__(self, onsets: set[tuple[Phone, ...]], syllabics: set[Phone]):
        self.syllabics = syllabics
        self.onsets = onsets

    @classmethod
    def from_corpus(cls, corpus: CorpusContext):
        """Initialize the algorithm by finding onsets and syllabics from the corpus.

        Specifically, onsets are found using `CorpusContext.find_onsets()`.
        Syllabics are initialized to the segments previously designated as
        syllabics using `CorpusContext.encode_syllabic_segments()`.
        """
        query = cast(
            LiteralString,
            f"MATCH (n:{corpus.cypher_safe_name}:syllabic) return n.label as label",
        )
        records = corpus.graph_driver.execute_query(query).records
        syllabics = {x["label"] for x in records}

        onsets = set(corpus.find_onsets().keys())
        return cls(onsets, syllabics)

    def syllabify(self, word: Word) -> list[Syllable]:
        word_tuple = tuple(word)
        syllabic_indices = [i for i, phone in enumerate(word) if phone in self.syllabics]

        if not word:
            return []

        if not syllabic_indices:
            for i in range(len(word), 0, -1):
                if word_tuple[:i] in self.onsets:
                    return [Syllable(onset=(0, i), nucleus=(i, i), coda=(i, len(word)))]
            return [Syllable(onset=(0, 0), nucleus=(0, 0), coda=(0, len(word)))]

        syllables: list[Syllable] = []

        # Check word-initial onset permissibility
        if syllabic_indices[0] > 0 and word_tuple[: syllabic_indices[0]] not in self.onsets:
            raise ValueError(
                f"Word initial cluster {word[: syllabic_indices[0]]} in word {word} is not a permissible onset"
            )

        prev_onset_start = 0
        for i in range(len(syllabic_indices) - 1):
            next_onset_start = syllabic_indices[i] + 1
            while next_onset_start < syllabic_indices[i + 1]:
                if word_tuple[next_onset_start : syllabic_indices[i + 1]] in self.onsets:
                    break
                next_onset_start += 1
            syllables.append(
                Syllable(
                    onset=(prev_onset_start, syllabic_indices[i]),
                    nucleus=(syllabic_indices[i], syllabic_indices[i] + 1),
                    coda=(syllabic_indices[i] + 1, next_onset_start),
                )
            )
            prev_onset_start = next_onset_start

        # Append last syllable
        syllables.append(
            Syllable(
                onset=(prev_onset_start, syllabic_indices[-1]),
                nucleus=(syllabic_indices[-1], syllabic_indices[-1] + 1),
                coda=(syllabic_indices[-1] + 1, len(word)),
            )
        )

        return syllables

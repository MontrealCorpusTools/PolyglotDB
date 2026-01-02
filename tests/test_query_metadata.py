import pytest

from polyglotdb import CorpusContext


@pytest.mark.xfail
def test_query_metadata_words(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_metadata(g.word)

        assert q.factors() == ["label"]
        assert q.numerics() == ["begin", "end"]
        assert len(q.levels(g.word.label)) == 10

        assert q.range(g.word.begin) == [0, 10]
        assert len(q.grouping_factors() == 0)


@pytest.mark.xfail
def test_query_metadata_discourses(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_metadata(g.discourse)

        assert len(q.levels() == 5)

        assert len(q.grouping_factors() == 0)

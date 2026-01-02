import os

import pytest

from polyglotdb import CorpusContext


def test_enrich_lexicon(timed_config, lexicon_test_data):
    with CorpusContext(timed_config) as c:
        c.enrich_lexicon(lexicon_test_data)

        q = c.query_graph(c.word).filter(c.word.POS == "JJ")

        results = q.all()

        assert results[0].label == "cute"

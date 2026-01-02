import os

import pytest

from polyglotdb import CorpusContext


def test_encode_class(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        results = q.all()

        first_twenty = results.next(20)

        assert first_twenty == results.previous(20)

        second_twenty = results.next(20)

        assert second_twenty == results.previous(40)

        assert len(results) == 203

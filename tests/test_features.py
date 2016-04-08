
import pytest
import os

from polyglotdb import CorpusContext

from polyglotdb.exceptions import SubsetError

def test_encode_class(timed_config):
    with CorpusContext(timed_config) as g:
        label = 'encoded_class'

        g.encode_class(['ae'], label)

        q = g.query_graph(g.phone).filter(g.phone.type_subset == label)

        assert(all(x.label == 'ae' for x in q.all()))

        g.reset_class(label)

        with pytest.raises(SubsetError):
            g.phone.subset_type(label)

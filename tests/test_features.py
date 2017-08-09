import pytest
import os

from polyglotdb import CorpusContext

from polyglotdb.exceptions import SubsetError


def test_encode_class(timed_config):
    with CorpusContext(timed_config) as g:
        label = 'encoded_class'

        g.encode_class(['ae'], label)
        print(g.hierarchy.subset_types)

        q = g.query_graph(g.phone).filter(g.phone.subset == label)

        assert (all(x.label == 'ae' for x in q.all()))

        q = g.query_graph(g.phone).filter(g.phone.subset != label)
        results = q.all()
        assert (len(results) > 0)
        assert (all(x.label != 'ae' for x in results))

        g.reset_class(label)
        print(g.hierarchy.subset_types)
        with pytest.raises(SubsetError):
            g.phone.filter_by_subset(label)

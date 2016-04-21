
import pytest
import os

from polyglotdb import CorpusContext

from polyglotdb.exceptions import SubsetError

from polyglotdb.io.enrichment import enrich_features_from_csv

def test_encode_class(timed_config):
    with CorpusContext(timed_config) as g:
        label = 'encoded_class'

        g.encode_class(['ae'], label)

        q = g.query_graph(g.phone).filter(g.phone.type_subset == label)

        assert(all(x.label == 'ae' for x in q.all()))

        g.reset_class(label)

        with pytest.raises(SubsetError):
            g.phone.subset_type(label)

def test_encode_from_file(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'timed_features.txt')
    with CorpusContext(timed_config) as c:
        enrich_features_from_csv(c, path)

        q = c.query_graph(c.phone).filter(c.phone.vowel_height == 'lowhigh')

        q = q.columns(c.phone.label.column_name('label'))

        res = q.all()

        assert(all(x.label == 'ay' for x in res))

        q = c.query_graph(c.phone).filter(c.phone.place_of_articulation == 'velar')

        q = q.columns(c.phone.label.column_name('label'))

        res = q.all()

        assert(all(x.label in ['k','g'] for x in res))

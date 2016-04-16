
import pytest
import os

from polyglotdb import CorpusContext

from polyglotdb.io.enrichment import enrich_lexicon_from_csv

def test_lexicon_enrichment(timed_config, csv_test_dir):
    path = os.path.join(csv_test_dir, 'timed_enrichment.txt')
    with CorpusContext(timed_config) as c:
        enrich_lexicon_from_csv(c, path)

        q = c.query_graph(c.word).filter(c.word.neighborhood_density < 10)

        q = q.columns(c.word.label.column_name('label'))

        res = q.all()

        assert(all(x.label == 'guess' for x in res))

        q = c.query_graph(c.word).filter(c.word.label == 'i')

        res = q.all()

        assert(res[0].frequency == 150)
        assert(res[0].part_of_speech == 'PRP')
        assert(res[0].neighborhood_density == 17)

        q = c.query_graph(c.word).filter(c.word.label == 'cute')

        res = q.all()

        assert(res[0].frequency is None)
        assert(res[0].part_of_speech == 'JJ')
        assert(res[0].neighborhood_density == 14)

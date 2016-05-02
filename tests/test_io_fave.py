
import pytest
import os

from polyglotdb.io import inspect_fave

from polyglotdb import CorpusContext

from polyglotdb.exceptions import TextGridError, GraphQueryError

def test_load_fave(fave_test_dir, graph_db):
    path = os.path.join(fave_test_dir, 'fave_test.TextGrid')

    with CorpusContext('test_fave', **graph_db) as c:
        c.reset()
        parser = inspect_fave(path)
        c.load(parser, path)

        q = c.query_graph(c.word).filter(c.word.label == 'JURASSIC')
        q = q.filter(c.word.speaker.name == 'Gary Salvi')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        results = q.all()
        assert(len(results) == 1)

        q = c.query_graph(c.word).filter(c.word.label == 'JURASSIC')
        q = q.filter(c.word.speaker.name == 'Interviewer')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        results = q.all()
        assert(len(results) == 0)

        c.encode_pauses('<SIL>')

        q = c.query_graph(c.word).filter(c.word.label == 'PLANET')
        q = q.filter(c.word.speaker.name == 'Gary Salvi')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name('following'))
        results = q.all()
        assert(len(results) == 1)
        assert(results[0].following == 'JURASSIC')

        q = c.query_graph(c.word).filter(c.word.label == 'MURDER')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name('following'))
        results = q.all()
        assert(len(results) == 1)
        assert(results[0].following == 'KNOW')



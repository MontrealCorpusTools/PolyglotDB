
import pytest
import os

from polyglotdb.io import inspect_fave

from polyglotdb import CorpusContext

from polyglotdb.exceptions import TextGridError, GraphQueryError

def test_load_fave(fave_test_dir, graph_db):

    with CorpusContext('test_fave', **graph_db) as c:
        c.reset()
        parser = inspect_fave(fave_test_dir)
        c.load(parser, fave_test_dir)

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
        assert(len(results) == 2)
        assert(results[0].following == 'KNOW')

        interviewer = c.census['Interviewer']

        assert(len(interviewer.discourses) == 2)
        assert(sorted(x.name for x in interviewer.discourses) == ['fave_test', 'fave_test2'])

        s = c.census['Gary Salvi']

        assert(len(s.discourses) == 1)
        assert([x.name for x in s.discourses] == ['fave_test'])



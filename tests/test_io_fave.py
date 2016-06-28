
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
        print(q.cypher())
        results = q.all()
        assert(len(results) == 1)

        q = c.query_graph(c.word).filter(c.word.label == 'JURASSIC')
        q = q.filter(c.word.speaker.name == 'Interviewer')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        print(q.cypher())
        results = q.all()
        assert(len(results) == 0)

        c.encode_pauses('<SIL>')

        c.encode_utterances(min_pause_length = 0)

        q = c.query_graph(c.word).filter(c.word.label == 'PLANET')
        q = q.filter(c.word.speaker.name == 'Gary Salvi')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name('following'))
        print(q.cypher())
        results = q.all()
        assert(len(results) == 1)
        assert(results[0]['following'] == 'JURASSIC')

        q = c.query_graph(c.word).filter(c.word.label == 'MURDER')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name('following'))
        print(q.cypher())
        results = q.all()
        assert(len(results) == 2)
        assert(results[0]['following'] == 'KNOW')

        interviewer = c.census['Interviewer']

        assert(len(interviewer.discourses) == 2)
        assert(sorted(x.discourse.name for x in interviewer.discourses) == ['fave_test', 'fave_test2'])

        s = c.census['Gary Salvi']

        assert(len(s.discourses) == 1)
        assert([x.discourse.name for x in s.discourses] == ['fave_test'])

def test_load_fave_stereo(fave_test_dir, graph_db):

    with CorpusContext('test_stereo', **graph_db) as c:
        c.reset()
        parser = inspect_fave(fave_test_dir)
        c.load(parser, fave_test_dir)

        s = c.census['Speaker 1']

        assert(len(s.discourses) == 1)
        assert([x.channel for x in s.discourses] == [0])

        s = c.census['Speaker 2']

        assert(len(s.discourses) == 1)
        assert([x.channel for x in s.discourses] == [1])

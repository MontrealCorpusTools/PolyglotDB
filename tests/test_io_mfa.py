
import pytest
import os

from polyglotdb.io import inspect_mfa

from polyglotdb import CorpusContext

from polyglotdb.exceptions import TextGridError, GraphQueryError, ParseError

def test_load_mfa(mfa_test_dir, graph_db):

    with CorpusContext('test_mfa', **graph_db) as c:
        c.reset()
        parser = inspect_mfa(mfa_test_dir)
        c.load(parser, mfa_test_dir)
        assert(c.hierarchy.has_type_property('word', 'transcription'))


        q = c.query_graph(c.word).filter(c.word.label == 'JURASSIC')
        q = q.filter(c.word.speaker.name == 'mfa')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label)
        results = q.all()
        assert(len(results) == 1)

        c.encode_pauses('<SIL>')

        c.encode_utterances(min_pause_length = 0)

        q = c.query_graph(c.word).filter(c.word.label == 'PLANET')
        q = q.filter(c.word.speaker.name == 'mfa')
        q = q.order_by(c.word.begin)
        q = q.columns(c.word.label, c.word.following.label.column_name('following'))
        results = q.all()
        assert(len(results) == 1)
        assert(results[0]['following'] == 'JURASSIC')

        s = c.census['mfa']

        assert(len(s.discourses) == 1)
        assert([x.discourse.name for x in s.discourses] == ['mfa_test'])

def test_mismatch_parser(timit_test_dir, graph_db):

    with CorpusContext('test_mismatch', **graph_db) as c:
        c.reset()
        parser = inspect_mfa(timit_test_dir)
        with pytest.raises(ParseError):
            c.load(parser, timit_test_dir)



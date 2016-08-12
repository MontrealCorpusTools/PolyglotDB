import pytest
import os

from polyglotdb.io.parsers.partitur import PartiturParser
from polyglotdb.io.inspect.partitur import inspect_partitur
from polyglotdb import CorpusContext

def test_load_partitur(partitur_test_dir, graph_db):
	with CorpusContext('test_partitur', **graph_db) as c:
		c.reset()
		parser = inspect_partitur(partitur_test_dir)
		c.load(parser, partitur_test_dir)

		q = c.query_graph(c.word).filter(c.word.label == 'möchte')
		q = q.filter(c.word.speaker.name == 'alz')
		results = q.all()
		assert(len(results)==1)

		c.encode_pauses('<p:>')

		c.encode_utterances(min_pause_length = 0)

		q = c.query_graph(c.utterance)
		results = q.all()
		assert(len(results)==1)

		q = c.query_graph(c.word).filter(c.word.label == 'wer')
		q = q.filter(c.word.speaker.name == 'alz')
		q = q.order_by(c.word.begin)
		q = q.columns(c.word.label.column_name('label'), c.word.following.label.column_name('following'))
		results = q.all()
		assert(len(results) == 1)
		
		assert(results[0]['following'] == 'möchte')	

		s = c.census['alz']
		assert(len(s.discourses) == 1)
		assert([x.discourse.name for x in s.discourses] == ['partitur_test'])
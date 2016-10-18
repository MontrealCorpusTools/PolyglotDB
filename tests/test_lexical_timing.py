import pytest
from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig
from polyglotdb.io.enrichment import enrich_lexicon_from_csv
from polyglotdb.io import inspect_textgrid
import time

graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

path = '/Users/Elias/Desktop/SCT enrichment and tests/German/GermanEnrichmentData.csv'
config = CorpusConfig('GE', **graph_db)


def test_time():
	with CorpusContext(config) as c:
		t0 = time.clock()
		enrich_lexicon_from_csv(c,path)
		print("time elapsed: ")
		print(time.clock()-t0)
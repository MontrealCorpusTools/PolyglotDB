import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
import polyglotdb.io as aio

from polyglotdb.corpus import CorpusContext

from polyglotdb.config import CorpusConfig

graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

praat = r'C:\Users\michael\Documents\Praat\praatcon.exe'

config = CorpusConfig('buckeye', praat_path = praat, **graph_db)

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

with CorpusContext(config) as g:
    g.analyze_acoustics()

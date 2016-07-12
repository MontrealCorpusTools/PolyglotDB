import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

import polyglotdb.io as aio
from polyglotdb.config import CorpusConfig

from polyglotdb import CorpusContext


graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

praat = r'C:\Users\michael\Documents\Praat\praatcon.exe'

reaper = r'D:\Dev\Tools\REAPER-master\reaper.exe'

config = CorpusConfig('buckeye', **graph_db)

config.reaper_path = reaper
#config.praat_path = praat

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

if __name__ == '__main__':
    with CorpusContext(config) as g:
        g.encode_pauses('^[{<].*')
        g.encode_utterances(min_pause_length = 0.25)
        g.analyze_acoustics()

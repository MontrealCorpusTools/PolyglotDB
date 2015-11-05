import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
import polyglotdb.io as aio

from polyglotdb.corpus import CorpusContext

path_to_buckeye = r'D:\Data\VIC\Speakers'
#path_to_buckeye = r'D:\Data\BuckeyeSubset'

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

with CorpusContext('buckeye', **graph_db) as g:
    g.reset()
    beg = time.time()
    aio.load_directory_buckeye(g, path_to_buckeye,
                                            call_back = call_back)
    end = time.time()
    print('Time taken: {}'.format(end - beg))

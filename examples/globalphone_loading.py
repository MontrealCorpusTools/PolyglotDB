import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
#import polyglotdb.io as aio
import polyglotdb.io.textgrid as tio


from polyglotdb.corpus import CorpusContext

path_to_gp = r'D:\Data\GlobalPhone\BG'

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}



def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

reset = True

if reset:
    print("Getting annotation types..")
    annotation_types = tio.inspect_discourse_textgrid(path_to_gp)
    print('Loading corpus...')
    with CorpusContext('gp_bulgarian', **graph_db) as g:
        g.reset()
        beg = time.time()
        tio.load_directory_textgrid(g, path_to_gp, annotation_types, call_back = print)
        end = time.time()
        print('Time taken: {}'.format(end - beg))


if __name__ == '__main__':
    with CorpusContext('gp_bulgarian', **graph_db) as g:
        q = g.query_graph(g.phones).filter(g.phones.label == 'd')
        print(q.cypher())
        print(q.count())

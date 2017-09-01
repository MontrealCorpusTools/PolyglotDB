import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
import polyglotdb.io as pgio
from polyglotdb.io.parsers import FilenameSpeakerParser


from polyglotdb import CorpusContext

path_to_gp = r'D:\Data\GP_aligned\TH'

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

reset = True

if __name__ == '__main__':

    if reset:
        print("Getting annotation types..")
        parser = pgio.inspect_textgrid(path_to_gp)
        parser.speaker_parser = FilenameSpeakerParser(5)
        parser.call_back = print
        print('Loading corpus...')
        with CorpusContext('gp_thai', **graph_db) as c:
            c.reset()
            beg = time.time()
            c.load(parser, path_to_gp)
            end = time.time()
            print('Time taken: {}'.format(end - beg))

    with CorpusContext('gp_thai', **graph_db) as g:
        q = g.query_graph(g.phones).filter(g.phones.label == 'd')
        print(q.cypher())
        print(q.count())

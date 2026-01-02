import os
import sys
import time

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, base)
import polyglotdb.io as pgio
from polyglotdb import CorpusContext

path_to_buckeye = r"D:\Data\VIC\Speakers"
# path_to_buckeye = r'D:\Data\BuckeyeSubset'

graph_db = {"host": "localhost", "port": 7474, "user": "neo4j", "password": "test"}


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(" ".join(args))


with CorpusContext("buckeye", **graph_db) as c:
    c.reset()
    beg = time.time()
    parser = pgio.inspect_buckeye(path_to_buckeye)
    parser.call_back = call_back
    c.load(parser, path_to_buckeye)
    end = time.time()
    print("Time taken: {}".format(end - beg))

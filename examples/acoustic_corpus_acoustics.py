import os
import sys
import time

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, base)
import polyglotdb.io as aio
from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig

graph_db = {
    "graph_host": "localhost",
    "graph_port": 7474,
    "graph_user": "neo4j",
    "graph_password": "test",
}

praat = r"C:\Users\michael\Documents\Praat\praatcon.exe"

config = CorpusConfig("acoustic", **graph_db)

config.reaper_path = r"D:\Dev\Tools\REAPER-master\reaper.exe"


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(" ".join(args))


if __name__ == "__main__":
    with CorpusContext(config) as g:
        g.encode_pauses(["sil"])
        g.encode_utterances()
        g.analyze_acoustics()

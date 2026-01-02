import os
import sys
import time

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, base)
import polyglotdb.io as pgio
from polyglotdb import CorpusContext
from polyglotdb.io import enrich_lexicon_from_csv, enrich_speakers_from_csv

path_to_buckeye = r"D:\Data\VIC\Speakers"
# path_to_buckeye = r'D:\Data\BuckeyeSubset'

lexicon_info_path = r"D:\Data\Iphod\iphod_for_sct.txt"

graph_db = {"host": "localhost", "port": 7474, "user": "neo4j", "password": "test"}


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(" ".join(args))


with CorpusContext("buckeye", **graph_db) as c:
    begin = time.time()
    enrich_lexicon_from_csv(c, lexicon_info_path)
    print("Lexicon enrichment took:", time.time() - begin)

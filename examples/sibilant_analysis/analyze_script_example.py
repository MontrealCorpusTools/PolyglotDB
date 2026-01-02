import os
import sys
import time

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, base)

import polyglotdb.io as aio
from polyglotdb import CorpusContext
from polyglotdb.config import CorpusConfig
from polyglotdb.corpus import AudioContext
from polyglotdb.io import inspect_textgrid

# from polyglotdb.query.graph.func import Count
from polyglotdb.query.annotations.func import Count

# exports all sibilants

graph_db = {
    "graph_host": "localhost",
    "graph_port": 7474,
    "graph_user": "neo4j",
    "graph_password": "test",
}

praat_path = "C:\\Users\\samih\\Documents\\0_SPADE_labwork\\praatcon.exe"
script_path = (
    "C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\sibilant_jane.praat"
)
# script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\COG.praat'
# script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\COG_middle50percent.praat'
output_path = "C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\sib_data.csv"


config = CorpusConfig("librispeech", **graph_db)

# config = CorpusConfig('acoustic utt', **graph_db)

config.praat_path = praat_path

if __name__ == "__main__":
    with CorpusContext(config) as c:
        c.encode_class(["S", "Z", "SH", "ZH"], "sibilant")  # encode_class method is in featured.py

        begin = time.time()

        c.analyze_script("sibilant", script_path, stop_check=None, call_back=None)
        end = time.time()
        print("Analyzing sibilants for acoustic measures took: " + str(end - begin))

        q = c.query_graph(c.phone).filter(c.phone.type_subset == "sibilant")
        q = q.columns(
            c.phone.speaker.name.column_name("speaker"),
            c.phone.discourse.name.column_name("discourse"),
            c.phone.id.column_name("phone_id"),
            c.phone.label.column_name("phone_label"),
            c.phone.begin.column_name("begin"),
            c.phone.end.column_name("end"),
            c.phone.following.label.column_name("following_phone"),
            c.phone.following.following.label.column_name("2nd_following_phone"),
            c.phone.previous.label.column_name("previous_phone"),
            c.phone.word.label.column_name("word"),
            c.phone.cog.column_name("cog"),
            c.phone.peak.column_name("peak"),
            c.phone.slope.column_name("slope"),
            c.phone.spread.column_name("spread"),
        )
        q.to_csv(output_path)
        print("Results for sibilants written to " + output_path)

import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from polyglotdb import CorpusContext
from polyglotdb.corpus import AudioContext
from polyglotdb.config import CorpusConfig
from polyglotdb.query.annotations.func import Count

from polyglotdb.io import inspect_textgrid
import polyglotdb.io as aio


# exports all sibilants

graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

praat_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\praatcon.exe'
script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\COG.praat'
#script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\COG_middle50percent.praat'
output_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\cog_data.csv'


config = CorpusConfig('librispeech', **graph_db)

# config = CorpusConfig('acoustic utt', **graph_db)

config.praat_path = praat_path

if __name__ == '__main__':
    with CorpusContext(config) as g:

        g.encode_class(['S', 'Z', 'SH', 'ZH'], 'sibilant')  # encode_class method is in featured.py
        # #g.encode_class(['s', 'z', 'sh', 'zh'], 'sibilant')  # encode_class method is in featured.py

        begin = time.time()
        #g.analyze_script(q, script_path, 'COG', ['1', '2'], stop_check=None, call_back=None)
        g.analyze_script('sibilant', script_path, 'COG', stop_check=None, call_back=None)
        end = time.time()
        print("Analyzing sibilants for COG took: " + str(end - begin))

        q = g.query_graph(g.phone).filter(g.phone.type_subset == 'sibilant')
        q = q.columns(g.phone.speaker.name.column_name('speaker'), g.phone.discourse.name.column_name('discourse'), g.phone.id.column_name('phone_id'), g.phone.label.column_name('phone_label'), g.phone.begin.column_name('begin'), g.phone.end.column_name('end'), g.phone.following.label.column_name('following_phone'), g.phone.word.label.column_name('word'),  g.phone.COG.column_name('COG'))
        q.to_csv(output_path)
        print("Results for word-initial sibilants written to " + output_path)
        # cog_data is data to be imported into R for sanity check
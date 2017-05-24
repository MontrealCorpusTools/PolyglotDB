import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from polyglotdb import CorpusContext
from polyglotdb.corpus import AudioContext
from polyglotdb.config import CorpusConfig
from polyglotdb.query.graph.func import Count

from polyglotdb.io import inspect_textgrid
import polyglotdb.io as aio


# exports all sibilants (word-initial part is commented out)

graph_db = {'graph_host':'localhost', 'graph_port': 7474,
            'graph_user': 'neo4j', 'graph_password': 'test'}

praat_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\praatcon.exe'
script_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\PolyglotDB\\examples\\COG.praat'
output_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\cog_data.csv'
#output_path = 'C:\\Users\\samih\\Documents\\0_SPADE_labwork\\cog_data_test.csv'


config = CorpusConfig('librispeech', **graph_db)

# config = CorpusConfig('acoustic utt', **graph_db)

config.praat_path = praat_path

if __name__ == '__main__':
    with CorpusContext(config) as g:
        # begin = time.time()
        g.encode_class(['S', 'Z', 'SH', 'ZH'], 'sibilant')  # encode_class method is in featured.py
        # #g.encode_class(['s', 'z', 'sh', 'zh'], 'sibilant')  # encode_class method is in featured.py
        # end = time.time()
        # print("Encoding sibilants took: " + str(end - begin))

        # q = g.query_graph(g.phone).filter(g.phone.label.in_(['ZH']))

        # q = g.query_graph(g.phone).filter(g.phone.label.in_(['S', 'Z', 'SH', 'ZH']))
        # q = q.filter_left_aligned(g.word)
        # q = q.filter(g.phone.following.label.in_(['AE1']))
#        q = q.filter(g.phone.speaker.name == '7558') # 7558 or 1012 for first
        # phones = q.all()
        # for i, ph in enumerate(phones):
        #     begin = time.time()
        #     print(ph.discourse.name)
        #     print(time.time() - begin)
        #     begin2 = time.time()
        #     print(g.discourse_sound_file(ph.discourse.name))
        #     print(time.time() - begin2)

#        q = g.query_graph(g.phone).filter(g.phone.label.in_(['s', 'z', 'sh', 'zh']))

        # print("Number of sibilants: " + str(q.aggregate(Count()))) # this causes an error when you try to use the query after doing this
        # number of ZH: 648
        # number of sibilants word-initial before a vowel of length 1: 22162
        # number of sibilants word-initial before a AE1 vowel: 979 -> 1.5 hours
        # number of sibilants: 121796
        # sibilants of speaker 7558: 514

        begin = time.time()
        #g.analyze_script(q, script_path, 'COG', ['1', '2'], stop_check=None, call_back=None)
        g.analyze_script('sibilant', script_path, 'COG', stop_check=None, call_back=None)
        end = time.time()
        print("Analyzing sibilants for COG took: " + str(end - begin))

#        q = g.query_graph(g.phone).filter(g.phone.label.in_(['s', 'z', 'sh', 'zh']))

        # q = g.query_graph(g.phone).filter(g.phone.label.in_(['ZH']))
        print("starting query")
        #q = g.query_graph(g.phone).filter(g.phone.label.in_(['S', 'Z', 'SH', 'ZH']))
        print("done1")
        # q = q.filter_left_aligned(g.word)
        # q = q.filter(g.phone.following.label.in_(['AE1']))
        #q = q.filter(g.phone.speaker.name == '7558')
        print("done2")
        q = g.query_graph(g.phone).filter(g.phone.type_subset == 'sibilant')
        #q = q.filter_left_aligned(g.word)
        q = q.columns(g.phone.speaker.name.column_name('speaker'), g.phone.discourse.name.column_name('discourse'), g.phone.id.column_name('phone_id'), g.phone.label.column_name('phone_label'), g.phone.begin.column_name('begin'), g.phone.end.column_name('end'), g.phone.following.label.column_name('following_phone'), g.phone.word.label.column_name('word'),  g.phone.COG.column_name('COG'))
        print("done cols")
        q.to_csv(output_path)
        # also want word, following phone
        print("Results for word-initial sibilants written to " + output_path)
        # cog_data is data to be imported into R for sanity check
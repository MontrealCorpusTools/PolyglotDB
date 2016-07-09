import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
#import polyglotdb.io as aio
import polyglotdb.io.textgrid as tio

from polyglotdb import CorpusContext

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}


def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

obstruents = ['b','bj','d','dj','f','fj','g','gj','k','kj','p','pj','s','sj','S', 't','tj','v','vj','z','zj','Z','x','dz','dZ','ts','tS']
#obstruents = ['p', 'b', 't', 'd', 'tr', 'dr', 'k', 'g', 'f', 'v', 's', 'S', 'C', 'h', 'ks']

vowels = ['a', 'y',' e','i','o','u','ja','ju']
#vowels = ['a','e', 'al', 'ael', 'alel', 'el', 'il', 'oel', 'ol', 'olel', 'uel',  'ul', 'i', 'ue', 'uxl', 'u', 'oe', 'etu', 'ox', 'o', 'ae', 'ole', 'oc', 'ale', 'abl']


first_run = True
import time
if __name__ == '__main__':
    with CorpusContext('gp_bulgarian', **graph_db) as g:
        print(g.hierarchy)
        if first_run:
            begin = time.time()
            g.encode_pauses(['sil'])
            print('Pause encoding took: {} seconds'.format(time.time() - begin))
            begin = time.time()
            g.encode_utterances(min_pause_length = 0.15)
            print('Utterance encoding took: {} seconds'.format(time.time() - begin))
        begin = time.time()
        q = g.query_graph(g.phone).filter(g.phone.label.in_(vowels))
        q = q.filter(g.phone.following.label.in_(obstruents))
        q = q.filter(g.phone.following.end == g.phone.word.end)
        q = q.filter(g.phone.word.end == g.phone.word.utterance.end)

        q = q.clear_columns().columns(g.phone.label.column_name('vowel'),
                                      g.phone.duration.column_name('vowel_duration'),
                                      g.phone.begin.column_name('vowel_begin'),
                                      g.phone.end.column_name('vowel_end'),
                                      g.phone.word.utterance.phone.rate.column_name('phone_rate'),
                                      g.phone.word.phone.count.column_name('num_segments_in_word'),
                                      g.phone.word.discourse.column_name('discourse'),
                                      g.phone.word.label.column_name('word'),
                                      g.phone.word.transcription.column_name('word_transcription'),
                                      g.phone.word.following.label.column_name('following_word'),
                                      g.phone.word.following.transcription.column_name('following_word_transcription'),
                                      g.phone.word.following.duration.column_name('following_word_duration'),
                                      g.pause.following.duration.column_name('following_pause_duration'),
                                      g.phone.following.label.column_name('following_phone'))
        print(q.cypher())
        q.to_csv('bulgarian.csv')
        print('Query took: {} seconds'.format(time.time() - begin))
        #print(q.count())

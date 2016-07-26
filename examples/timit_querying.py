import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
import polyglotdb.io as aio

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Sum

path_to_timit = r'D:\Data\TIMIT_fixed'

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

def call_back(*args):
    args = [x for x in args if isinstance(x, str)]
    if args:
        print(' '.join(args))

vowels = ['aa', 'ae', 'ah', 'ao', 'aw', 'ax', 'ax-h', 'axr', 'ay',
            'eh', 'el', 'em', 'en', 'eng', 'er', 'ey',
            'ih', 'ix', 'iy',
            'ow',' oy',
            'uh', 'uw', 'ux']

first_run = True

language = 'timit'

with CorpusContext('timit', **graph_db) as g:
    if first_run:
        g.encode_pauses(['sil']) ## used to be '','sil'
        g.encode_utterances(min_pause_length = 0.150)

    q = g.query_graph(g.phone)
    q = q.filter(g.phone.label.in_(vowels))
    q.set_type('syllabic')

    begin = time.time()
    print("Doing query 3...")

    syl = g.phone.subset_type('syllabic')
    q = g.query_graph(syl)
    q = q.filter(g.phone.word.end == g.phone.word.utterance.end)

    q = q.times().duration().columns(syl.label.column_name('vowel'),
                                     syl.duration.column_name('vowel_duration'),
                                     syl.begin.column_name('vowel_begin'),
                                     syl.end.column_name('vowel_end'),
                                     g.phone.word.label.column_name('word'),
                                     g.phone.word.duration.column_name('word_duration'),
                                     g.phone.word.begin.column_name('word_begin'),
                                     g.phone.word.end.column_name('word_end'),
                                     g.pause.following.duration.column_name('following_pause_duration'),
                                     g.pause.following.label.column_name('following_pause'),
                                     g.phone.word.utterance.phone.subset_type('syllabic').rate.column_name('utterance_syllables_per_second'),
                                     g.phone.word.utterance.begin.column_name('utterance_begin'),
                                     g.phone.word.utterance.end.column_name('utterance_end'),
                                     g.phone.word.utterance.word.position.column_name('utterance_word_position'),
                                     g.phone.word.utterance.word.count.column_name('utterance_word_count'),
                                     g.phone.word.following.label.column_name('following_word'),
                                     g.phone.word.following.duration.column_name('following_word_duration'),
                                     g.phone.word.phone.subset_type('syllabic').count.column_name('word_syllable_count'),
                                     g.phone.word.phone.subset_type('syllabic').position.column_name('word_syllable_position'))
    q = q.order_by(g.phone.word.discourse)

    q.to_csv(language+'_uttfinalwordvowels.csv')

    print('Finished query in: {} seconds'.format(time.time() - begin))

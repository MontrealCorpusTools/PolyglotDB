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

vowels = set(['aa', 'ae', 'ah', 'ao', 'aw', 'ax', 'ax-h', 'axr', 'ay',
            'eh', 'el', 'em', 'en', 'eng', 'er', 'ey',
            'ih', 'ix', 'iy',
            'ow',' oy',
            'uh', 'uw', 'ux'])

first_run = True

language = 'timit'

with CorpusContext('timit', **graph_db) as g:
    if first_run:
        g.encode_pauses(['sil']) ## used to be '','sil'
        g.encode_utterances(min_pause_length = 0.150)

        q = g.query_graph(g.surface_transcription)
        q = q.filter(g.surface_transcription.label.in_(vowels))
        q.set_type('syllabic')

    begin = time.time()
    print("Doing query 3...")

    syl = g.surface_transcription.subset_type('syllabic')
    q = g.query_graph(syl)
    q = q.filter(g.word.end==g.utterance.end)
    #q = q.filter(g.phones.end == g.word.end)

    q = q.times().duration().columns(syl.label.column_name('vowel'),
                                     syl.duration.column_name('vowel_duration'),
                                     syl.begin.column_name('vowel_begin'),
                                     syl.end.column_name('vowel_end'),
                                     g.word.label.column_name('word'),
                                     g.word.duration.column_name('word_duration'),
                                     g.word.begin.column_name('word_begin'),
                                     g.word.end.column_name('word_end'),
                                     g.word.transcription.column_name('word_transcription'),
                                     g.pause.following.duration.column_name('following_pause_duration'),
                                     g.pause.following.label.column_name('following_pause'),
                                     g.utterance.surface_transcription.subset_type('syllabic').rate.column_name('utterance_syllables_per_second'),
                                     g.utterance.begin.column_name('utterance_begin'),
                                     g.utterance.end.column_name('utterance_end'),
                                     g.utterance.word.position.column_name('utterance_word_position'),
                                     g.utterance.word.count.column_name('utterance_word_count'),
                                     g.word.following.label.column_name('following_word'),
                                     g.word.following.duration.column_name('following_word_duration'),
                                     g.word.surface_transcription.subset_type('syllabic').count.column_name('word_syllable_count'),
                                     g.word.surface_transcription.subset_type('syllabic').position.column_name('word_syllable_position'))
    # q = q.times().duration().columns(g.phones.label, g.word.discourse, g.word.label, g.word.transcription, g.word.following.label, g.phones.following.label.column_name('following_phone'))
    q = q.order_by(g.word.discourse)

    q.to_csv(language+'_uttfinalwordvowels.csv')

    print('Finished query in: {} seconds'.format(time.time() - begin))

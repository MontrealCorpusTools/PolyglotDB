import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from polyglotdb import CorpusContext
from polyglotdb.graph.func import Count, Average

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

first_run = True

syllabics = ['aa', 'aan','ae', 'aen','ah', 'ahn','ay', 'ayn','aw','awn','ao', 'aon',
            'iy','iyn','ih', 'ihn',
            'uw', 'uwn','uh', 'uhn',
            'eh', 'ehn','ey', 'eyn', 'er','el','em', 'eng',
            'ow','own', 'oy', 'oyn']

with CorpusContext('buckeye', **graph_db) as g:
    if first_run:
        begin = time.time()
        g.encode_pauses('^[<{].*')
        print('Finished encoding pauses in {} seconds'.format(time.time() - begin))

        begin = time.time()
        g.reset_utterances()
        print('Finished resetting utterances in {} seconds'.format(time.time() - begin))
        g.encode_utterances(min_pause_length = 0.15)
        print('Finished encoding utterances in {} seconds'.format(time.time() - begin))
        #g.encode_syllables(syllabics)

        begin = time.time()
        q = g.query_graph(g.phone).filter(g.phone.label.in_(syllabics))
        q.set_type('syllabic')
        print('Finished encoding syllabics in {} seconds'.format(time.time() - begin))

        begin = time.time()
        q = g.query_graph(g.utterance)

        q.cache(g.utterance.phone.subset_type('syllabic').rate.column_name('syllables_per_second'),
                g.utterance.phone.subset_type('syllabic').count.column_name('number_of_syllables'))
        print('Finished caching query in: {} seconds'.format(time.time() - begin))

    begin = time.time()
    q = g.query_graph(g.phone).filter(g.phone.label == 'l')
    print(q.count())

    q = q.times().columns(g.phone.word.label.column_name('orthography'),
                #g.phone.word.following.label.column_name('following_orthography'),
                g.phone.word.begin.column_name('word_begin'),
                g.phone.word.end.column_name('word_end'),
                g.phone.word.transcription.column_name('underlying_transcription'),
                #g.phone.word.following.transcription.column_name('following_underlying_transcription'),
                #g.phone.word.transcription.column_name('underlying'),
                #g.word.following.transcription.column_name('following_underlying'),
                #g.pause.following.duration.column_name('following_pause_duration'),
                #g.pause.following.label.column_name('following_pause'),
                #g.word.phone.count.column_name('number_of_phones'),
                #g.word.phone.label.column_name('surface_transcription'),
                #g.word.phone.penultimate.label.column_name('penult_segment'),
                #g.word.phone.penultimate.duration.column_name('penult_segment_duration'),
                #g.word.phone.final.label.column_name('final_segment'),
                #g.word.phone.final.duration.column_name('final_segment_duration'),
                #g.word.following.phone.label.column_name('following_phone'),
                #g.word.following.phone.initial.label.column_name('following_initial_segment'),
                #g.word.following.phone.initial.duration.column_name('following_initial_segment_duration'),
                #g.word.duration.column_name('word_duration'),
                #g.word.following.duration.column_name('following_word_duration'),
                g.phone.word.utterance.syllables_per_second.column_name('utterance_syllables_per_second'),
                g.phone.word.utterance.number_of_syllables.column_name('utterance_syllables_number'),
                g.phone.word.utterance.duration.column_name('utterance_duration'),
                g.phone.discourse.name.column_name('discourse'),
                g.phone.speaker.name.column_name('speaker'))
    q = q.order_by(g.phone.discourse.name)
    print(q.cypher())
    q.to_csv('test_l.csv')

    print('Finished query in: {} seconds'.format(time.time() - begin))





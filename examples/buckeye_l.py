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

syllabics = set(['aa', 'aan','ae', 'aen','ah', 'ahn','ay', 'ayn','aw','awn','ao', 'aon',
            'iy','iyn','ih', 'ihn',
            'uw', 'uwn','uh', 'uhn',
            'eh', 'ehn','ey', 'eyn', 'er','el','em', 'eng',
            'ow','own', 'oy', 'oyn'])

with CorpusContext('buckeye', **graph_db) as g:
    if first_run:
        begin = time.time()
        g.encode_pauses('^[<{].*')
        print('Finished encoding pauses in {} seconds'.format(time.time() - begin))
        #g.encode_pauses(['uh','um','okay','yes','yeah','oh','heh','yknow','um-huh',
        #        'uh-uh','uh-huh','uh-hum','mm-hmm'])
        begin = time.time()
        g.reset_utterances()
        print('Finished resetting utterances in {} seconds'.format(time.time() - begin))
        g.encode_utterances(min_pause_length = 0.15)
        print('Finished encoding utterances in {} seconds'.format(time.time() - begin))
        #g.encode_syllables(syllabics)

        begin = time.time()
        q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label.in_(syllabics))
        q.set_type('syllabic')
        print('Finished encoding syllabics in {} seconds'.format(time.time() - begin))

        begin = time.time()
        q = g.query_graph(g.utterance)

        q.cache(g.utterance.surface_transcription.subset_type('syllabic').rate.column_name('syllables_per_second'),
                g.utterance.surface_transcription.subset_type('syllabic').count.column_name('number_of_syllables'))
        print('Finished caching query in: {} seconds'.format(time.time() - begin))

    else:

        begin = time.time()
        q = g.query_graph(g.surface_transcription).filter(g.surface_transcription.label == 'l')
        print(q.count())
        #q = q.filter(g.surface_transcription.speaker.name == 's01')
        #print('words ending in t/d:',q.count())
        #q = q.filter(g.word.following.transcription.regex(r'^({})(\..*)?'.format('|'.join(syllabics))))
        #print('and with following word starting with a vowel:', q.count())

        q = q.times().columns(g.surface_transcription.word.label.column_name('orthography'),
                    #g.surface_transcription.word.following.label.column_name('following_orthography'),
                    g.surface_transcription.word.begin.column_name('word_begin'),
                    g.surface_transcription.word.end.column_name('word_end'),
                    g.surface_transcription.word.transcription.column_name('underlying_transcription'),
                    #g.surface_transcription.word.following.transcription.column_name('following_underlying_transcription'),
                    #g.surface_transcription.word.transcription.column_name('underlying'),
                    #g.word.following.transcription.column_name('following_underlying'),
                    #g.pause.following.duration.column_name('following_pause_duration'),
                    #g.pause.following.label.column_name('following_pause'),
                    #g.word.surface_transcription.count.column_name('number_of_surface_phones'),
                    #g.word.surface_transcription.label.column_name('surface_transcription'),
                    #g.word.surface_transcription.penultimate.label.column_name('penult_segment'),
                    #g.word.surface_transcription.penultimate.duration.column_name('penult_segment_duration'),
                    #g.word.surface_transcription.final.label.column_name('final_segment'),
                    #g.word.surface_transcription.final.duration.column_name('final_segment_duration'),
                    #g.word.following.surface_transcription.label.column_name('following_surface_transcription'),
                    #g.word.following.surface_transcription.initial.label.column_name('following_initial_segment'),
                    #g.word.following.surface_transcription.initial.duration.column_name('following_initial_segment_duration'),
                    #g.word.duration.column_name('word_duration'),
                    #g.word.following.duration.column_name('following_word_duration'),
                    g.surface_transcription.word.utterance.syllables_per_second.column_name('utterance_syllables_per_second'),
                    g.surface_transcription.word.utterance.number_of_syllables.column_name('utterance_syllables_number'),
                    g.surface_transcription.word.utterance.duration.column_name('utterance_duration'),
                    g.surface_transcription.discourse.name.column_name('discourse'),
                    g.surface_transcription.speaker.name.column_name('speaker'))
        q = q.order_by(g.surface_transcription.discourse.name)
        print(q.cypher())
        q.to_csv('test_l.csv')

        print('Finished query in: {} seconds'.format(time.time() - begin))





import sys
import os
import time
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)

from polyglotdb.corpus import CorpusContext
from polyglotdb.graph.func import Count, Average

from polyglotdb.io.csv import save_results

graph_db = {'host':'localhost', 'port': 7474,
            'user': 'neo4j', 'password': 'test'}

first_run = False

syllabics = set(['aa', 'aan','ae', 'aen','ah', 'ahn','ay', 'ayn','aw','awn','ao', 'aon',
            'iy','iyn','ih', 'ihn',
            'uw', 'uwn','uh', 'uhn',
            'eh', 'ehn','ey', 'eyn', 'er','el','em', 'eng',
            'ow','own', 'oy', 'oyn'])
import time
print(r'^({})\..*'.format('|'.join(syllabics)))
with CorpusContext('buckeye', **graph_db) as g:
    if first_run:
        begin = time.time()
        g.encode_pauses('^[<{].*')
        print('Finished encoding pauses in {} seconds'.format(time.time() - begin))
        #g.encode_pauses(['uh','um','okay','yes','yeah','oh','heh','yknow','um-huh',
        #        'uh-uh','uh-huh','uh-hum','mm-hmm'])
        begin = time.time()
        g.encode_utterances(min_pause_length = 0.15)
        print('Finished encoding utterances in {} seconds'.format(time.time() - begin))
        #g.encode_syllables(syllabics)

    q = g.query_graph(g.surface_transcription).group_by(g.surface_transcription.label, g.surface_transcription.discourse).aggregate(Average(g.surface_transcription.duration))
    save_results(q, 't.csv')
    begin = time.time()
    q = g.query_graph(g.word).filter(g.word.transcription.regex(r'.*\.[td]$'))
    #print('words ending in t/d:',q.count())
    q = q.filter(g.word.following.transcription.regex(r'^({})(\..*)?'.format('|'.join(syllabics))))
    #print('and with following word starting with a vowel:', q.count())


    q = q.clear_columns().times().columns(g.word.label.column_name('orthography'),
                #g.word.following.label.column_name('following_orthography'),
                #g.word.transcription.column_name('underlying_transcription'),
                #g.word.following.transcription.column_name('following_underlying_transcription'),
                #g.word.transcription.column_name('underlying'),
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
                g.utterance.surface_transcription.rate.column_name('utterance_surface_phones_per_second'),
                g.utterance.surface_transcription.count.column_name('utterance_surface_phones_number'),
                g.utterance.duration.column_name('utterance_duration'),
                g.word.discourse.column_name('discourse'))
    q = q.order_by(g.word.discourse)
    print(q.cypher())
    q.to_csv('test_nofilled.csv')

    print('Finished query in: {} seconds'.format(time.time() - begin))





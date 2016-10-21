import os
import pytest

from polyglotdb import CorpusContext

from polyglotdb.io import inspect_textgrid
from polyglotdb.graph.func import Count

def test_get_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.reset_utterances()
        g.encode_pauses(['sil'])
        utterances = g.get_utterances('acoustic_corpus', min_pause_length = 0, min_utterance_length = 0)

        expected_utterances = [(1.059223, 7.541484), (8.016164, 11.807666),
                                (12.167356, 13.898228), (14.509726, 17.207370),
                                (18.359807, 19.434003), (19.599747, 21.017242),
                                (21.208318, 22.331874), (22.865036, 23.554014),
                                (24.174348, 24.706663), (24.980290, 25.251656)]
        print(utterances)
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))
        utterances = g.get_utterances('acoustic_corpus', min_pause_length = 0.5)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 22.331874), (22.865036, 23.554014),
                                (24.174348, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

        utterances = g.get_utterances('acoustic_corpus', min_pause_length = 0.5, min_utterance_length = 1.0)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 23.554014),
                                (24.174348, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

        utterances = g.get_utterances('acoustic_corpus', min_pause_length = 0.5, min_utterance_length = 1.1)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

        g.encode_pauses(['sil','um'])
        utterances = g.get_utterances('acoustic_corpus', min_pause_length = 0, min_utterance_length = 0)

        expected_utterances = [(1.059223, 7.541484), (8.576511, 11.807666),
                                (12.167356, 13.898228), (14.509726, 17.207370),
                                (18.359807, 19.434003), (19.599747, 21.017242),
                                (21.208318, 22.331874),
                                (24.174348, 24.706663), (24.980290, 25.251656)]
        print(utterances)
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

def test_utterance_nosilence(graph_db, textgrid_test_dir):
    tg_path = os.path.join(textgrid_test_dir, 'phone_word_no_silence.TextGrid')
    with CorpusContext('word_phone_nosilence', **graph_db) as g:
        g.reset()
        parser = inspect_textgrid(tg_path)
        parser.annotation_types[0].linguistic_type = 'phone'
        parser.annotation_types[1].linguistic_type = 'word'
        parser.hierarchy['word'] = None
        parser.hierarchy['phone'] = 'word'
        g.load(parser, tg_path)

        g.encode_utterances()

        q = g.query_graph(g.word).filter(g.word.label == 'b')

        q = q.columns(g.word.following.label.column_name('following_word'))
        print(q.cypher())
        results = q.all()
        assert(len(results) == 1)
        assert(results[0]['following_word'] is None)

        q = g.query_graph(g.word).filter(g.word.begin == g.word.utterance.begin)

        results = q.all()

        assert(len(results) == 1)
        assert(results[0]['label'] == 'a')

        q = g.query_graph(g.phone).filter(g.phone.begin == g.phone.utterance.begin)

        results = q.all()

        assert(len(results) == 1)
        assert(results[0]['label'] == 'a')

        #Things like g.phone.word.following are currently broken in PolyglotDB
        return

        q = g.query_graph(g.phone).filter(g.phone.label == 'b')

        q = q.filter(g.phone.following.label == 'b')

        q = q.columns(g.phone.label,g.phone.id,g.phone.word.following.label.column_name('following_word'))
        print(q.cypher())
        results = q.all()
        assert(len(results) == 1)
        assert(results[0]['following_word'] is None)

def test_utterance_oneword(graph_db, textgrid_test_dir):
    tg_path = os.path.join(textgrid_test_dir, 'one_word_no_silence.TextGrid')
    with CorpusContext('one_word_no_silence', **graph_db) as g:
        g.reset()
        parser = inspect_textgrid(tg_path)
        parser.annotation_types[0].linguistic_type = 'phone'
        parser.annotation_types[1].linguistic_type = 'word'
        parser.hierarchy['word'] = None
        parser.hierarchy['phone'] = 'word'
        g.load(parser, tg_path)

        g.encode_utterances()

        q = g.query_graph(g.utterance)

        res = q.all()

        assert(res[0].begin == 0)

def test_no_speech_utterance(graph_db, textgrid_test_dir):
    tg_path = os.path.join(textgrid_test_dir, 'one_word_no_silence.TextGrid')
    with CorpusContext('one_word_no_silence', **graph_db) as g:
        g.reset()
        parser = inspect_textgrid(tg_path)
        parser.annotation_types[0].linguistic_type = 'phone'
        parser.annotation_types[1].linguistic_type = 'word'
        parser.hierarchy['word'] = None
        parser.hierarchy['phone'] = 'word'
        g.load(parser, tg_path)

        g.encode_pauses(['ab'])

        g.encode_utterances()

        q = g.query_graph(g.utterance)

        res = q.all()

        assert(len(res) == 0)

def test_encode_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil', 'um'])
        g.encode_utterances(min_pause_length = 0)
        q = g.query_graph(g.utterance).times().duration().order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        print(results)
        expected_utterances = [(1.059223, 7.541484), (8.576511, 11.807666),
                                (12.167356, 13.898228), (14.509726, 17.207370),
                                (18.359807, 19.434003), (19.599747, 21.017242),
                                (21.208318, 22.331874),
                                (24.174348, 24.706663), (24.980290, 25.251656)]
        assert(len(results) == len(expected_utterances))
        for i, r in enumerate(results):
            assert(round(r['begin'],3) == round(expected_utterances[i][0], 3))
            assert(round(r['end'],3) == round(expected_utterances[i][1],3))
        assert(abs(results[0]['duration'] - 6.482261) < 0.001)

        g.encode_pauses(['sil'])
        g.encode_utterances(min_pause_length = 0)

        expected_utterances = [(1.059223, 7.541484), (8.016164, 11.807666),
                                (12.167356, 13.898228), (14.509726, 17.207370),
                                (18.359807, 19.434003), (19.599747, 21.017242),
                                (21.208318, 22.331874), (22.865036, 23.554014),
                                (24.174348, 24.706663), (24.980290, 25.251656)]
        q = g.query_graph(g.utterance).times().duration().order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        assert(len(g.query_graph(g.pause).all()) == 11)
        assert(len(results) == len(expected_utterances))
        for i, r in enumerate(results):
            assert(round(r['begin'],3) == round(expected_utterances[i][0], 3))
            assert(round(r['end'],3) == round(expected_utterances[i][1],3))

        q = g.query_graph(g.utterance).order_by(g.utterance.begin)
        results = q.all()
        for i, r in enumerate(results):
            assert(round(r['begin'],3) == round(expected_utterances[i][0], 3))
            assert(round(r['end'],3) == round(expected_utterances[i][1],3))
            assert(r['label'] is None)

        q = g.query_graph(g.phone).filter(g.phone.begin == g.phone.utterance.begin)
        q = q.order_by(g.phone.begin)
        results = q.all()

        assert(len(results) == len(expected_utterances))

        expected = ['dh', 'ah', 'l', 'ah', 'ae', 'hh', 'w', 'ah', 'ae', 'th']

        for i, r in enumerate(results):
            assert(r['label'] == expected[i])

def test_speech_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.utterance)
        q = q.columns(g.utterance.word.rate.column_name('words_per_second'), g.utterance.word.label)
        q = q.order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0]['words_per_second'] - (26 / 6.482261)) < 0.001)

def test_query_speaking_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'talking')
        q = q.columns(g.word.utterance.word.rate.column_name('words_per_second'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0]['words_per_second'] - (26 / 6.482261)) < 0.001)

def test_utterance_position(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil','um'])
        q = g.query_graph(g.pause)
        print(q.all())
        g.encode_utterances(min_pause_length = 0)
        q = g.query_graph(g.word)
        q = q.filter(g.word.label == 'this')
        q = q.order_by(g.word.begin)
        q = q.columns(g.word.utterance.word.position.column_name('position'))
        print(q.cypher())
        results = q.all()
        assert(results[0]['position'] == 1)

        q = g.query_graph(g.word)
        q = q.filter(g.word.label == 'talking')
        q = q.order_by(g.word.begin)
        q = q.columns(g.word.utterance.word.position.column_name('position'))
        print(q.cypher())
        results = q.all()
        assert(results[0]['position'] == 7)
        assert(results[1]['position'] == 4)


@pytest.mark.xfail
def test_complex_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        vowels = ['aa']
        obstruents = ['k']
        syllabics = ['aa','ih']
        q = g.query_graph(g.phone).filter(g.phone.label.in_(syllabics))
        q.set_type('syllabic')

        q = g.query_graph(g.phone).filter(g.phone.label.in_(vowels))
        q = q.filter(g.phone.following.label.in_(obstruents))
        #q = q.filter(g.phone.following.end == g.word.end)
        #q = q.filter(g.word.end == g.utterance.end)

        q = q.clear_columns().columns(g.phone.label.column_name('vowel'),
                                      g.phone.duration.column_name('vowel_duration'),
                                      g.phone.begin.column_name('vowel_begin'),
                                      g.phone.end.column_name('vowel_end'),
                                      g.utterance.phone.rate.column_name('phone_rate'),
                                      g.word.phone.count.column_name('num_segments_in_word'),
                                      g.word.phone.subset_type('syllabic').count.column_name('num_syllables_in_word'),
                                      g.word.discourse.column_name('discourse'),
                                      g.word.label.column_name('word'),
                                      g.word.transcription.column_name('word_transcription'),
                                      g.word.following.label.column_name('following_word'),
                                      g.word.following.duration.column_name('following_word_duration'),
                                      g.pause.following.duration.column_name('following_pause_duration'),
                                      g.phone.following.label.column_name('following_phone'))
        q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(len(results) == 2)
        assert(results[0]['num_segments_in_word'] == 5)
        assert(results[0]['num_syllables_in_word'] == 2)

@pytest.mark.xfail
def test_utterance_minimum_pause(french_config):
    with CorpusContext(french_config) as g:
        g.encode_utterances(min_pause_length=0.15)

        q = g.query_graph(g.utterance)
        res = q.all()
        assert(len(res) == 2)


        q1= g.query_graph(g.phone)
        q1 = q1.filter(g.phone.begin == g.phone.utterance.begin)
        q1 = q1.filter(g.phone.label.in_(['T','t']))
        secondres = q1.aggregate(Count())

        assert(secondres == 0)

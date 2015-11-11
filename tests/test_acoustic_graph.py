
import os
import pytest

from polyglotdb.corpus import CorpusContext

def test_encode_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil'])
        q = g.query_graph(g.pause)
        assert(len(q.all()) > 0)

def test_get_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        utterances = g.get_utterances('acoustic_corpus', ['sil'], min_pause_length = 0, min_utterance_length = 0)

        expected_utterances = [(1.059223, 7.541484), (8.016164, 11.807666),
                                (12.167356, 13.898228), (14.509726, 17.207370),
                                (18.359807, 19.434003), (19.599747, 21.017242),
                                (21.208318, 22.331874), (22.865036, 23.554014),
                                (24.174348, 24.706663), (24.980290, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))
        utterances = g.get_utterances('acoustic_corpus', ['sil'], min_pause_length = 0.5)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 22.331874), (22.865036, 23.554014),
                                (24.174348, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

        utterances = g.get_utterances('acoustic_corpus', ['sil'], min_pause_length = 0.5, min_utterance_length = 1.0)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 23.554014),
                                (24.174348, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

        utterances = g.get_utterances('acoustic_corpus', ['sil'], min_pause_length = 0.5, min_utterance_length = 1.1)

        expected_utterances = [(1.059223, 13.898228), (14.509726, 17.207370),
                                (18.359807, 25.251656)]
        assert(len(utterances) == len(expected_utterances))
        for i, u in enumerate(utterances):
            assert(round(u[0],5) == round(expected_utterances[i][0],5))
            assert(round(u[1],5) == round(expected_utterances[i][1],5))

def test_query_with_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['uh','um'])
        q = g.query_graph(g.word).filter(g.word.label == 'cares')
        q = q.columns(g.word.following.label.column_name('following'),
                    g.pause.following.label.column_name('following_pause'),
                    g.pause.following.duration.column_name('following_pause_duration')).order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].following == 'this')
        assert(results[0].following_pause == ['sil', 'um'])
        assert(abs(results[0].following_pause_duration - 1.035027) < 0.001)

        q = g.query_graph(g.word).filter(g.word.label == 'this')
        q = q.columns(g.word.previous.label.column_name('previous'),
                    g.pause.previous.label.column_name('previous_pause'),
                    g.pause.previous.duration.column_name('previous_pause_duration'),
                    g.pause.previous.begin,
                    g.pause.previous.end).order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].previous == 'cares')
        assert(results[0].previous_pause == ['sil', 'um'])
        assert(abs(results[0].previous_pause_duration - 1.035027) < 0.001)

def test_encode_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_utterances()
        q = g.query_graph(g.utterance).duration().order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0].duration - 6.482261) < 0.001)

def test_speech_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.utterance)
        q = q.columns(g.utterance.word.rate.column_name('words_per_second'), g.utterance.word.label)
        q = q.order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0].words_per_second - (26 / 6.482261)) < 0.001)

def test_query_duration(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa').order_by(g.phone.begin.column_name('begin')).duration()
        print(q.cypher())
        results = q.all()
        assert(len(results) == 3)
        assert(abs(results[0].begin - 2.704) < 0.001)
        assert(abs(results[0].duration - 0.078) < 0.001)

        assert(abs(results[1].begin - 9.320) < 0.001)
        assert(abs(results[1].duration - 0.122) < 0.001)

        assert(abs(results[2].begin - 24.560) < 0.001)
        assert(abs(results[2].duration - 0.039) < 0.001)


def test_discourses_prop(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        assert(g.discourses == ['acoustic_corpus'])

def test_wav_info(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        sf = g.discourse_sound_file('acoustic_corpus')
        assert(sf.sampling_rate == 16000)
        assert(sf.n_channels == 1)


def test_query_pitch(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow').order_by(g.phone.begin.column_name('begin'))
        aq = g.query_acoustics(q).pitch('acousticsim')
        results = aq.all()
        expected_pitch = {4.23: 98.2,
                            4.24:390.2,
                            4.25:0.0,
                            4.26:95.8,
                            4.27:95.8}
        assert(set(results[0].pitch.keys()) == set(expected_pitch.keys()))
        for k, v in results[0].pitch.items():
            assert(round(v,1) == expected_pitch[k])

        assert(round(aq.max()[0].max_pitch, 1) == round(max(expected_pitch.values()), 1))

def test_query_formants(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        aq = g.query_acoustics(q).formants('acousticsim')


def test_query_formants_aggregate_group_by(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        aq = g.query_acoustics(q).group_by(g.phone.label).formants('acousticsim')
        #results = aq.aggregate(Average())


def test_analyze_utterances(graph_db):
    with CorpusContext('acoustic', pause_words = ['sil'], **graph_db) as g:
        g.analyze_acoustics()

def test_query_speaking_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'talking')
        q = q.columns(g.utterance.word.rate.column_name('words_per_second'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0].words_per_second - (26 / 6.482261)) < 0.001)

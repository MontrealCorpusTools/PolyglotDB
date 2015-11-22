
import os
import pytest

from polyglotdb.corpus import CorpusContext

def test_encode_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        discourse = g.discourse('acoustic_corpus')
        g.encode_pauses(['sil'])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert(len(q.all()) == 11)

        paused = g.discourse('acoustic_corpus')
        expected = [x for x in discourse if x.label != 'sil']
        for i,d in enumerate(expected):
            print(d.label, paused[i].label)
            assert(d.label == paused[i].label)

        g.reset_pauses()
        new_discourse = g.discourse('acoustic_corpus')
        for i,d in enumerate(discourse):
            assert(d.label == new_discourse[i].label)

        g.encode_pauses(['sil','um','uh'])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert(len(q.all()) == 14)

        paused = g.discourse('acoustic_corpus')
        expected = [x for x in discourse if x.label not in ['sil','um','uh']]
        for i,d in enumerate(expected):
            print(d.label, paused[i].label)
            assert(d.label == paused[i].label)

        g.reset_pauses()
        new_discourse = g.discourse('acoustic_corpus')
        print(discourse)
        print(new_discourse)
        for i,d in enumerate(discourse):
            assert(d.label == new_discourse[i].label)

def test_get_utterances(acoustic_config):
    with CorpusContext(acoustic_config) as g:
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
            assert(round(r.begin,3) == round(expected_utterances[i][0], 3))
            assert(round(r.end,3) == round(expected_utterances[i][1],3))
        assert(abs(results[0].duration - 6.482261) < 0.001)

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
            assert(round(r.begin,3) == round(expected_utterances[i][0], 3))
            assert(round(r.end,3) == round(expected_utterances[i][1],3))

def test_query_with_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil', 'uh','um'])
        q = g.query_graph(g.word).filter(g.word.label == 'cares')
        q = q.columns(g.word.following.label.column_name('following'),
                    g.pause.following.label.column_name('following_pause'),
                    g.pause.following.duration.column_name('following_pause_duration')).order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(len(results) == 1)
        assert(results[0].following == 'this')
        assert(results[0].following_pause == ['sil','um'])
        assert(abs(results[0].following_pause_duration - 1.035027) < 0.001)

        q = g.query_graph(g.word).filter(g.word.label == 'this')
        q = q.columns(g.word.previous.label.column_name('previous'),
                    g.pause.previous.label.column_name('previous_pause'),
                    g.pause.previous.duration.column_name('previous_pause_duration'),
                    g.pause.previous.begin,
                    g.pause.previous.end).order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(len(results) == 2)
        assert(results[1].previous == 'cares')
        assert(results[1].previous_pause == ['sil','um'])
        assert(abs(results[1].previous_pause_duration - 1.035027) < 0.001)

@pytest.mark.xfail
def test_encode_syllables(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_syllables(set(['ih','iy','ah','uw','er','ay','aa','ae','eh','ow']))

        q = g.query_graph(g.word)
        q = q.columns(g.word.syllable.rate.column_name('syllables_per_second'))
        #print(q.cypher())
        #print(q.all())
        q = g.query_graph(g.utterance)
        q = q.columns(g.utterance.syllable.rate.column_name('syllables_per_second'),g.utterance.syllable.count.column_name('num_syllables'))
        q = q.order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        print(results)
        assert(abs(results[0].syllables_per_second - (35 / 6.482261)) < 0.001) # 34 syllabic segments plus one word that doesn't have syllabic segments

def test_position_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil'])
        q = g.query_graph(g.pause)
        print(q.all())
        g.encode_utterances(min_pause_length = 0)
        q = g.query_graph(g.utterance).times()
        print(q.all())
        q = g.query_graph(g.word).filter(g.word.label == 'words')
        q = q.columns(g.utterance.word.position.column_name('word_position'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        expected = [6, 4, 1, 2, 3]
        assert(len(results) == len(expected))
        for i in range(len(expected)):
            assert(results[i].word_position == expected[i])

        q = g.query_graph(g.phone).filter(g.word.label == 'words').filter(g.phone.label == 'er')
        q = q.columns(g.utterance.word.position.column_name('word_position'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(len(results) == len(expected))
        for i in range(len(expected)):
            assert(results[i].word_position == expected[i])

def test_initial_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.word).filter(g.word.label == 'this')
        g.encode_pauses(['sil'])
        q = q.columns(g.word.following.phone.initial.label.column_name('initial_following_phone'),
                    g.word.following.phone.initial.duration.column_name('initial_following_phone_duration'),
                    g.word.following.phone.initial.begin.column_name('begin'),
                    g.word.following.phone.initial.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].initial_following_phone == 'ih')
        assert(abs(results[0].initial_following_phone_duration - 0.062353) < 0.001)
        assert(abs(results[0].begin - 1.203942) < 0.001)
        assert(abs(results[0].end - 1.266295) < 0.001)

def test_final_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil'])
        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.final.label.column_name('final_previous_phone'),
                    g.word.previous.phone.final.duration.column_name('final_previous_phone_duration'),
                    g.word.previous.phone.final.begin.column_name('begin'),
                    g.word.previous.phone.final.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].final_previous_phone == 's')
        assert(abs(results[0].final_previous_phone_duration - 0.079107) < 0.001)
        assert(abs(results[0].begin - 1.124835) < 0.001)
        assert(abs(results[0].end - 1.203942) < 0.001)

def test_penult_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil'])
        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.penultimate.label.column_name('phone'),
                    g.word.previous.phone.penultimate.duration.column_name('duration'),
                    g.word.previous.phone.penultimate.begin.column_name('begin'),
                    g.word.previous.phone.penultimate.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].phone == 'ih')
        assert(abs(results[0].duration - 0.042712) < 0.001)
        assert(abs(results[0].begin - 1.082123) < 0.001)
        assert(abs(results[0].end - 1.124835) < 0.001)

        q = g.query_graph(g.word).filter(g.word.label == 'is')
        q = q.columns(g.word.previous.phone.antepenultimate.label.column_name('phone'),
                    g.word.previous.phone.antepenultimate.duration.column_name('duration'),
                    g.word.previous.phone.antepenultimate.begin.column_name('begin'),
                    g.word.previous.phone.antepenultimate.end.column_name('end'))
        q = q.order_by(g.word.begin)
        print(q.cypher())
        results = q.all()
        assert(results[0].phone == 'dh')
        assert(abs(results[0].duration - 0.022900) < 0.001)
        assert(abs(results[0].begin - 1.059223) < 0.001)
        assert(abs(results[0].end - 1.082123) < 0.001)

def test_speech_rate(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.utterance)
        q = q.columns(g.utterance.word.rate.column_name('words_per_second'), g.utterance.word.label)
        q = q.order_by(g.utterance.begin)
        print(q.cypher())
        results = q.all()
        assert(abs(results[0].words_per_second - (26 / 6.482261)) < 0.001)

def test_utterance_position(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil','um'])
        q = g.query_graph(g.pause)
        print(q.all())
        g.encode_utterances(min_pause_length = 0)
        q = g.query_graph(g.word)
        q = q.filter(g.word.label == 'this')
        q = q.order_by(g.word.begin)
        q = q.columns(g.utterance.word.position.column_name('position'))
        print(q.cypher())
        results = q.all()
        assert(results[0].position == 1)

        q = g.query_graph(g.word)
        q = q.filter(g.word.label == 'talking')
        q = q.order_by(g.word.begin)
        q = q.columns(g.utterance.word.position.column_name('position'))
        print(q.cypher())
        results = q.all()
        assert(results[0].position == 7)
        assert(results[1].position == 4)


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

def test_complex_query(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        vowels = ['aa']
        obstruents = ['k']
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
        assert(results[0].num_segments_in_word == 5)

def test_mirrored(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        vowels = ['ih']
        obstruents = ['s']
        q = g.query_graph(g.phone).filter(g.phone.label.in_(obstruents))
        q = q.filter(g.phone.previous.label.in_(vowels))
        q = q.filter(g.phone.following.label == g.phone.previous.label)

        print(q.cypher())

        results = q.all()
        print(results)
        assert(len(results) == 2)
        q = g.query_graph(g.phone).filter(g.phone.label.in_(obstruents))
        q = q.filter(g.phone.previous.label.in_(vowels))
        q = q.filter(g.phone.following.label == g.phone.previous.label)
        q = q.filter(g.phone.end == g.word.end)
        q = q.filter(g.phone.following.begin == g.word.following.begin)

        print(q.cypher())

        results = q.all()
        print(results)
        assert(len(results) == 2)


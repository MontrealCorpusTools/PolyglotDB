import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


def test_wav_info(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        sf = g.discourse_sound_file('acoustic_corpus')
        assert (sf.sampling_rate == 16000)
        assert (sf.n_channels == 1)


@acoustic
def test_analyze_pitch_basic_praat(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'basic'
        g.analyze_pitch()
        assert(g.has_pitch(g.discourses[0], 'praat'))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.pitch.track)
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            assert(r.track)

@acoustic
def test_track_mean_query(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin.column_name('begin'), g.phone.end, g.phone.pitch.track, g.phone.pitch.mean)
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            assert(r.track)
            assert(r['Mean_F0'])
            print(r.track, r['Mean_F0'])
            calc_mean =  sum(x['F0'] for x in r.track.values())/len(r.track)
            assert(abs(r['Mean_F0'] - calc_mean) < 0.001)

@acoustic
def test_track_following_mean_query(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin.column_name('begin'), g.phone.end, g.phone.pitch.track, g.phone.following.pitch.mean.column_name('following_phone_pitch_mean'))
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            assert(r.track)
            assert(r['following_phone_pitch_mean'])
            print(r.track, r['following_phone_pitch_mean'])
            calc_mean =  sum(x['F0'] for x in r.track.values())/len(r.track)
            assert(abs(r['following_phone_pitch_mean'] - calc_mean) > 0.001)

@acoustic
def test_track_hierarchical_mean_query(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin.column_name('begin'), g.phone.end, g.phone.pitch.track, g.phone.word.pitch.mean.column_name('word_pitch_mean'))
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            assert(r.track)
            assert(r['word_pitch_mean'])
            print(r.track, r['word_pitch_mean'])
            calc_mean =  sum(x['F0'] for x in r.track.values())/len(r.track)
            assert(abs(r['word_pitch_mean'] - calc_mean) > 0.001)

@acoustic
def test_track_hierarchical_following_mean_query(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin.column_name('begin'), g.phone.end, g.phone.pitch.track,
                      g.phone.word.pitch.mean.column_name('word_pitch_mean'),
                      g.phone.word.following.pitch.mean.column_name('following_word_pitch_mean')
                      )
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            print(r['begin'])
            assert(r.track)
            assert(r['word_pitch_mean'])
            print(r['word_pitch_mean'],r['following_word_pitch_mean'])
            assert(r['word_pitch_mean'] != r['following_word_pitch_mean'])

@acoustic
def test_track_hierarchical_utterance_mean_query(acoustic_utt_config, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.label, g.phone.pitch.track,
                      g.phone.syllable.following.pitch.mean.column_name('following_syllable_pitch_mean'),
                      g.phone.syllable.following.following.pitch.mean.column_name('following_following_syllable_pitch_mean'),
                      g.phone.syllable.word.utterance.pitch.mean.column_name('utterance_pitch_mean'),
                      g.phone.syllable.word.utterance.pitch.min.column_name('utterance_pitch_min'),
                      g.phone.syllable.word.utterance.pitch.max.column_name('utterance_pitch_max'),
                      )
        results = q.all()
        assert(len(results) > 0)
        for r in results:
            assert(r.track)
            assert(r['utterance_pitch_mean'])
            assert(r['utterance_pitch_min'])
            assert(r['utterance_pitch_max'])
            print(r['utterance_pitch_mean'],r['following_syllable_pitch_mean'])
            with pytest.raises(KeyError):
                assert(r['utterance_pitch_mean'] != r['following_word_pitch_mean'])
            assert(r['utterance_pitch_mean'] != r['following_syllable_pitch_mean'])
            assert(r['following_following_syllable_pitch_mean'] != r['following_syllable_pitch_mean'])
        q.to_csv(os.path.join(results_test_dir, 'test_track_hierarchical_utterance_mean_query.txt'))

@acoustic
def test_analyze_pitch_basic_reaper(acoustic_utt_config, reaper_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'reaper'
        g.config.reaper_path = reaper_path
        g.config.pitch_algorithm = 'basic'
        g.analyze_pitch()


@acoustic
def test_analyze_pitch_gendered_praat(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'gendered'
        g.analyze_pitch()

@acoustic
def test_analyze_pitch_gendered_praat(acoustic_utt_config, praat_path):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.pitch_source = 'praat'
        g.config.praat_path = praat_path
        g.config.pitch_algorithm = 'speaker_adjusted'
        g.analyze_pitch()
        assert (g.has_pitch('acoustic_corpus'))




def test_query_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'dummy'
        expected_pitch = {Decimal('4.23'): {'F0': 98},
                          Decimal('4.24'): {'F0': 100},
                          Decimal('4.25'): {'F0': 99},
                          Decimal('4.26'): {'F0': 95.8},
                          Decimal('4.27'): {'F0': 95.8}}
        g.save_pitch('acoustic_corpus', expected_pitch)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.pitch.track)
        print(q.cypher())
        results = q.all()
        assert (len(results[0].track.items()) == len(expected_pitch.items()))
        print(sorted(expected_pitch.items()))
        print(sorted(results[0].track.items()))
        for k, v in results[0].track.items():
            assert (round(v['F0'], 1) == expected_pitch[k]['F0'])


def test_query_intensity(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.intensity_source = 'dummy'
        expected_intensity = {Decimal('4.23'): {'Intensity': 98},
                              Decimal('4.24'): {'Intensity': 100},
                              Decimal('4.25'): {'Intensity': 99},
                              Decimal('4.26'): {'Intensity': 95.8},
                              Decimal('4.27'): {'Intensity': 95.8}}
        g.save_intensity('acoustic_corpus', expected_intensity)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.intensity.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_intensity.items()))
        print(sorted(results[0].track.items()))
        for k, v in results[0].track.items():
            assert (round(v['Intensity'], 1) == expected_intensity[k]['Intensity'])


def test_query_aggregate_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'dummy'
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.pitch.min,
                      g.phone.pitch.max, g.phone.pitch.mean)
        print(q.cypher())
        results = q.all()

        assert (results[0]['Min_F0'] == 95.8)
        assert (results[0]['Max_F0'] == 100)
        assert (round(results[0]['Mean_F0'], 2) == 97.72)


def test_query_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_source = 'dummy'
        expected_formants = {Decimal('4.23'): {'F1': 501, 'F2': 1500, 'F3': 2500},
                             Decimal('4.24'): {'F1': 502, 'F2': 1499, 'F3': 2500},
                             Decimal('4.25'): {'F1': 503, 'F2': 1498, 'F3': 2500},
                             Decimal('4.26'): {'F1': 504, 'F2': 1497, 'F3': 2500},
                             Decimal('4.27'): {'F1': 505, 'F2': 1496, 'F3': 2500}}
        g.save_formants('acoustic_corpus', expected_formants)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.formants.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_formants.items()))
        print(sorted(results[0].track.items()))
        for k, v in results[0].track.items():
            assert (round(v['F1'], 1) == expected_formants[k]['F1'])
            assert (round(v['F2'], 1) == expected_formants[k]['F2'])
            assert (round(v['F3'], 1) == expected_formants[k]['F3'])


def test_query_aggregate_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_source = 'dummy'

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.formants.min,
                      g.phone.formants.max, g.phone.formants.mean)
        print(q.cypher())
        results = q.all()

        assert (results[0]['Min_F1'] == 501)
        assert (results[0]['Max_F1'] == 505)
        assert (round(results[0]['Mean_F1'], 2) == 503)

        assert (results[0]['Min_F2'] == 1496)
        assert (results[0]['Max_F2'] == 1500)
        assert (round(results[0]['Mean_F2'], 2) == 1498)

        assert (results[0]['Min_F3'] == 2500)
        assert (results[0]['Max_F3'] == 2500)
        assert (round(results[0]['Mean_F3'], 2) == 2500)


def test_export_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_source = 'dummy'

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label.column_name('label'), g.phone.pitch.track)
        print(q.cypher())
        results = q.all()

        t = results.rows_for_csv()
        assert (next(t) == {'label': 'ow', 'time': Decimal('4.23'), 'F0': 98})
        assert (next(t) == {'label': 'ow', 'time': Decimal('4.24'), 'F0': 100})
        assert (next(t) == {'label': 'ow', 'time': Decimal('4.25'), 'F0': 99})
        assert (next(t) == {'label': 'ow', 'time': Decimal('4.26'), 'F0': 95.8})
        assert (next(t) == {'label': 'ow', 'time': Decimal('4.27'), 'F0': 95.8})

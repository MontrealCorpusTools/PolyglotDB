import os
from decimal import Decimal
import pytest

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Average

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)

def test_wav_info(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        sf = g.discourse_sound_file('acoustic_corpus')
        assert(sf.sampling_rate == 16000)
        assert(sf.n_channels == 1)

@acoustic
def test_analyze_acoustics(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.analyze_acoustics()

@acoustic
def test_analyze_acoustics_praat(acoustic_utt_config, praat_path):
    acoustic_utt_config.pitch_algorithm = 'praat'
    acoustic_utt_config.praat_path = praat_path
    with CorpusContext(acoustic_utt_config) as g:
        g.analyze_acoustics()

        assert(g.has_pitch('acoustic_corpus'))

def test_query_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_algorithm = 'dummy'
        expected_pitch = {Decimal('4.23'): {'F0':98},
                            Decimal('4.24'):{'F0':100},
                            Decimal('4.25'):{'F0':99},
                            Decimal('4.26'):{'F0':95.8},
                            Decimal('4.27'):{'F0':95.8}}
        g.save_pitch('acoustic_corpus', expected_pitch)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.pitch.track)
        print(q.cypher())
        results = q.all()

        times = list(expected_pitch.keys())

        print(sorted(expected_pitch.items()))
        print(sorted(results[0].track.items()))
        for k, v in results[0].track.items():
            assert(round(v['F0'],1) == expected_pitch[k]['F0'])

def test_query_aggregate_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_algorithm = 'dummy'
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.pitch.min,
                    g.phone.pitch.max, g.phone.pitch.mean)
        print(q.cypher())
        results = q.all()

        assert(results[0]['Min_F0'] == 95.8)
        assert(results[0]['Max_F0'] == 100)
        assert(round(results[0]['Mean_F0'], 2) == 97.72)

def test_query_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_algorithm = 'dummy'
        expected_formants = {Decimal('4.23'): {'F1':501, 'F2': 1500, 'F3': 2500},
                            Decimal('4.24'): {'F1':502, 'F2': 1499, 'F3': 2500},
                            Decimal('4.25'): {'F1':503, 'F2': 1498, 'F3': 2500},
                            Decimal('4.26'): {'F1':504, 'F2': 1497, 'F3': 2500},
                            Decimal('4.27'): {'F1':505, 'F2': 1496, 'F3': 2500}}
        g.save_formants('acoustic_corpus', expected_formants)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.formants.track)
        print(q.cypher())
        results = q.all()

        times = list(expected_formants.keys())

        print(sorted(expected_formants.items()))
        print(sorted(results[0].track.items()))
        for k, v in results[0].track.items():
            assert(round(v['F1'],1) == expected_formants[k]['F1'])
            assert(round(v['F2'],1) == expected_formants[k]['F2'])
            assert(round(v['F3'],1) == expected_formants[k]['F3'])

def test_query_aggregate_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_algorithm = 'dummy'

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.formants.min,
                    g.phone.formants.max, g.phone.formants.mean)
        print(q.cypher())
        results = q.all()

        assert(results[0]['Min_F1'] == 501)
        assert(results[0]['Max_F1'] == 505)
        assert(round(results[0]['Mean_F1'], 2) == 503)

        assert(results[0]['Min_F2'] == 1496)
        assert(results[0]['Max_F2'] == 1500)
        assert(round(results[0]['Mean_F2'], 2) == 1498)

        assert(results[0]['Min_F3'] == 2500)
        assert(results[0]['Max_F3'] == 2500)
        assert(round(results[0]['Mean_F3'], 2) == 2500)

def test_export_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.pitch_algorithm = 'dummy'

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label.column_name('label'), g.phone.pitch.track)
        print(q.cypher())
        results = q.all()

        t = results.rows_for_csv()
        assert(next(t) == {'label':'ow','time': Decimal('4.23'), 'F0': 98})
        assert(next(t) == {'label':'ow','time': Decimal('4.24'), 'F0': 100})
        assert(next(t) == {'label':'ow','time': Decimal('4.25'), 'F0': 99})
        assert(next(t) == {'label':'ow','time': Decimal('4.26'), 'F0': 95.8})
        assert(next(t) == {'label':'ow','time': Decimal('4.27'), 'F0': 95.8})
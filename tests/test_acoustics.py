import os
import pytest

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Average

def test_wav_info(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        sf = g.discourse_sound_file('acoustic_corpus')
        assert(sf.sampling_rate == 16000)
        assert(sf.n_channels == 1)

def test_analyze_acoustics(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.analyze_acoustics()

@pytest.mark.xfail
def test_query_pitch(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.pitch.column_name('pitch'))
        results = q.all()
        expected_pitch = {4.23: 98.2,
                            4.24:390.2,
                            4.25:0.0,
                            4.26:95.8,
                            4.27:95.8}
        times = list(results[0].F0.keys())
        mean_time = sum(times)/ len(times)
        expected_mean_time = sum(expected_pitch.keys())/ len(expected_pitch.keys())
        assert(abs(mean_time - expected_mean_time) < 0.01)
        print(sorted(expected_pitch.items()))
        print(sorted(results[0].F0.items()))
        for k, v in results[0].F0.items():
            assert(round(v,1) == expected_pitch[k])

def test_query_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.formants.column_name('formants'))

def test_query_formants_aggregate_group_by(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        q = q.columns(Average(g.phone.formants))

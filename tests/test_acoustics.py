import os
import pytest

from polyglotdb import CorpusContext

from polyglotdb.graph.func import Average

def test_wav_info(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        sf = g.discourse_sound_file('acoustic_corpus')
        assert(sf.sampling_rate == 16000)
        assert(sf.n_channels == 1)

@pytest.mark.xfail
def test_query_pitch(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.pitch.column_name('pitch'))
        results = q.all()
        expected_pitch = {4.23: 98.2,
                            4.24:390.2,
                            4.25:0.0,
                            4.26:95.8,
                            4.27:95.8}
        assert(set(results[0].pitch.keys()) == set(expected_pitch.keys()))
        for k, v in results[0].pitch.items():
            assert(round(v,1) == expected_pitch[k])

        assert(round(aq.max()[0].max_pitch, 1) == round(max(expected_pitch.values()), 1))

@pytest.mark.xfail
def test_query_formants(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label == 'aa')
        q = q.columns(g.phone.formants.column_name('formants'))
        aq = g.query_acoustics(q).formants('acousticsim')


@pytest.mark.xfail
def test_query_formants_aggregate_group_by(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        q = g.query_graph(g.phone).filter(g.phone.label.in_(['aa','ae']))
        q = q.columns(Average(g.phone.formants))



def test_analyze_acoustics(graph_db):
    with CorpusContext('acoustic', **graph_db) as g:
        g.analyze_acoustics()

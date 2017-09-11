import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


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


@acoustic
def test_analyze_intensity_basic_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.intensity_source = 'praat'
        g.config.praat_path = praat_path
        g.analyze_intensity()
        assert (g.has_intensity(g.discourses[0], 'praat'))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.intensity.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'intensity_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (r.track)

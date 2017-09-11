import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.base import analyze_formant_points
from polyglotdb.acoustics.formants.refined import get_mean_SD, \
    analyze_formant_points_refinement, save_formant_point_data

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


@acoustic
def test_analyze_formants_basic_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        g.analyze_formant_tracks()
        assert (g.has_formants(g.discourses[0], 'praat'))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (r.track)


def test_analyze_formants_vowel_segments(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        g.analyze_vowel_formant_tracks(vowel_inventory=vowel_inventory)
        assert (g.has_formants(g.discourses[0], 'praat'))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_vowel_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        print(len(results))
        for r in results:
            # print(r.track)
            assert (r.track)


@acoustic
def test_analyze_formants_gendered_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.formant_source = 'praat'
        gender_dict = {'gender': 'male'}
        g.hierarchy.add_speaker_properties(g, gender_dict.items())
        assert (g.hierarchy.has_speaker_property('gender'))
        g.config.praat_path = praat_path
        g.analyze_formant_tracks()
        assert (g.has_formants(g.discourses[0], 'praat'))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (r.track)


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
        assert (round(results[0]['Min_F1'], 0) > 0)
        assert (round(results[0]['Max_F1'], 0) > 0)
        assert (round(results[0]['Mean_F1'], 0) > 0)

        assert (round(results[0]['Min_F2'], 0) > 0)
        assert (round(results[0]['Max_F2'], 0) > 0)
        assert (round(results[0]['Mean_F2'], 0) > 0)

        assert (round(results[0]['Min_F3'], 0) > 0)
        assert (round(results[0]['Max_F3'], 0) > 0)
        assert (round(results[0]['Mean_F3'], 0) > 0)


def test_refine_formants(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, 'formant_vowel_data.csv')
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = 'ow'
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        old_data = analyze_formant_points(corpus_context=g, vowel_inventory=vowel_inventory)
        old_metadata = get_mean_SD(old_data)
        save_formant_point_data(g, old_data)
        assert (g.hierarchy.has_token_property('phone', 'F1'))
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name('F1'))
        q.to_csv(output_path)
        results = q.all()
        assert (len(results) > 0)

        for r in results:
            assert (r['F1'])

            # assert False


def test_extract_formants_full(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, 'full_formant_vowel_data.csv')
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = 'ow'
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        print("starting test")
        metadata = analyze_formant_points_refinement(g, vowel_inventory)
        assert (g.hierarchy.has_token_property('phone', 'F1'))
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name('F1'))
        q.to_csv(output_path)
        results = q.all()
        assert (len(results) > 0)

        for r in results:
            assert (r['F1'])

            # assert False, "dumb assert

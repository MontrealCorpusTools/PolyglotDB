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
        g.reset_acoustics()
        g.config.praat_path = praat_path
        g.analyze_formant_tracks(multiprocessing=False)
        assert (g.has_formants(g.discourses[0]))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (len(r.track))


def test_analyze_formants_vowel_segments(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        g.analyze_vowel_formant_tracks(vowel_inventory=vowel_inventory, multiprocessing=False)
        assert (g.has_formants(g.discourses[0]))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_vowel_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        print(len(results))
        for r in results:
            # print(r.track)
            assert (len(r.track))

        g.reset_formants()
        assert not g.has_formants(g.discourses[0])


@acoustic
def test_analyze_formants_gendered_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        gender_dict = {'gender': 'male'}
        g.hierarchy.add_speaker_properties(g, gender_dict.items())
        assert (g.hierarchy.has_speaker_property('gender'))
        g.config.praat_path = praat_path
        g.analyze_formant_tracks()
        assert (g.has_formants(g.discourses[0]))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'formant_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (len(r.track))


def test_query_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        g.reset_acoustics()
        expected_formants = {Decimal('4.23'): {'F1': 501, 'F2': 1500, 'F3': 2500},
                             Decimal('4.24'): {'F1': 502, 'F2': 1499, 'F3': 2498},
                             Decimal('4.25'): {'F1': 503, 'F2': 1498, 'F3': 2500},
                             Decimal('4.26'): {'F1': 504, 'F2': 1497, 'F3': 2502},
                             Decimal('4.27'): {'F1': 505, 'F2': 1496, 'F3': 2500}}
        g.save_formants('acoustic_corpus', expected_formants)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.formants.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_formants.items()))
        print(results[0].track)
        for point in results[0].track:
            assert (round(point['F1'], 1) == expected_formants[point.time]['F1'])
            assert (round(point['F2'], 1) == expected_formants[point.time]['F2'])
            assert (round(point['F3'], 1) == expected_formants[point.time]['F3'])


def test_relative_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        means = {'F1': 503, 'F2': 1498, 'F3': 2500}
        sds = {'F1': 1.5811, 'F2': 1.5811, 'F3': 1.4142}

        expected_formants = {Decimal('4.23'): {'F1': 501, 'F2': 1500, 'F3': 2500},
                             Decimal('4.24'): {'F1': 502, 'F2': 1499, 'F3': 2498},
                             Decimal('4.25'): {'F1': 503, 'F2': 1498, 'F3': 2500},
                             Decimal('4.26'): {'F1': 504, 'F2': 1497, 'F3': 2502},
                             Decimal('4.27'): {'F1': 505, 'F2': 1496, 'F3': 2500}}
        for k, v in expected_formants.items():
            for f in ['F1', 'F2', 'F3']:
                expected_formants[k]['{}_relativized'.format(f)] = (v[f] - means[f]) / sds[f]

        g.relativize_formants(by_speaker=True)
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        ac = g.phone.formants
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert (len(results[0].track) == len(expected_formants.items()))
        print(sorted(expected_formants.items()))
        print(results[0].track)
        for point in results[0].track:
            print(point)
            for f in ['F1', 'F2', 'F3']:
                assert (round(point[f], 4) == round(expected_formants[point.time]['{}_relativized'.format(f)], 4))

        g.reset_relativized_formants()

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        ac = g.phone.formants
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == 0


def test_query_aggregate_formants(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
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

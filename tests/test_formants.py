import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.base import analyze_formants_initial_pass
from polyglotdb.acoustics.formants.refined import get_mean_SD, refine_formants, \
    analyze_formants_refinement, save_formant_point_data

def test_refine_formants(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, 'formant_vowel_data.csv')
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = 'ow'
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        old_data = analyze_formants_initial_pass(corpus_context=g, vowel_inventory=vowel_inventory)
        old_metadata = get_mean_SD(old_data)
        data = refine_formants(corpus_context=g, prototype_metadata=old_metadata,
                               vowel_inventory=vowel_inventory)
        save_formant_point_data(g, data)
        assert(g.hierarchy.has_token_property('phone','F1'))
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name('F1'))
        q.to_csv(output_path)
        results = q.all()
        assert (len(results) > 0)

        for r in results:
            assert (r['F1'])

        #assert False


def test_extract_formants_full(acoustic_utt_config, praat_path, export_test_dir):
    output_path = os.path.join(export_test_dir, 'full_formant_vowel_data.csv')
    with CorpusContext(acoustic_utt_config) as g:
        test_phone_label = 'ow'
        g.config.formant_source = 'praat'
        g.config.praat_path = praat_path
        vowel_inventory = ['ih', 'iy', 'ah', 'uw', 'er', 'ay', 'aa', 'ae', 'eh', 'ow']
        print("starting test")
        metadata = analyze_formants_refinement(g, vowel_inventory)
        assert(g.hierarchy.has_token_property('phone','F1'))
        q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
        q = q.columns(g.phone.begin, g.phone.end, g.phone.F1.column_name('F1'))
        q.to_csv(output_path)
        results = q.all()
        assert (len(results) > 0)

        for r in results:
            assert (r['F1'])

        # assert False, "dumb assert

import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext
from polyglotdb.acoustics.formant import analyze_formants_vowel_segments_new, get_mean_SD, refine_formants, extract_formants_full
from polyglotdb.acoustics.analysis import generate_phone_segments_by_speaker

from acousticsim.analysis.praat import run_script


"""def test_analyze_formants_vowel_segments_new(acoustic_utt_config, praat_path):
	with CorpusContext(acoustic_utt_config) as g:
		test_phone_label = 'ow'
		g.config.formant_source = 'praat'
		g.config.praat_path = praat_path
		vowel_inventory = ['ih','iy','ah','uw','er','ay','aa','ae','eh','ow']
		data = analyze_formants_vowel_segments_new(corpus_context=g, vowel_inventory=vowel_inventory)
		assert(g.has_formants(g.discourses[0], 'praat'))
		q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
		q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
		output_path = '/Users/mlml/Documents/testing/formant_vowel_data.csv'
		q.to_csv(output_path)
		results = q.all()
		assert(len(results) > 0)

		# Counts number of remaining tracks with said phone (not counting those whose formants were undetermined)
		counter = 0
		#print(data)
		for d in data:
			for d2 in d:
				for key in d2.items():
					if d2['fields']['phone'].strip() == test_phone_label:
						counter = counter + 1
						break

		# Counts difference between q.all() filled tracks and empty tracks
		empty_tracks = 0
		for r in results:
			if not r.track:
				empty_tracks = empty_tracks + 1
		full_tracks = len(results) - empty_tracks

		# The only tracks disregarded from q.all() should be because they are empty
		assert(counter == full_tracks)

		#assert False, "dumb assert to make PyTest print my stuff"""



def test_refine_formants(acoustic_utt_config, praat_path):
	with CorpusContext(acoustic_utt_config) as g:
		test_phone_label = 'ow'
		g.config.formant_source = 'praat'
		g.config.praat_path = praat_path
		vowel_inventory = ['ih','iy','ah','uw','er','ay','aa','ae','eh','ow']
		old_data = analyze_formants_vowel_segments_new(corpus_context=g, vowel_inventory=vowel_inventory)
		old_metadata = get_mean_SD(g, old_data)
		data = refine_formants(corpus_context=g, prototype_data=old_data, prototype_metadata=old_metadata, vowel_inventory=vowel_inventory)
		assert(g.has_formants(g.discourses[0], 'praat'))
		q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
		q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
		output_path = '/Users/mlml/Documents/testing/formant_vowel_data.csv'
		q.to_csv(output_path)
		results = q.all()
		assert(len(results) > 0)

		for r in results:
			assert(r.track)

		#assert False, "dumb assert"""


def test_extract_formants_full(acoustic_utt_config, praat_path):
	with CorpusContext(acoustic_utt_config) as g:
		test_phone_label = 'ow'
		g.config.formant_source = 'praat'
		g.config.praat_path = praat_path
		vowel_inventory = ['ih','iy','ah','uw','er','ay','aa','ae','eh','ow']
		print("starting test")
		prototype_data, metadata, data = extract_formants_full(g, vowel_inventory)
		assert(g.has_formants(g.discourses[0], 'praat'))
		q = g.query_graph(g.phone).filter(g.phone.label == test_phone_label)
		q = q.columns(g.phone.begin, g.phone.end, g.phone.formants.track)
		output_path = '/Users/mlml/Documents/testing/formant_vowel_data.csv'
		q.to_csv(output_path)
		results = q.all()
		assert(len(results) > 0)

		for r in results:
			assert(r.track)

		#assert False, "dumb assert

import time
import logging

import os
import math
import csv

from functools import partial

from polyglotdb.sql.models import SoundFile, Discourse

from polyglotdb.exceptions import GraphQueryError, AcousticError

from polyglotdb.acoustics.analysis import generate_phone_segments_by_speaker
from polyglotdb.corpus.audio import sanitize_formants, to_nano

from acousticsim.analysis.formants import (signal_to_formants as ASFormants_signal, file_to_formants as ASFormants_file,
										   signal_to_formants_praat as PraatFormants_signal,
										   file_to_formants_praat as PraatFormants_file)

from acousticsim.main import analyze_long_file, analyze_file_segments
from acousticsim.multiprocessing import generate_cache, default_njobs
from acousticsim.analysis.praat import run_script, read_praat_out
from acousticsim.analysis.helper import ASTemporaryWavFile, fix_time_points

import sys
import io

from statistics import mean, stdev
import numpy as np
from numpy import linalg
import scipy
from scipy import linalg

def sanitize_bandwidths(value):
    try:
        b1 = value['B1'][0]
    except TypeError:
        b1 = value['B1']
    if b1 is None:
        b1 = 0
    try:
        b2 = value['B2'][0]
    except TypeError:
        b2 = value['B2']
    if b2 is None:
        b2 = 0
    try:
        b3 = value['B3'][0]
    except TypeError:
        b3 = value['B3']
    if b3 is None:
        b3 = 0
    return b1, b2, b3

def signal_to_formants_praat_new(signal, sr, praat_path=None, num_formants=5, max_freq=5000,
							 time_step=0.01, win_len=0.025,
							 begin=None, padding=None):
	with ASTemporaryWavFile(signal, sr) as wav_path:
		output = file_to_formants_praat_new(wav_path, praat_path, num_formants, max_freq, time_step, win_len)
	duration = signal.shape[0] / sr
	return fix_time_points(output, begin, padding, duration)


def file_to_formants_praat_new(file_path, praat_path=None, num_formants=5, max_freq=5000,
						   time_step=0.01, win_len=0.025):
	script_dir = os.path.dirname(os.path.abspath(__file__))
	script = os.path.join(script_dir, 'formants_bandwidth.praat')

	if praat_path is None:
		praat_path = 'praat'
		if sys.platform == 'win32':
			praat_path += 'con.exe'

	listing = run_script(praat_path, script, file_path, time_step,
						 win_len, num_formants, max_freq)
	output = read_praat_out(listing)
	return output

def generate_base_formants_function_new(corpus_context, signal=False, gender=None):
	algorithm = corpus_context.config.formant_source
	max_freq = 5500
	#if gender == 'M':
	#	max_freq = 5000
	if algorithm == 'praat':
		if getattr(corpus_context.config, 'praat_path', None) is None:
			raise (AcousticError('Could not find the Praat executable'))
		if signal:
			PraatFormants = signal_to_formants_praat_new
		else:
			PraatFormants = file_to_formants_praat_new
		formant_function = partial(PraatFormants,
								   praat_path=corpus_context.config.praat_path,
								   max_freq=max_freq, num_formants=5, win_len=0.025,
								   time_step=0.01)
	return formant_function

def generate_variable_formants_function(corpus_context, nformants, signal=False, gender=None):
	algorithm = corpus_context.config.formant_source
	max_freq = 5500
	if algorithm == 'praat':
		if getattr(corpus_context.config, 'praat_path', None) is None:
			raise (AcousticError('Could not find the Praat executable'))
		if signal:
			PraatFormants = signal_to_formants_praat_new
		else:
			PraatFormants = file_to_formants_praat_new
		formant_function = partial(PraatFormants,
								   praat_path=corpus_context.config.praat_path,
								   max_freq=max_freq, num_formants=nformants, win_len=0.025,
								   time_step=0.01)
	return formant_function

def save_formant_tracks_new(corpus_context, measurement, tracks, speaker, to_save):
		if measurement == 'formants':
			source = corpus_context.config.formant_source
		else:
			raise (NotImplementedError('This function only saves formant tracks.'))
		data = []
		for seg, track in tracks.items():
			if not len(track.keys()):
				print(seg)
				continue
			file_path, begin, end, channel = seg
			discourse = corpus_context.sql_session.query(Discourse).join(SoundFile).filter(
				SoundFile.vowel_filepath == file_path).first()
			discourse = discourse.name
			phone_type = getattr(corpus_context, corpus_context.phone_name)
			min_time = min(track.keys())
			max_time = max(track.keys())
			q = corpus_context.query_graph(phone_type).filter(phone_type.discourse.name == discourse)
			q = q.filter(phone_type.end >= min_time).filter(phone_type.begin <= max_time)
			q = q.columns(phone_type.label.column_name('label'),
						  phone_type.begin.column_name('begin'),
						  phone_type.end.column_name('end')).order_by(phone_type.begin)
			phones = [(x['label'], x['begin'], x['end']) for x in q.all()]
			for time_point, value in track.items():
				label = None
				for i, p in enumerate(phones):
					if p[1] > time_point:
						break
					label = p[0]
					if i == len(phones) - 1:
						break
				else:
					label = None
				if label is None:
					continue
				t_dict = {'speaker': speaker, 'discourse': discourse, 'channel': channel, 'source': source}
				fields = {'phone': label}
				if measurement == 'formants':
					F1, F2, F3 = sanitize_formants(value)
					if F1 > 0:
						fields['F1'] = F1
					if F2 > 0:
						fields['F2'] = F2
					if F3 > 0:
						fields['F3'] = F3

					B1, B2, B3 = sanitize_bandwidths(value)
					if B1 > 0:
						fields['B1'] = math.log(B1)
					if B2 > 0:
						fields['B2'] = math.log(B2)
					if B3 > 0:
						fields['B3'] = math.log(B3)
			   
				d = {'measurement': measurement,
					 'tags': t_dict,
					 'time': to_nano(time_point),
					 'fields': fields
					 }
				if 'F1' in d['fields']:
					data.append(d)
					
		if to_save == True:
			corpus_context.acoustic_client().write_points(data, batch_size=1000)
		return data

def analyze_formants_vowel_segments_new(corpus_context, call_back=None, stop_check=None, vowel_inventory=None):
	# ------------- Step 1 -------------
	# encodes vowel inventory into a phone class if it's specified
	if vowel_inventory is not None:
		corpus_context.encode_class(vowel_inventory, 'vowel')
	# gets segment mapping of phones that are vowels
	segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)
	if call_back is not None:
		call_back('Analyzing files...')
	# go through each phone
	#v = 0
	#formant_function = ""
	for i, (speaker, v) in enumerate(segment_mapping.items()):
		formant_function = generate_base_formants_function_new(corpus_context, signal=True)		# Make formant function
	output = analyze_file_segments(v, formant_function, padding=None, stop_check=stop_check)	# Analyze the phone
	data = save_formant_tracks_new(corpus_context, 'formants', output, speaker, True)			# Save tracks
	return data

def get_stdev(data):
	if len(data) == 1:	# SD of one value is undefined
		return None
	else:
		return stdev(data)

def get_mean_SD(corpus_context, data):
	# Make a dictionary with {vowel class : [[all_means], [all_SDs]]}
	# Where all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean], etc.
	metadata = {}

	phones = []
	for line in data:
		phone = line['fields']['phone']
		if phone not in phones:
			phones.append(phone)

	for phone in phones:
		f1, f2, f3 = [], [], []
		b1, b2, b3 = [], [], []

		for line in data:
			if line['fields']['phone'] == phone:
				f1.append(line['fields']['F1'])
				f2.append(line['fields']['F2'])
				f3.append(line['fields']['F3'])
				b1.append(line['fields']['B1'])
				b2.append(line['fields']['B2'])
				b3.append(line['fields']['B3'])

		f1_mean, f2_mean, f3_mean = mean(f1), mean(f2), mean(f3)
		b1_mean, b2_mean, b3_mean = mean(b1), mean(b2), mean(b3)

		f1_SD, f2_SD, f3_SD = get_stdev(f1), get_stdev(f2), get_stdev(f3)
		b1_SD, b2_SD, b3_SD = get_stdev(b1), get_stdev(b2), get_stdev(b3)

		all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean]
		all_SDs = [f1_SD, f2_SD, f3_SD, b1_SD, b2_SD, b3_SD]
		measurements = [all_means, all_SDs]
		metadata[phone] = measurements

	return metadata

def save_mean_SD(corpus_context, metadata):
	#Save mean and standard deviations to Neo4j as phone properties
	statement = '''WITH'''

def get_measurement_lists_without_average(data, vowel):
	new_line = []
	return_list = []
	for line in data:
		if line['fields']['phone'].strip() == vowel.strip():
			new_line = []
			new_line.append(line['fields']['F1'])
			new_line.append(line['fields']['F2'])
			new_line.append(line['fields']['F3'])
			new_line.append(line['fields']['B1'])
			new_line.append(line['fields']['B2'])
			new_line.append(line['fields']['B3'])
			return_list.append(new_line)
	return return_list

def get_mahalanobis(prototype, observation, sample):
	prototype = np.array(prototype)
	observation = np.array(observation)
	sample = np.array(sample)
	covariance = np.cov(sample, rowvar=0)
	try:
		inverse_covariance = np.linalg.inv(covariance)
	except:
		print("There's only one observation of this phone, so Mahalanobis distance isn't useful here.")
		return math.inf
	distance = scipy.spatial.distance.mahalanobis(prototype, observation, inverse_covariance)
	return distance

def refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory, call_back=None, stop_check=None):
	# ------------- Step 2 -------------
	# encodes vowel inventory into a phone class if it's specified
	if vowel_inventory is not None:
		corpus_context.encode_class(vowel_inventory, 'vowel')
	# gets segment mapping of phones that are vowels
	segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)
	if call_back is not None:
		call_back('Analyzing files...')
	
	# go through each phone
	#num_formants_list = [3, 4, 5, 6]
	num_formants_list = [4, 5, 6, 7]	# Off by one error, probably how Praat measures it from F0
	best_distance = math.inf
	best_track = 0

	testing_dict = {}

	for vowel in vowel_inventory:
		print("Looking at vowel", vowel)
		for num in num_formants_list:
			#v = 0
			#call_back("hello")
			for i, (speaker, v) in enumerate(segment_mapping.items()):
				#call_back("i: ", i)
				#print("speaker: ", speaker)
				#print("v: ", v)
				formant_function = generate_variable_formants_function(corpus_context, num, signal=True)	# Make formant function
			output = analyze_file_segments(v, formant_function, padding=None, stop_check=stop_check)		# Analyze the phone
			new_data = save_formant_tracks_new(corpus_context, 'formants', output, speaker, False)			# Get data

			if vowel in prototype_metadata:
				prototype_means = prototype_metadata[vowel][1]
			else:
				continue
			new_observation = []
			new_observation_list = []

			vowel_found = False
			for line in new_data:
				if line['fields']['phone'] == vowel:
					vowel_found = True
					new_observation = []
					new_observation.append(line['fields']['F1'])
					new_observation.append(line['fields']['F2'])
					new_observation.append(line['fields']['F3'])
					new_observation.append(line['fields']['B1'])
					new_observation.append(line['fields']['B2'])
					new_observation.append(line['fields']['B3'])
					new_observation_list.append(new_observation)

			if vowel_found == False:
				print("Can't find this vowel in the new data")
				continue

			if len(new_observation_list) == 1:
				print("This vowel only has one observation, so skip for now:", vowel, num)
				continue

			# Get smallest distance and the best track
			for observation in new_observation_list:
				sample = get_measurement_lists_without_average(prototype_data, vowel)
				distance = get_mahalanobis(prototype_means, observation, sample)
				if distance < best_distance:
					best_distance = distance
					best_track = observation

		print("best mahalanobis distance for vowel", vowel, best_distance)

		testing_dict[vowel] = best_distance

		# Save best track
		

	return testing_dict

def extract_formants_full(corpus_context, vowel_inventory):
	# Step 1: Get prototypes
	prototype_data = analyze_formants_vowel_segments_new(corpus_context, vowel_inventory=vowel_inventory)
	prototype_metadata = get_mean_SD(corpus_context, prototype_data)

	# Step 2: Get best formants from varying nformants
	refined_data = refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory)
	print(refined_data)

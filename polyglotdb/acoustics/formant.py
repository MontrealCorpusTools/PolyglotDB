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

from subprocess import Popen, PIPE
from acousticsim.exceptions import AcousticSimPraatError

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

def signal_to_formants_praat_new(signal, sr, praat_path=None, num_formants=5, min_formants=4, max_formants=7, max_freq=5000,
							 time_step=0.01, win_len=0.025,
							 begin=None, padding=None, multiple_measures=False):
	with ASTemporaryWavFile(signal, sr) as wav_path:
		output = file_to_formants_praat_new(wav_path, praat_path, num_formants, min_formants, max_formants, max_freq, time_step, win_len, padding, multiple_measures)
	duration = signal.shape[0] / sr
	if multiple_measures == False:
		#print(fix_time_points(output, begin, padding, duration))
		return_value = fix_time_points(output, begin, padding, duration)
		for key, val in return_value.items():
			if all(value == 0 for value in val.values()):
				print("Praat is measuring all values to be 0.")
			break
		return fix_time_points(output, begin, padding, duration)
	else:
		return_list = []
		for item in output:
			to_append = fix_time_points(item, begin, padding, duration)
			to_append = {track_nformants(to_append) : to_append}
			return_list.append(to_append)
		return return_list

def track_nformants(track):
	nformants = 0
	for key, value in track.items():
		if 'F7' in value:
			nformants = 7
		elif 'F6' in value:
			nformants = 6
		elif 'F5' in value:
			nformants = 5
		else:
			nformants = 4
	return nformants

def file_to_formants_praat_new(file_path, praat_path=None, num_formants=5, min_formants=4, max_formants=7, max_freq=5000,
						   time_step=0.01, win_len=0.025, padding=None, multiple_measures=False):
	if praat_path is None:
		praat_path = 'praat'
		if sys.platform == 'win32':
			praat_path += 'con.exe'

	script_dir = os.path.dirname(os.path.abspath(__file__))

	if multiple_measures == False:
		script = os.path.join(script_dir, 'formants_bandwidth.praat')
		listing = run_script(praat_path, script, file_path, time_step,
							 win_len, num_formants, max_freq, padding)
		output = read_praat_out(listing)
		#if all(value == 0 for value in output.values()):
		#	print("Praat is measuring all values to be 0.")
	else:
		script = os.path.join(script_dir, 'multiple_formants_bandwidth.praat')
		listing = run_script(praat_path, script, file_path, time_step,
							 win_len, min_formants, max_formants, max_freq, padding)
		output = ""
		listing_list = listing.split("\n\n")
		output_list = []
		for item in listing_list:
			item = item.replace(r"\n", "")
			item = item.replace(r"\t", "	")
			output = read_praat_out(item)
			output_list.append(output)
		output = output_list
		if output_list == []:
			print("Output list empty.")
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
								   time_step=0.01, multiple_measures=False)
	return formant_function

def generate_variable_formants_function_new(corpus_context, minformants, maxformants, signal=False, gender=None):
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
								   max_freq=max_freq, min_formants=minformants, max_formants=maxformants, win_len=0.025,
								   time_step=0.01, multiple_measures=True)
	return formant_function

def save_formant_tracks_new(corpus_context, measurement, tracks, to_save, speaker=None):
		if measurement == 'formants':
			source = corpus_context.config.formant_source
		else:
			raise (NotImplementedError('This function only saves formant tracks.'))
		data = []
		for seg, track in tracks.items():
			if not len(track.keys()):
				print(seg)
				continue
			file_path, begin, end, channel, label = seg[:5]
			discourse = corpus_context.sql_session.query(Discourse).join(SoundFile).filter(
				SoundFile.vowel_filepath == file_path).first()
			discourse = discourse.name
			phone_type = getattr(corpus_context, corpus_context.phone_name)
			for time_point, value in track.items():
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
					 'fields': fields,
					 'duration': (end-begin),
					 'begin': begin,
					 'end': end
					 }
				if 'F1' in d['fields']:
					data.append(d)

		if to_save == True:
			corpus_context.acoustic_client().write_points(data, batch_size=1000)
		return data

def analyze_formants_vowel_segments_new(corpus_context, call_back=None, stop_check=None, vowel_inventory=None):
	# ------------- Step 1: Prototypes -------------
	# Encodes vowel inventory into a phone class if it's specified
	if vowel_inventory is not None:
		corpus_context.encode_class(vowel_inventory, 'vowel')

	# Gets segment mapping of phones that are vowels
	segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)

	# Cleans segment mapping (no speaker info, and throws out intervals too short)
	strip_speakers = []
	for speaker, v_list in segment_mapping.items():
		for v in v_list:
			strip_speakers.append(v)
	segment_mapping = strip_speakers

	if call_back is not None:
		call_back('Analyzing files...')

	# Go through each segment
	data = []
	vowel = ""
	for i, v in enumerate(segment_mapping):
		print("Segment", i+1, "of", len(segment_mapping), ":", v)
		formant_function = generate_base_formants_function_new(corpus_context, signal=True)				# Make formant function
		output = analyze_file_segments(v, formant_function, padding=.25, stop_check=stop_check)		# Analyze the phone
		data_point = save_formant_tracks_new(corpus_context, 'formants', output, True, speaker=None)	# Save tracks
		data.append(data_point)
	return data

def get_stdev(data):
	if len(data) == 1:	# SD of one value is undefined
		return None
	else:
		return stdev(data)

def get_mean_SD(corpus_context, data):
	# Make a dictionary with {vowel token : [[all_means], [all_SDs]]}
	# Where all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean], etc.
	metadata = {}

	phones = []
	for item in data:
		for line in item:
			phone = line['fields']['phone']
			if phone not in phones:
				phones.append(phone)

	for phone in phones:
		f1, f2, f3 = [], [], []
		b1, b2, b3 = [], [], []

		for item in data:
			for line in item:
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

def get_measurement_lists_without_average(data, vowel):	# Gets "sample" for Mahalanobis distance
	new_line = []
	return_list = []
	for item in data:
		for line in item:
			if line['fields']['phone'].strip() == vowel.strip():
				new_line = []
				duration = line['duration']
				new_line.append(line['fields']['F1'])
				new_line.append(line['fields']['F2'])
				new_line.append(line['fields']['F3'])
				new_line.append(line['fields']['B1'])
				new_line.append(line['fields']['B2'])
				new_line.append(line['fields']['B3'])
				return_list.append(new_line)
	return return_list

def get_mahalanobis(prototype, observation, inverse_covariance):
	prototype = np.array(prototype)
	observation = np.array(observation)
	inverse_covariance = np.array(inverse_covariance)
	distance = scipy.spatial.distance.mahalanobis(prototype, observation, inverse_covariance)
	return distance

def refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory, call_back=None, stop_check=None):
	# ------------- Step 2: Varying formants -------------
	# Encodes vowel inventory into a phone class if it's specified
	if vowel_inventory is not None:
		corpus_context.encode_class(vowel_inventory, 'vowel')

	# Gets segment mapping of phones that are vowels
	segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)

	# Cleans segment mapping (no speaker info, and throws out intervals too short)
	strip_speakers = []
	for speaker, v_list in segment_mapping.items():
		for v in v_list:
			strip_speakers.append(v)
	segment_mapping = strip_speakers
	new_mapping = []
	for segment in segment_mapping:
		duration = segment[2] - segment[1]
		if duration >= 0.07:
			new_mapping.append(segment)
	segment_mapping = new_mapping

	if call_back is not None:
		call_back('Analyzing files...')

	samples = {}
	testing_dict = {}
	data_points = {}

	# For each vowel token, collect the formant measurements
	# Pick the best track that is closest to the averages gotten from prototypes
	for i, seg in enumerate(segment_mapping):
		vowel = seg[4]
		print()
		print("Examining token", i+1, "of", len(segment_mapping), ":", seg)

		# Make sure the vowel in question is in the data, otherwise it's a pointless iteration
		if vowel in prototype_metadata:
			prototype_means = prototype_metadata[vowel][1]
		else:
			print("Continuing. Vowel for this segment, while in inventory, is not in the data.")
			best_distance = "not in data"
			continue

		#segment_mapping = new_mapping

		if vowel not in samples:
			sample = get_measurement_lists_without_average(prototype_data, vowel)	# Gets sample for Mahalanobis distance ready
		else:
			sample = samples[vowel]

		if len(sample) < 6:
			print("Not enough observations of vowel \'", vowel, "\', at least 6 are needed.")
			best_distance = "too short"
			continue

		# Measure with varying levels of formants
		min_formants = 4	# Off by one error, probably how Praat measures it from F0
							# This really measures with 3 formants: F1, F2, F3. And so on.
		max_formants = 7

		formant_function = generate_variable_formants_function_new(corpus_context, min_formants, max_formants, signal=True)	# Make formant function (VARIABLE)
		output = analyze_file_segments(seg, formant_function, padding=None, stop_check=stop_check)							# Analyze the phone

		track_collection = []																								# Organize data
		for key, value in output.items():
			for item in value:
				data_point = {key : item}
				for header, info in data_point.items():
					for nformants, formants in info.items():
						formants = {header : formants}
						measurements = save_formant_tracks_new(corpus_context, 'formants', formants, False, speaker=None)	# Get formatted data
						if not measurements:
							continue	# If Praat couldn't measure formants
						else:
							measurements = measurements[0]
							data_point = {(header, nformants) : measurements}
							track_collection.append(data_point)
		new_observation = []
		new_observation_list = []

		# Prepare JUST the formant values for distance calculation
		for track in track_collection:
			for nformants, data in track.items():
				new_observation = []
				try:
					new_observation.append(data['fields']['F1'])
					new_observation.append(data['fields']['F2'])
					new_observation.append(data['fields']['F3'])
					new_observation.append(data['fields']['B1'])
					new_observation.append(data['fields']['B2'])
					new_observation.append(data['fields']['B3'])
					new_observation = {nformants : new_observation}
					new_observation_list.append(new_observation)
				except:
					print("There was an error with this track:")
					print(track)
					continue

		if len(new_observation_list) == 1:
			print("This vowel only has one observation, so skip for now:", vowel, num)	# Also shouldn't happen
			best_distance = "too short"
			continue

		# Get Mahalanobis distance between every new observation and the sample/means
		sample = np.array(sample)
		covariance = np.cov(sample.T)
		try:
			inverse_covariance = np.linalg.pinv(covariance)
		except:
			print("There's only one observation of this phone, so Mahalanobis distance isn't useful here.")	# Should never happen
			raise

		best_distance = math.inf
		best_track = 0
		best_output = 0
		best_info = ""

		for observation in new_observation_list:
			for info, data in observation.items():
				distance = get_mahalanobis(prototype_means, data, inverse_covariance)
				if distance < best_distance:	# Update "best" measures when new best distance is found
					best_distance = distance
					best_track = data
					best_output = output
					best_info = info

		print("BEST:", {best_info : data})
		if best_info == "":
			print("There was an error with this track.")	# Something going wrong - check later
			continue

		#testing_dict[vowel] = best_distance		# Debugging

		if best_distance == "too short" or best_distance == "not in data":
			continue

		# Reformulate the best track for the vowel (into the same format as other tracks above)
		return_track = {}
		return_track['F1'] = best_track[0]
		return_track['F2'] = best_track[1]
		return_track['F3'] = best_track[2]
		return_track['B1'] = best_track[3]
		return_track['B2'] = best_track[4]
		return_track['B3'] = best_track[5]

		for key, value in best_output.items():
			track_tuple = key
			for key2, value2 in value[0].items():
				for key3, value3 in value2.items():
					time = key3
			break

		track_to_save = {}
		track_value = {}
		track_value[time] = return_track
		track_to_save[track_tuple] = track_value

		#data_points[seg] = return_track
		data_points[best_info] = return_track

		# Save the track
		new_data = save_formant_tracks_new(corpus_context, 'formants', track_to_save, True, speaker=None)

	print()
	return data_points

def extract_formants_full(corpus_context, vowel_inventory):
	# Step 1: Get prototypes
	print("Generating prototypes...")
	prototype_data = analyze_formants_vowel_segments_new(corpus_context, vowel_inventory=vowel_inventory)
	prototype_metadata = get_mean_SD(corpus_context, prototype_data)

	print("Prototype data:")
	print(prototype_data)
	print()
	print("Metadata (means SDS:)")	# Debugging
	print(prototype_metadata)

	print()
	print()
	print()

	# Step 2: Get best formants from varying nformants
	print("Varying formants to find shortest distance and best track for each token...")
	refined_data = refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory)
	return prototype_data, refined_data

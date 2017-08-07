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
	"""Cleans bandwidth data from dictionary form.

	Parameters
	----------
	value : dict
		Observation values produced by reading out from Praat.

	Returns
	-------
	b1 : float
		The first bandwidth.
	b2 : float
		The second bandwidth.
	b3 : float
		The third bandwidth.
	"""
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
	"""Wrapper to call Praat and fix the time points before returning.

	Parameters
	----------
	signal : boolean
		Contains signal information.
	sr : float
		Contains sample rate information.
	praat_path : string
		Contains information about the Praat path if specialized.
	num_formants : int
		The number of formants to measure with on the first pass (default is 5).
	min_formants: int
		The minimum number of formants to measure with on subsequent passes (default is 4).
	max_formants : int
		The maximum number of formants to measure with on subsequent passes (default is 7).
	max_freq : int
		The cutoff frequency for measurement in Praat (default is 5000).
	time_step : float
		The time step for measurement in Praat (default is 0.01).
	win_len :
		The window length for measurement in praat (default is 0.025).
	begin : float
		Extra parameter for setting the beginning time.
	padding : float
		Extra parameter for setting the padding around the segment.
	multiple_measures : boolean
		Whether the call to Praat is iterating from `min_formants` to `max_formants` (multiple measures) or just measuring once with `num_formants`.

	Returns
	-------
	dict
		Output from a non-multiple-measures call to Praat, with fixed time points.
	list
		Output from a multiple-measures call to Praat, with fixed time points.
	"""
	#print("SR:", sr)
	with ASTemporaryWavFile(signal, sr) as wav_path:
		output = file_to_formants_praat_new(wav_path, praat_path, num_formants, min_formants, max_formants, max_freq, time_step, win_len, padding, multiple_measures)
		duration = signal.shape[0] / sr
		if multiple_measures == False:
			return_value = fix_time_points(output, begin, padding, duration)
			for key, val in return_value.items():
				if all(value == 0 for value in val.values()):
					print("Praat is measuring all values to be 0.")	# Should not occur, debugging
				break
			return fix_time_points(output, begin, padding, duration)
		else:
			return_list = []
			for item in output:
				to_append = fix_time_points(item, begin, padding, duration)
				to_append = {track_nformants(to_append) : to_append}
				if not to_append:
					continue
				return_list.append(to_append)
			return return_list

def track_nformants(track):
	"""Gets the number of formants used to arrive at a given track.

	Parameters
	----------
	track : dict
		The measured track.

	Returns
	-------
	nformants : int
		The number of formants used to measure that track.
	"""
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
	"""Wrapper to call Praat to measure formants and bandwidths.

	Parameters
	----------
	signal : boolean
		Contains signal information.
	sr : float
		Contains sample rate information.
	praat_path : string
		Contains information about the Praat path if specialized.
	num_formants : int
		The number of formants to measure with on the first pass (default is 5).
	min_formants: int
		The minimum number of formants to measure with on subsequent passes (default is 4).
	max_formants : int
		The maximum number of formants to measure with on subsequent passes (default is 7).
	max_freq : int
		The cutoff frequency for measurement in Praat (default is 5000).
	time_step : float
		The time step for measurement in Praat (default is 0.01).
	win_len :
		The window length for measurement in praat (default is 0.025).
	begin : float
		Extra parameter for setting the beginning time.
	padding : float
		Extra parameter for setting the padding around the segment.
	multiple_measures : boolean
		Whether the call to Praat is iterating from `min_formants` to `max_formants` (multiple measures) or just measuring once with `num_formants`.

	Returns
	-------
	dict
		Output from a non-multiple-measures call to Praat.
	list
		Output from a multiple-measures call to Praat.
	"""
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
		#print("OUTPUT:", output)
		return output
	else:
		script = os.path.join(script_dir, 'multiple_formants_bandwidth.praat')
		listing = run_script(praat_path, script, file_path, time_step,
							 win_len, min_formants, max_formants, max_freq, padding)
		output = ""
		listing_list = listing.split("\n\n")
		output_list = []
		for item in listing_list:
			output = read_praat_out(item)
			output_list.append(output)
		return output_list

def generate_base_formants_function_new(corpus_context, signal=False, gender=None):
	"""Generates a function used to call Praat to measure formants and bandwidths with fixed num_formants.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	signal : boolean
		Contains signal information.
	gender : string
		'M' or 'F'; used to modulate cutoff frequency in call to Praat. Default is None.

	Returns
	-------
	formant_function : Partial function object
		The function used to call Praat.
	"""
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
	"""Generates a function used to call Praat to measure formants and bandwidths with variable num_formants.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	minformants : int
		The minimum number of formants to measure with on subsequent passes (default is 4).
	maxformants : int
		The maximum number of formants to measure with on subsequent passes (default is 7).
	signal : boolean
		Contains signal information.
	gender : string
		'M' or 'F'; used to modulate cutoff frequency in call to Praat. Default is None.

	Returns
	-------
	formant_function : Partial function object
		The function used to call Praat.
	"""
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
	"""Reformats tracks and optionally saves them into PolyglotDB.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	measurement : string
		Must be "formants" to save down into the formant area of the database.
	tracks : dict
		Observed tracks from Praat.
	to_save : boolean
		Whether to save into PolyglotDB or not.
	speaker : string
		Information about the speaker (as of now unused).

	Returns
	-------
	data : list
		Reformatted track data.
	"""
	if measurement == 'formants':
		source = corpus_context.config.formant_source
	else:
		raise (NotImplementedError('This function only saves formant tracks.'))
	data = []
	for seg, track in tracks.items():
		if not len(track.keys()):
			#print("not len(track.keys()) from save_formant_tracks_new")
			#with open("error.txt", "a+") as f:
			#	f.write(str(seg))
			#	f.write("not len(track.keys()) from save_formant_tracks_new\n")
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

def analyze_formants_vowel_segments_new(corpus_context, call_back=None, stop_check=None, vowel_inventory=None, remove_short=None):
	"""First pass of the algorithm; generates prototypes.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	call_back : string
		Information about callback.
	stop_check : string
		Information about stop check.
	vowel_inventory : list
		A list of all the vowels (in strings) used in the corpus.
	remove_short : float, optional
		Segments with length shorter than this value (in milliseconds) will not be analyzed.

	Returns
	-------
	data2 : list
		Track data.
	"""
	# ------------- Step 1: Prototypes -------------
	# Encodes vowel inventory into a phone class if it's specified
	if vowel_inventory is not None:
		corpus_context.encode_class(vowel_inventory, 'vowel')

	# Gets segment mapping of phones that are vowels
	segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)

	# Cleans segment mapping (no speaker info)
	strip_speakers = []
	for speaker, v_list in segment_mapping.items():
		for v in v_list:
			strip_speakers.append(v)
	segment_mapping = strip_speakers

	# Debugging
	#segment_mapping = segment_mapping[:300]

	if remove_short:
		new_mapping = []
		for segment in segment_mapping:
			duration = segment[2] - segment[1]
			if duration >= remove_short:
				new_mapping.append(segment)
		segment_mapping = new_mapping

	if call_back is not None:
		call_back('Analyzing files...')

	# Go through each segment
	data = []
	vowel = ""
	for i, v in enumerate(segment_mapping):
		#with open("error.txt", "a+") as f:
		#	f.write(str(i))
		#	f.write("\n")
		print("Segment", i+1, "of", len(segment_mapping), ":", v)
		formant_function = generate_base_formants_function_new(corpus_context, signal=True)				# Make formant function
		output = analyze_file_segments(v, formant_function, padding=.25, stop_check=stop_check)			# Analyze the phone
		data_point = save_formant_tracks_new(corpus_context, 'formants', output, True, speaker=None)	# Save tracks
		data.append(data_point)

	data2 = [x for x in data if x]
	return data2

def get_mean_SD(corpus_context, data):
	"""Generates means for F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	data : list
		Track data from which means and covariance matrices will be generated.

	Returns
	-------
	metadata : dict
		Means and covariance matrices per vowel class.
	"""
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

		observation_list = []
		for item in data:
			for line in item:
				if line['fields']['phone'] == phone:
					observation = [
						line['fields']['F1'],
						line['fields']['F2'],
						line['fields']['F3'],
						line['fields']['B1'],
						line['fields']['B2'],
						line['fields']['B3']
					]
					observation_list.append(observation)
					f1.append(line['fields']['F1'])
					f2.append(line['fields']['F2'])
					f3.append(line['fields']['F3'])
					b1.append(line['fields']['B1'])
					b2.append(line['fields']['B2'])
					b3.append(line['fields']['B3'])

		f1_mean, f2_mean, f3_mean = mean(f1), mean(f2), mean(f3)
		b1_mean, b2_mean, b3_mean = mean(b1), mean(b2), mean(b3)
		all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean]

		observation_list = np.array(observation_list)
		cov = np.cov(observation_list.T)

		measurements = [all_means, cov.tolist()]
		metadata[phone] = measurements

	return metadata

def get_measurement_lists_without_average(data, vowel):	# Gets "sample" for Mahalanobis distance
	"""Gets all observed measurements for a vowel class (without means or covariance matrices).

	Parameters
	----------
	data : list
		Track data.
	vowel : string
		Vowel for which measurements will be gathered.

	Returns
	-------
	return_list : list
		All observed measurements of a given vowel.
	"""
	new_line = []
	return_list = []

	if isinstance(data, list):	# If coming from the first pass
		for item in data:
			for line in item:
				if line['fields']['phone'].strip() == vowel.strip():
					new_line = []
					new_line.append(line['fields']['F1'])
					new_line.append(line['fields']['F2'])
					new_line.append(line['fields']['F3'])
					new_line.append(line['fields']['B1'])
					new_line.append(line['fields']['B2'])
					new_line.append(line['fields']['B3'])
					return_list.append(new_line)
	elif isinstance(data, dict):	# If coming from a reiteration pass
		for key, value in data.items():
			if key[0][-1].strip() == vowel.strip():
				new_line = []
				new_line.append(value['F1'])
				new_line.append(value['F2'])
				new_line.append(value['F3'])
				new_line.append(value['B1'])
				new_line.append(value['B2'])
				new_line.append(value['B3'])
				return_list.append(new_line)

	return return_list

def get_mahalanobis(prototype, observation, inverse_covariance):
	"""Gets the Mahalanobis distance between an observation and the prototype.

	Parameters
	----------
	prototype : list
		Prototype data.
	observation : list
		Given observation of a vowel instance.
	inverse_covariance : list
		The inverse of the covariance matrix for the vowel class.

	Returns
	-------
	distance : float
		The Mahalanobis distance for the observation.
	"""
	prototype = np.array(prototype)
	observation = np.array(observation)
	inverse_covariance = np.array(inverse_covariance)
	distance = scipy.spatial.distance.mahalanobis(prototype, observation, inverse_covariance)
	return distance

def refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory, call_back=None, stop_check=None, remove_short=None):
	"""Second pass of the algorithm; gets measurement with lowest Mahalanobis distance from prototype using variable num_formants and saves the best track into PolyglotDB.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	prototype_data : list
		F1, F2, F3, B1, B2, B3 as measured with standard settings per vowel instance (the algorithm's first pass), used to generate prototypes.
	prototype_metadata : dict
		Means of F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.
	vowel_inventory : list
		A list of all the vowels (in strings) used in the corpus.
	call_back : string
		Information about callback.
	stop_check : string
		Information about stop check.
	remove_short : float, optional
		Segments with length shorter than this value (in milliseconds) will not be analyzed.

	Returns
	-------
	data_points : dict
		The best track (closest in Mahalanobis distance).
	"""
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

	# Debugging
	#segment_mapping = segment_mapping[:300]

	if remove_short:
		new_mapping = []
		for segment in segment_mapping:
			duration = segment[2] - segment[1]
			if duration >= remove_short:
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
		#with open("error.txt", "a+") as f:
		#	f.write(str(i))
		#	f.write("\n")
		vowel = seg[4]
		print()
		print("Examining token", i+1, "of", len(segment_mapping), ":", seg)

		# Make sure the vowel in question is in the data, otherwise it's a pointless iteration
		if vowel in prototype_metadata:
			prototype_means = prototype_metadata[vowel][0]
		else:
			print("Continuing. Vowel for this segment, while in inventory, is not in the data.")
			best_distance = "not in data"
			continue

		if vowel not in samples:
			sample = get_measurement_lists_without_average(prototype_data, vowel)	# Gets sample for Mahalanobis distance ready
			samples[vowel] = sample
		else:
			sample = samples[vowel]

		if len(sample) < 6:
			print("Not enough observations of vowel \'", vowel, "\', at least 6 are needed.")
			best_distance = "too short"
			continue

		# Measure with varying levels of formants
		min_formants = 4	# Off by one error, due to how Praat measures it from F0
							# This really measures with 3 formants: F1, F2, F3. And so on.
		max_formants = 7

		formant_function = generate_variable_formants_function_new(corpus_context, min_formants, max_formants, signal=True)	# Make formant function (VARIABLE)
		output = analyze_file_segments(seg, formant_function, padding=0.25, stop_check=stop_check)							# Analyze the phone

		skip = False
		for key, val in output.items():
			if val == [{0: {}}, {0: {}}, {0: {}}, {0: {}}]:	# Mimics "if not len(track.keys()):" in save_formant_tracks_new
				skip = True
				break
		if skip == True:
			#print("not len(track.keys()) from refine_formants")
			#with open("error.txt", "a") as f:
			#	f.write(str(i))
			#	f.write(str(seg))
			#	f.write("not len(track.keys()) from refine_formants\n")
			continue



		track_collection = []																								# Organize data
		for key, value in output.items():
			for item in value:
				data_point = {key : item}
				for header, info in data_point.items():
					for nformants, formants in info.items():
						formants = {header : formants}
						measurements = save_formant_tracks_new(corpus_context, 'formants', formants, False, speaker=None)	# Get formatted data
						if not measurements:
							print("not measurements")
							continue	# If Praat couldn't measure formants
						else:
							measurements = measurements[0]
							data_point = {(header, nformants) : measurements}
							track_collection.append(data_point)
		new_observation = []
		new_observation_list = []

		# Prepare JUST the formant values for distance calculation
		for track in track_collection:
			for header, data in track.items():
				nformants = header[1]
				new_observation = []
				try:
					new_observation.append(data['fields']['F1'])
					new_observation.append(data['fields']['F2'])
					new_observation.append(data['fields']['F3'])
					new_observation.append(data['fields']['B1'])
					new_observation.append(data['fields']['B2'])
					new_observation.append(data['fields']['B3'])
					new_observation = {header : new_observation}
					new_observation_list.append(new_observation)
				except:
					print("There was an error with this track (track collection):")
					print(track)
					#with open("error.txt", "a") as f:
					#	f.write(str(i))
					#	f.write(str(seg))
					#	f.write("There was an error with this track (track collection)\n")
					continue

		if len(new_observation_list) == 1:
			print("This vowel only has one observation, so skip for now:", vowel, num)	# Shouldn't happen
			best_distance = "too short"
			#with open("error.txt", "a") as f:
			#	f.write(str(i))
			#	f.write(str(seg))
			#	f.write("This vowel only has one observation\n")
			continue

		# Get Mahalanobis distance between every new observation and the sample/means
		covariance = np.array(prototype_metadata[vowel][1])
		try:
			inverse_covariance = np.linalg.pinv(covariance)
		except:
			print("There's only one observation of this phone, so Mahalanobis distance isn't useful here.")	# Also shouldn't happen
			continue

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
		best = str({best_info : data})
		#with open("error.txt", "a") as f:
		#	f.write(str(best))
		if best_info == "":
			print("There was an error with this track (BEST INFO).")	# Should never happen
			#with open("error.txt", "a") as f:
			#	f.write(str(i))
			#	f.write(str(seg))
			#	f.write("TThere was an error with this track (BEST INFO)\n")
			continue

		if best_distance == "too short" or best_distance == "not in data":
			with open("error.txt", "a") as f:
				f.write(str(i))
				f.write(str(seg))
				f.write("best distance wrong\n")
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

		data_points[best_info] = return_track

		# Save the track
		new_data = save_formant_tracks_new(corpus_context, 'formants', track_to_save, True, speaker=None)

	print()
	return data_points

def get_mean_SD_reiterate(algorithm_data):
	"""Generates means for F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class on a second pass of the algorithm.

	Parameters
	----------
	algorithm_data : dict
		Track data from which means and covariance matrices will be generated, from a first pass of the algorithm.

	Returns
	-------
	metadata : dict
		Means and covariance matrices per vowel class.
	"""
	metadata = {}

	phones = []
	for key, value in algorithm_data.items():
		phone = key[0][-1]
		if phone not in phones:
			phones.append(phone)

	for phone in phones:
		f1, f2, f3 = [], [], []
		b1, b2, b3 = [], [], []

		observation_list = []
		for key, value in algorithm_data.items():
			if key[0][-1] == phone:
				observation = [
					value['F1'],
					value['F2'],
					value['F3'],
					value['B1'],
					value['B2'],
					value['B3']
				]
				observation_list.append(observation)
				f1.append(value['F1'])
				f2.append(value['F2'])
				f3.append(value['F3'])
				b1.append(value['B1'])
				b2.append(value['B2'])
				b3.append(value['B3'])

		f1_mean, f2_mean, f3_mean = mean(f1), mean(f2), mean(f3)
		b1_mean, b2_mean, b3_mean = mean(b1), mean(b2), mean(b3)
		all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean]

		observation_list = np.array(observation_list)
		cov = np.cov(observation_list.T)
		measurements = [all_means, cov.tolist()]
		metadata[phone] = measurements

	return metadata

def extract_formants_full(corpus_context, vowel_inventory, remove_short=None, nIterations=1):
	"""Extracts F1, F2, F3 and B1, B2, B3.

	Parameters
	----------
	corpus_context : CorpusContext object
		The CorpusContext object of the corpus.
	vowel_inventory : list
		A list of vowels contained in the corpus.
	remove_short : float, optional
		Segments with length shorter than this value (in milliseconds) will not be analyzed.
	nIterations : int, optional
		How many times the algorithm should iterate before returning values.

	Returns
	-------
	prototype_data : list
		F1, F2, F3, B1, B2, B3 as measured with standard settings per vowel instance (the algorithm's first pass), used to generate prototypes.
	prototype_metadata : dict
		Means of F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.
	refined_data : dict
		The best tracks of F1, F2, F3, B1, B2, B3 per vowel instance (the algorithm's next pass(es)), as defined by Mahalanobis distance from the prototypes.
	"""
	# Step 1: Get prototypes
	print("Generating prototypes...")
	#with open("error.txt", "w+") as f:
	#	f.write("Generating prototypes:")
	prototype_data = analyze_formants_vowel_segments_new(corpus_context, vowel_inventory=vowel_inventory, remove_short=remove_short)
	prototype_metadata = get_mean_SD(corpus_context, prototype_data)

	#print("Prototype data:")
	#print(prototype_data)
	#print()
	#print("Metadata (means SDS:)")	# Debugging
	#print(prototype_metadata)

	print()
	print()
	print()

	# Step 2: Get best formants from varying nformants
	print("Varying formants to find shortest distance and best track for each token...")
	#with open("error.txt", "a") as f:
	#	f.write("Varying formants:")
	refined_data = refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory, remove_short=remove_short)
	#return prototype_data, prototype_metadata, refined_data

	# Step 3: first pass data = new prototypes, and run again
	print("Regenerating prototypes and running again...")
	counter = 1
	#remaining_iterations = nIterations-1
	while counter != nIterations:
		print("counter:", counter)
		prototype_data = refined_data
		prototype_metadata = get_mean_SD_reiterate(prototype_data)
		refined_data = refine_formants(corpus_context, prototype_data, prototype_metadata, vowel_inventory, remove_short=remove_short)
		print("increasing counter.")
		counter = counter + 1

	return prototype_data, prototype_metadata, refined_data

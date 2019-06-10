import os
import sys
from functools import partial
import csv

from statistics import mean, stdev
import numpy as np
import scipy

from conch import analyze_segments
from conch.analysis.praat import PraatAnalysisFunction
from conch.analysis.segments import SegmentMapping
from conch.analysis.formants import PraatSegmentFormantTrackFunction, FormantTrackFunction, \
    PraatSegmentFormantPointFunction

from pyraat.parse_outputs import parse_point_script_output

from ...exceptions import AcousticError

from ..io import point_measures_from_csv, point_measures_to_csv


def sanitize_bandwidths(value):
    """Cleans bandwidth data from dictionary form.

    Parameters
    ----------
    value : dict
        Observation values produced by reading out from Praat.

    Returns
    -------
    float
        The first bandwidth.
    float
        The second bandwidth.
    float
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


def track_nformants(track):
    """Gets the number of formants used to arrive at a given track.

    Parameters
    ----------
    track : dict
        The measured track.

    Returns
    -------
    int
        The number of formants used to measure that track
    """
    numbers = set(int(x[1]) for x in track.keys() if x.startswith('F'))
    return max(numbers)


def parse_multiple_formant_output(output):
    listing_list = output.split("\n\n")
    to_return = {}
    for item in listing_list:
        output = parse_point_script_output(item)
        # print (output)
        reported_nformants = output.pop('num_formants')
        # to_return[track_nformants(output)] = output
        to_return[reported_nformants] = output
    return to_return


def generate_variable_formants_point_function(corpus_context, min_formants, max_formants):
    """Generates a function used to call Praat to measure formants and bandwidths with variable num_formants.
    This specific function returns a single point per formant at a third of the way through the segment

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    min_formants : int
        The minimum number of formants to measure with on subsequent passes (default is 4).
    max_formants : int
        The maximum number of formants to measure with on subsequent passes (default is 7).

    Returns
    -------
    formant_function : Partial function object
        The function used to call Praat.
    """
    max_freq = 5500
    script_dir = os.path.dirname(os.path.abspath(__file__))

    script = os.path.join(script_dir, 'multiple_num_formants.praat')
    formant_function = PraatAnalysisFunction(script, praat_path=corpus_context.config.praat_path,
                                             arguments=[0.01, 0.025, min_formants, max_formants, max_freq])

    formant_function._function._output_parse_function = parse_multiple_formant_output
    return formant_function


def generate_variable_formants_track_function(corpus_context, n_formants):
    """Generates a function used to call Praat to measure formants and bandwidths with a single num_formants.
    This function returns the formants and bandwidths as a track, rather than a single point

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    n_formants : int
        The minimum number of formants to measure with on subsequent passes (default is 5).

    Returns
    -------
    formant_function : Partial function object
        The function used to call Praat.
    """
    max_freq = 5500
    script_dir = os.path.dirname(os.path.abspath(__file__))

    script = os.path.join(script_dir, 'formant_tracks.praat')
    formant_function = PraatAnalysisFunction(script, praat_path=corpus_context.config.praat_path,
                                             arguments=[0.01, 0.025, n_formants, max_freq])

    return formant_function


def generate_formants_point_function(corpus_context, gender=None):
    """Generates a function used to call Praat to measure formants and bandwidths with variable num_formants.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    min_formants : int
        The minimum number of formants to measure with on subsequent passes (default is 4).
    max_formants : int
        The maximum number of formants to measure with on subsequent passes (default is 7).

    Returns
    -------
    formant_function : Partial function object
        The function used to call Praat.
    """
    max_freq = 5500
    formant_function = PraatSegmentFormantPointFunction(praat_path=corpus_context.config.praat_path,
                                                        max_frequency=max_freq, num_formants=5, window_length=0.025,
                                                        time_step=0.01)
    return formant_function


def get_mean_SD(data, prototype_parameters=None):
    """Generates per-vowel-class means and covariance matrices for an arbitrary set of parameters (such as F1, F2, F3, B1, B2, B3) .

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    data : dict
        Track data from which means and covariance matrices will be generated.

    Returns
    -------
    metadata : dict
        Means and covariance matrices per vowel class.
    """
    if prototype_parameters is None:
        prototype_parameters = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    metadata = {}
    phones = set()
    for seg, value in data.items():
        phones.add(seg['label'])

    for phone in phones:

        observation_list = []
        for seg, value in data.items():
            if seg['label'] == phone:
                observation = [value[pp] for pp in prototype_parameters]
                # observation = [
                #     value['F1'],
                #     value['F2'],
                #     value['F3'],
                #     value['B1'],
                #     value['B2'],
                #     value['B3']
                # ]
                observation_list.append([x if x else 0 for x in observation])

        # f1_mean, f2_mean, f3_mean = mean(x[0] for x in observation_list), mean(x[1] for x in observation_list), mean(
        #     x[2] for x in observation_list)
        # b1_mean, b2_mean, b3_mean = mean(x[3] for x in observation_list), mean(x[4] for x in observation_list), mean(
        #     x[5] for x in observation_list)
        # all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean]
        all_means = [mean(x[i] for x in observation_list) for i, pp in enumerate(prototype_parameters)]

        observation_list = np.array(observation_list)
        cov = np.cov(observation_list.T)

        measurements = [all_means, cov.tolist()]
        metadata[phone] = measurements
    return metadata


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


def save_formant_point_data(corpus_context, data, num_formants=False):
    header = ['id', 'F1', 'F2', 'F3', 'B1', 'B2', 'B3', 'A1', 'A2', 'A3', 'Ax', 'drop_formant']
    if num_formants:
        header += ['num_formants']
    point_measures_to_csv(corpus_context, data, header)
    header_info = {}
    for h in header:
        if h == 'id':
            continue
        if h != 'num_formants' or h != 'drop_formant':
            header_info[h] = float
        # elif h != 'Fx':
        #     header_info[h] = str
        else:
            header_info[h] = int
    point_measures_from_csv(corpus_context, header_info)

def extract_and_save_formant_tracks(corpus_context, data, num_formants=False):
    #Dictionary of segment mapping objects where each n_formants has its own segment mapping object
    segment_mappings = {}
    for k, v in data.items():
        vowel_id = k.properties["id"]
        file_path = k["file_path"]
        begin = k["begin"]
        end = k["end"]
        if "num_formants" in v:
            n_formants = v["num_formants"]
        else:
            #There was not enough samples, so we use the default n
            n_formants = 5
        if not n_formants in segment_mappings:
            segment_mappings[n_formants] = SegmentMapping()
        segment_mappings[n_formants].add_file_segment(file_path, begin, end, 0, id=vowel_id, n_formants=n_formants)
    outputs = {}
    for n_formants in segment_mappings:
        func = generate_variable_formants_track_function(corpus_context, n_formants)

        output = analyze_segments(segment_mappings[n_formants], func)
        outputs.update(output)
    formant_tracks = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    for k, v in output.items():
        vowel_id = k.properties["id"]
        tracks = {x:[] for x in formant_tracks+["time"]}
        for t, formants in v.items():
            tracks["time"].append(t)
            for f in formant_tracks:
                tracks[f].append(formants[f])


def generate_base_formants_function(corpus_context, gender=None, source='praat'):
    max_freq = 5500
    if gender == 'M':
        max_freq = 5000
    if source == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        formant_function = PraatSegmentFormantTrackFunction(praat_path=corpus_context.config.praat_path,
                                                            max_frequency=max_freq, num_formants=5, window_length=0.025,
                                                            time_step=0.01)
    else:
        formant_function = FormantTrackFunction(max_frequency=max_freq,
                                                time_step=0.01, num_formants=5,
                                                window_length=0.025)
    return formant_function

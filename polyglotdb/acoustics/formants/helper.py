import os
import sys
from functools import partial
import csv

from statistics import mean, stdev
import numpy as np
import scipy

from acousticsim.analysis.praat import run_script, read_praat_out
from acousticsim.analysis.helper import ASTemporaryWavFile
from acousticsim.analysis.formants import (signal_to_formants as ASFormants_signal, file_to_formants as ASFormants_file,
                                           signal_to_formants_praat as PraatFormants_signal,
                                           file_to_formants_praat as PraatFormants_file)

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


def signal_to_formants_point_praat(signal, sr, praat_path=None, num_formants=5,
                                   max_freq=5000,
                                   time_step=0.01, win_len=0.025,
                                   begin=None, padding=None):
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

    Returns
    -------
    dict
        Output from call to Praat
    """
    with ASTemporaryWavFile(signal, sr) as wav_path:
        output = file_to_formants_point_praat(wav_path, praat_path, num_formants, max_freq,
                                              time_step, win_len, padding)
        return_value = list(output.values())[0]

        return return_value


def file_to_formants_point_praat(file_path, praat_path=None, num_formants=5,
                                 max_freq=5000,
                                 time_step=0.01, win_len=0.025, padding=None):
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

    Returns
    -------
    dict
        Output from call to Praat.
    """
    if praat_path is None:
        praat_path = 'praat'
        if sys.platform == 'win32':
            praat_path += 'con.exe'

    script_dir = os.path.dirname(os.path.abspath(__file__))

    script = os.path.join(script_dir, 'formants_bandwidth.praat')
    listing = run_script(praat_path, script, file_path, time_step,
                         win_len, num_formants, max_freq, padding)
    output = read_praat_out(listing)
    return output


def signal_to_multiple_formants_point_praat(signal, sr, praat_path=None, min_formants=4, max_formants=7,
                                            max_freq=5000,
                                            time_step=0.01, win_len=0.025,
                                            begin=None, padding=None):
    """Wrapper to call Praat and fix the time points before returning.

    Parameters
    ----------
    signal : boolean
        Contains signal information.
    sr : float
        Contains sample rate information.
    praat_path : string
        Contains information about the Praat path if specialized.
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

    Returns
    -------
    dict
        Output from call to Praat
    """
    with ASTemporaryWavFile(signal, sr) as wav_path:
        output = file_to_multiple_formants_point_praat(wav_path, praat_path, min_formants, max_formants,
                                                       max_freq,
                                                       time_step, win_len, padding)
        to_return = {}
        for item in output:
            item = list(item.values())[0]

            to_return[track_nformants(item)] = item
    return to_return


def segment_to_multiple_formants_point_praat(file_path, begin, end, channel, praat_path=None, min_formants=4, max_formants=7,
                                            max_freq=5000,
                                            time_step=0.01, win_len=0.025,
                                            padding=None):
    """Wrapper to call Praat and fix the time points before returning.

    Parameters
    ----------
    signal : boolean
        Contains signal information.
    sr : float
        Contains sample rate information.
    praat_path : string
        Contains information about the Praat path if specialized.
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

    Returns
    -------
    dict
        Output from call to Praat
    """
    if praat_path is None:
        praat_path = 'praat'
        if sys.platform == 'win32':
            praat_path += 'con.exe'

    script_dir = os.path.dirname(os.path.abspath(__file__))

    script = os.path.join(script_dir, 'multiple_formants_bandwidth_segment.praat')
    listing = run_script(praat_path, script, file_path, begin, end, channel, time_step,
                         win_len, min_formants, max_formants, max_freq, padding)

    listing_list = listing.split("\n\n")
    output_list = []
    to_return = {}
    for item in listing_list:
        output = read_praat_out(item)
        item = list(output.values())[0]

        to_return[track_nformants(item)] = item
    return to_return

def file_to_multiple_formants_point_praat(file_path, praat_path=None, min_formants=4, max_formants=7,
                                          max_freq=5000,
                                          time_step=0.01, win_len=0.025, padding=None):
    """Wrapper to call Praat to measure formants and bandwidths.

    Parameters
    ----------
    signal : boolean
        Contains signal information.
    sr : float
        Contains sample rate information.
    praat_path : string
        Contains information about the Praat path if specialized.
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

    Returns
    -------
    list
        Output from a multiple-measures call to Praat.
    """
    if praat_path is None:
        praat_path = 'praat'
        if sys.platform == 'win32':
            praat_path += 'con.exe'

    script_dir = os.path.dirname(os.path.abspath(__file__))

    script = os.path.join(script_dir, 'multiple_formants_bandwidth.praat')
    listing = run_script(praat_path, script, file_path, time_step,
                         win_len, min_formants, max_formants, max_freq, padding)

    listing_list = listing.split("\n\n")
    output_list = []
    for item in listing_list:
        output = read_praat_out(item)
        output_list.append(output)
    return output_list


def generate_base_formants_point_function(corpus_context, signal=False, gender=None):
    """Generates a function used to call Praat to measure formants and bandwidths with fixed num_formants.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
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
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        if signal:
            PraatFormants = signal_to_formants_point_praat
        else:
            PraatFormants = file_to_formants_point_praat
        formant_function = partial(PraatFormants,
                                   praat_path=corpus_context.config.praat_path,
                                   max_freq=max_freq, num_formants=5, win_len=0.025,
                                   time_step=0.01)
    return formant_function


def generate_variable_formants_point_function(corpus_context, min_formants, max_formants, signal=False, gender=None):
    """Generates a function used to call Praat to measure formants and bandwidths with variable num_formants.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    min_formants : int
        The minimum number of formants to measure with on subsequent passes (default is 4).
    max_formants : int
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
            PraatFormants = segment_to_multiple_formants_point_praat
        else:
            PraatFormants = file_to_multiple_formants_point_praat
        formant_function = partial(PraatFormants,
                                   praat_path=corpus_context.config.praat_path,
                                   max_freq=max_freq, min_formants=min_formants, max_formants=max_formants, win_len=0.025,
                                   time_step=0.01, padding=0.1)
    return formant_function


def get_mean_SD(data):
    """Generates means for F1, F2, F3, B1, B2, B3 and covariance matrices per vowel class.

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
    metadata = {}
    phones = set()
    for seg, value in data.items():
        phones.add(seg['label'])

    for phone in phones:

        observation_list = []
        for seg, value in data.items():
            if seg['label'] == phone:
                observation = [
                    value['F1'],
                    value['F2'],
                    value['F3'],
                    value['B1'],
                    value['B2'],
                    value['B3']
                ]
                observation_list.append(observation)

        f1_mean, f2_mean, f3_mean = mean(x[0] for x in observation_list), mean(x[1] for x in observation_list), mean(
            x[2] for x in observation_list)
        b1_mean, b2_mean, b3_mean = mean(x[3] for x in observation_list), mean(x[4] for x in observation_list), mean(
            x[5] for x in observation_list)
        all_means = [f1_mean, f2_mean, f3_mean, b1_mean, b2_mean, b3_mean]

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


def save_formant_point_data(corpus_context, data, num_formants = False):
    header = ['id', 'F1', 'F2', 'F3', 'B1', 'B2', 'B3']
    if num_formants:
        header += ['num_formants']
    point_measures_to_csv(corpus_context, data, header)
    header_info = {}
    for h in header:
        if h == 'id':
            continue
        if h != 'num_formants':
            header_info[h] = float
        else:
            header_info[h] = int
    point_measures_from_csv(corpus_context, header_info)



def generate_base_formants_function(corpus_context, signal=False, gender=None):
    algorithm = corpus_context.config.formant_source
    max_freq = 5500
    if gender == 'M':
        max_freq = 5000
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        if signal:
            PraatFormants = PraatFormants_signal
        else:
            PraatFormants = PraatFormants_file
        formant_function = partial(PraatFormants,
                                   praat_path=corpus_context.config.praat_path,
                                   max_freq=max_freq, num_formants=5, win_len=0.025,
                                   time_step=0.01)
    else:
        if signal:
            ASFormants = ASFormants_signal
        else:
            ASFormants = ASFormants_file
        formant_function = partial(ASFormants, max_freq=max_freq,
                                   time_step=0.01, num_formants=5,
                                   win_len=0.025)
    return formant_function

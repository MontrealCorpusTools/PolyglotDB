import time
import logging

import os
import math
import csv

from functools import partial

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


def signal_to_formants_praat_new(signal, sr, praat_path=None, num_formants=5, min_formants=4, max_formants=7,
                                 max_freq=5000,
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
    # print("SR:", sr)
    with ASTemporaryWavFile(signal, sr) as wav_path:
        output = file_to_formants_praat_new(wav_path, praat_path, num_formants, min_formants, max_formants, max_freq,
                                            time_step, win_len, padding, multiple_measures)
        duration = signal.shape[0] / sr
        if not multiple_measures:
            return_value = fix_time_points(output, begin, padding, duration)
            for key, val in return_value.items():
                if all(value == 0 for value in val.values()):
                    print("Praat is measuring all values to be 0.")  # Should not occur, debugging
                break
            return list(fix_time_points(output, begin, padding, duration).values())[0]
        else:
            to_return = {}
            for item in output:
                to_append = fix_time_points(item, begin, padding, duration)
                to_return = {track_nformants(to_append): list(to_append.values())[0]}
                if not to_return:
                    continue
                return to_return
            return to_return


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


def file_to_formants_praat_new(file_path, praat_path=None, num_formants=5, min_formants=4, max_formants=7,
                               max_freq=5000,
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

    if not multiple_measures:
        script = os.path.join(script_dir, 'formants_bandwidth.praat')
        listing = run_script(praat_path, script, file_path, time_step,
                             win_len, num_formants, max_freq, padding)
        output = read_praat_out(listing)
        # print("OUTPUT:", output)
        return output
    else:
        script = os.path.join(script_dir, 'multiple_formants_bandwidth.praat')
        listing = run_script(praat_path, script, file_path, time_step,
                             win_len, min_formants, max_formants, max_freq, padding)

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
    # if gender == 'M':
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


def analyze_formants_initial_pass(corpus_context, call_back=None, stop_check=None, vowel_inventory=None,
                                        duration_threshold=None):
    """First pass of the algorithm; generates prototypes.

    Parameters
    ----------
    corpus_context : CorpusContext object
        The CorpusContext object of the corpus.
    call_back : callable
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

    segment_mapping = generate_vowel_segments(corpus_context, call_back=call_back,
                                              duration_threshold=duration_threshold)

    # Debugging
    # segment_mapping = segment_mapping[:300]

    if call_back is not None:
        call_back('Analyzing files...')

    # Go through each segment
    data = []
    vowel = ""
    formant_function = generate_base_formants_function_new(corpus_context, signal=True)  # Make formant function
    output = analyze_file_segments(segment_mapping, formant_function, padding=.25,
                                   stop_check=stop_check)  # Analyze the phone
    return output


def get_mean_SD(data):
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


class Segment(object):
    def __init__(self, **kwargs):
        self.properties = kwargs

    def __repr__(self):
        return '<Segment object with properties: {}>'.format(str(self))

    def __str__(self):
        return str(self.properties)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.properties[item]
        elif isinstance(item, slice):
            if item.start is None:
                start = 0
            else:
                start = item.start
            if item.stop is None:
                stop = -1
            else:
                stop = item.stop
            if item.step is None:
                step = 1
            else:
                step = item.step
            return [self[i] for i in range(start, stop, step)]
        if item == 0:
            return self.properties['file_path']
        elif item == 1:
            return self.properties['begin']
        elif item == 2:
            return self.properties['end']
        elif item == 3:
            return self.properties['channel']

    def __hash__(self):
        return hash((self[0], self[1], self[2], self[3]))

    def __eq__(self, other):
        if self[0] != other[0]:
            return False
        if self[1] != other[1]:
            return False
        if self[2] != other[2]:
            return False
        if self[3] != other[3]:
            return False
        return True

    def __lt__(self, other):
        if self[0] < other[0]:
            return True
        elif self[0] == other[0]:
            if self[1] < other[1]:
                return True
            elif self[1] == other[1]:
                if self[2] < other[2]:
                    return True
        return False


class SegmentMapping(object):
    def __init__(self):
        self.segments = []

    def add_segment(self, **kwargs):
        self.segments.append(Segment(**kwargs))

    def levels(self, property_key):
        return set(x[property_key] for x in self.segments)

    def grouped_mapping(self, property_key):
        data = {x: [] for x in self.levels(property_key)}
        for s in self.segments:
            data[s[property_key]].append(s)
        return data

    def __iter__(self):
        for s in self.segments:
            yield s


def generate_vowel_segments(corpus_context, call_back=None, duration_threshold=None):
    """
    Generate segment vectors for each phone, to be used as input to analyze_file_segments.

    Arguments:
    -- corpus_context: corpus context to use
    -- phone_class: the phone class to generate segments for
    (optional:) call_back: call back function

    Returns:
    -- a mapping from speaker to a list of phone vectors belonging to that speaker,
    -- a mapping from discourse name to the sound file path for that discourse,
    -- a mapping from the phone vector to the phone id
    """
    if not corpus_context.hierarchy.has_type_subset('phone', 'vowel'):
        raise Exception()
    speakers = corpus_context.speakers
    segment_mapping = SegmentMapping()
    for s in speakers:
        time_sp = time.time()
        segments = []
        speaker_has_phone = False
        statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                    WHERE s.name = {{speaker_name}}
                    RETURN d, r'''.format(corpus_name=corpus_context.cypher_safe_name)
        results = corpus_context.execute_cypher(statement, speaker_name=s)

        for r in results:
            channel = r['r']['channel']
            discourse = r['d']['name']
            vowel_file_path = r['d']['vowel_file_path']
            qr = corpus_context.query_graph(corpus_context.phone).filter(
                corpus_context.phone.subset == 'vowel')
            qr = qr.filter(corpus_context.phone.discourse.name == discourse)
            qr = qr.filter(corpus_context.phone.speaker.name == s)
            if qr.count() == 0:
                continue
            phones = qr.all()
            if phones is not None:
                for ph in phones:
                    if duration_threshold is not None and ph.end - ph.begin < duration_threshold:
                        continue
                    segment_mapping.add_segment(file_path=vowel_file_path, begin=ph.begin, end=ph.end, label=ph.label,
                                                id=ph.id, discourse=discourse, channel=channel, speaker=s)
        print("time for current speaker: " + str(time.time() - time_sp))
    return segment_mapping


def refine_formants(corpus_context, prototype_metadata, vowel_inventory, call_back=None,
                    stop_check=None, duration_threshold=None):
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
    segment_mapping = generate_vowel_segments(corpus_context, call_back=call_back,
                                              duration_threshold=duration_threshold)

    # Debugging
    # segment_mapping = segment_mapping[:300]

    if call_back is not None:
        call_back('Analyzing files...')

    best_data = {}
    columns = ['F1', 'F2', 'F3', 'B1', 'B2', 'B3']

    # For each vowel token, collect the formant measurements
    # Pick the best track that is closest to the averages gotten from prototypes
    for i, (vowel, seg) in enumerate(segment_mapping.grouped_mapping('label').items()):

        if len(seg) < 6:
            print("Not enough observations of vowel {}, at least 6 are needed, only found {}.".format(vowel, len(seg)))
            best_distance = "too short"
            continue

        # Make sure the vowel in question is in the data, otherwise it's a pointless iteration
        if vowel in prototype_metadata:
            prototype_means = prototype_metadata[vowel][0]
        else:
            print("Continuing. Vowel for this segment, while in inventory, is not in the data.")
            best_distance = "not in data"
            continue

        # Measure with varying levels of formants
        min_formants = 4  # Off by one error, due to how Praat measures it from F0
        # This really measures with 3 formants: F1, F2, F3. And so on.
        max_formants = 7

        formant_function = generate_variable_formants_function_new(corpus_context, min_formants, max_formants,
                                                                   signal=True)  # Make formant function (VARIABLE)
        output = analyze_file_segments(seg, formant_function, padding=0.25,
                                       stop_check=stop_check)  # Analyze the phone

        # Get Mahalanobis distance between every new observation and the sample/means
        covariance = np.array(prototype_metadata[vowel][1])
        try:
            inverse_covariance = np.linalg.pinv(covariance)
        except:
            print(
                "There's only one observation of this phone, so Mahalanobis distance isn't useful here.")  # Also shouldn't happen
            continue

        for seg, data in output.items():

            best_distance = math.inf
            best_track = 0
            for number, point in data.items():
                point = [point[x] for x in columns]
                distance = get_mahalanobis(prototype_means, point, inverse_covariance)
                if distance < best_distance:  # Update "best" measures when new best distance is found
                    best_distance = distance
                    best_track = point
                    best_number = number

            best_data[seg] = {k:best_track[i] for i, k in enumerate(columns)}
    return best_data


def save_refined_formant_data(corpus_context, refined_data):
    from ..io.importer.from_csv import make_path_safe
    header = ['id', 'F1','F2','F3','B1','B2','B3']
    for s in corpus_context.speakers:
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_formants.csv'.format(s))
        with open(path, 'w', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, header, delimiter=',')
            writer.writeheader()
    for seg, best_track in refined_data.items():
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_formants.csv'.format(seg['speaker']))
        with open(path, 'a', newline='', encoding='utf8') as f:
            writer = csv.DictWriter(f, header, delimiter=',')
            row = dict(id=seg['id'], **best_track)
            writer.writerow(row)
    float_set_template = 'n.{name} = toFloat(csvLine.{name})'
    properties = []
    for h in header:
        if h == 'id':
            continue
        properties.append(float_set_template.format(name=h))
    properties = ',\n'.join(properties)

    for s in corpus_context.speakers:
        path = os.path.join(corpus_context.config.temporary_directory('csv'),
                            '{}_formants.csv'.format(s))
        import_path = 'file:///{}'.format(make_path_safe(path))
        import_statement = '''CYPHER planner=rule
            USING PERIODIC COMMIT 2000
            LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
            MATCH (n:{phone_type}:{corpus_name}) where n.id = csvLine.id
            SET {new_properties}'''

        statement = import_statement.format(path=import_path,
                                            corpus_name=corpus_context.cypher_safe_name,
                                            phone_type=corpus_context.phone_name,
                                            new_properties=properties)
        corpus_context.execute_cypher(statement)
    for h in header:
        if h == 'id':
            continue
        corpus_context.execute_cypher('CREATE INDEX ON :%s(%s)' % (corpus_context.phone_name, h))
    corpus_context.hierarchy.add_token_properties(corpus_context, corpus_context.phone_name, [(h, float) for h in header if h != 'id'])

def analyze_formants_refinement(corpus_context, vowel_inventory, duration_threshold=0, num_iterations=1):
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
    # with open("error.txt", "w+") as f:
    #	f.write("Generating prototypes:")
    prototype_data = analyze_formants_initial_pass(corpus_context, vowel_inventory=vowel_inventory,
                                                         duration_threshold=duration_threshold)
    prev_prototype_metadata = get_mean_SD(prototype_data)

    # Step 3: first pass data = new prototypes, and run again
    print("Regenerating prototypes and running again...")
    if num_iterations < 1:
        raise NotImplementedError
    for i in range(num_iterations):
        print("iteration:", i)
        refined_data = refine_formants(corpus_context, prev_prototype_metadata, vowel_inventory,
                                       duration_threshold=duration_threshold)
        prototype_data = refined_data
        prototype_metadata = get_mean_SD(refined_data)
        prev_prototype_metadata = prototype_metadata

    save_refined_formant_data(corpus_context, refined_data)
    return prototype_metadata

import time
import logging

import os
import math
import csv

from functools import partial

from ..exceptions import GraphQueryError, AcousticError, SpeakerAttributeError

from acousticsim.analysis.pitch import (signal_to_pitch as ASPitch_signal, file_to_pitch as ASPitch_file,
                                        signal_to_pitch_praat as PraatPitch_signal,
                                        file_to_pitch_praat as PraatPitch_file,
                                        signal_to_pitch_reaper as ReaperPitch_signal,
                                        file_to_pitch_reaper as ReaperPitch_file,
                                        signal_to_pitch_and_pulse_reaper as ReaperPitch_signal_pulse,
                                        file_to_pitch_and_pulse_reaper as ReaperPitch_file_pulse,
                                        )
from acousticsim.analysis.formants import (signal_to_formants as ASFormants_signal, file_to_formants as ASFormants_file,
                                           signal_to_formants_praat as PraatFormants_signal,
                                           file_to_formants_praat as PraatFormants_file)
from acousticsim.analysis.intensity import signal_to_intensity_praat as PraatIntensity_signal, \
    file_to_intensity_praat as PraatIntensity_file

from acousticsim.main import analyze_long_file, analyze_file_segments
from acousticsim.multiprocessing import generate_cache, default_njobs
from acousticsim.analysis.praat import run_script, read_praat_out
from acousticsim.analysis.helper import ASTemporaryWavFile, fix_time_points

import sys
import io
from contextlib import redirect_stdout

PADDING = 0.1


def analyze_discourse_pitch(corpus_context, discourse, pitch_source='praat', min_pitch=50, max_pitch=500, **kwargs):
    print(kwargs)
    segment_mapping = {}
    discourse_mapping = {}
    segments = []
    statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                WHERE d.name = {{discourse_name}}
                RETURN d, s, r'''.format(corpus_name=corpus_context.cypher_safe_name)
    results = corpus_context.execute_cypher(statement, discourse_name=discourse)

    for r in results:
        channel = r['r']['channel']
        speaker = r['s']['name']

        discourse = r['d']['name']
        file_path = r['d']['vowel_file_path']
        atype = corpus_context.hierarchy.highest
        prob_utt = getattr(corpus_context, atype)
        q = corpus_context.query_graph(prob_utt)
        q = q.filter(prob_utt.discourse.name == discourse)
        q = q.filter(prob_utt.speaker.name == speaker)
        utterances = q.all()
        for u in utterances:
            segments.append((file_path, u.begin, u.end, channel))

    path = None
    if pitch_source == 'praat':
        path = corpus_context.config.praat_path
        # kwargs = {'silence_threshold': 0.03,
        #          'voicing_threshold': 0.45, 'octave_cost': 0.01, 'octave_jump_cost': 0.35,
        #          'voiced_unvoiced_cost': 0.14}
    elif pitch_source == 'reaper':
        path = corpus_context.config.reaper_path
    pitch_function = generate_pitch_function(pitch_source, min_pitch, max_pitch, signal=True, path=path, pulses=True)
    print(pitch_function)
    track = {}
    pulses = set()
    output = analyze_file_segments(segments, pitch_function, padding=PADDING)
    print(output)
    for v in output.values():
        track.update(v[0])
        pulses.update(v[1])
    return track, sorted(pulses)


def generate_phone_segments_by_speaker(corpus_context, phone_class, call_back=None):
    """
    Generate segment vectors for each phone, to be used as input to analyze_file_segments.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    phone_class : string
        the phone class to generate segments for
    call_back : function
        call back function, optional

    Returns
    ----------
    segment_mapping : dict
        a mapping from speaker to a list of phone vectors belonging to that speaker 
    discourse_mapping : dict
        a mapping from discourse name to the sound file path for that discourse
    phone_ids : dict
        a mapping from the phone vector to the phone id
    """
    speakers = corpus_context.speakers
    segment_mapping = {}
    discourse_mapping = {}
    phone_ids = {}
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
            consonant_file_path = r['d']['consonant_file_path']
            # qr = corpus_context.query_graph(corpus_context.phone).filter(corpus_context.phone.id.in_(query))
            qr = corpus_context.query_graph(corpus_context.phone).filter(
                corpus_context.phone.subset == phone_class)
            qr = qr.filter(corpus_context.phone.discourse.name == discourse)
            qr = qr.filter(corpus_context.phone.speaker.name == s)
            if qr.count() == 0:
                continue
            phones = qr.all()
            speaker_has_phone = True
            if phones is not None:
                for ph in phones:
                    if 'vowel' in phone_class:
                        phone_ids[(vowel_file_path, ph.begin, ph.end, channel, ph.label)] = ph.id
                        segments.append((vowel_file_path, ph.begin, ph.end, channel, ph.label))
                    else:
                        phone_ids[(consonant_file_path, ph.begin, ph.end, channel, ph.label)] = ph.id
                        segments.append((consonant_file_path, ph.begin, ph.end, channel, ph.label))
            if phone_class is 'vowel':
                discourse_mapping[discourse] = vowel_file_path
            else:
                discourse_mapping[discourse] = consonant_file_path
        if speaker_has_phone:
            segment_mapping[s] = segments
        print("time for current speaker: " + str(time.time() - time_sp))
    return segment_mapping, discourse_mapping, phone_ids


def generate_speaker_segments(corpus_context):
    speakers = corpus_context.speakers
    segment_mapping = {}
    discourse_mapping = {}
    for s in speakers:
        segments = []
        statement = '''MATCH (s:Speaker:{corpus_name})-[r:speaks_in]->(d:Discourse:{corpus_name})
                    WHERE s.name = {{speaker_name}}
                    RETURN d, r'''.format(corpus_name=corpus_context.cypher_safe_name)
        results = corpus_context.execute_cypher(statement, speaker_name=s)

        for r in results:
            channel = r['r']['channel']
            discourse = r['d']['name']
            file_path = r['d']['vowel_file_path']
            atype = corpus_context.hierarchy.highest
            prob_utt = getattr(corpus_context, atype)
            q = corpus_context.query_graph(prob_utt)
            q = q.filter(prob_utt.discourse.name == discourse)
            q = q.filter(prob_utt.speaker.name == s)
            utterances = q.all()
            for u in utterances:
                segments.append((file_path, u.begin, u.end, channel))
            discourse_mapping[file_path] = discourse
        segment_mapping[s] = segments
    print(segment_mapping)
    return segment_mapping, discourse_mapping


def analyze_pitch(corpus_context,
                  call_back=None,
                  stop_check=None):
    absolute_min_pitch = 55
    absolute_max_pitch = 480
    if not 'utterance' in corpus_context.hierarchy:
        raise (Exception('Must encode utterances before pitch can be analyzed'))
    segment_mapping, discourse_mapping = generate_speaker_segments(corpus_context)
    num_speakers = len(segment_mapping)
    algorithm = corpus_context.config.pitch_algorithm
    path = None
    if corpus_context.config.pitch_source == 'praat':
        path = corpus_context.config.praat_path
        # kwargs = {'silence_threshold': 0.03,
        #          'voicing_threshold': 0.45, 'octave_cost': 0.01, 'octave_jump_cost': 0.35,
        #          'voiced_unvoiced_cost': 0.14}
    elif corpus_context.config.pitch_source == 'reaper':
        path = corpus_context.config.reaper_path
        # kwargs = None
    pitch_function = generate_pitch_function(corpus_context.config.pitch_source, absolute_min_pitch, absolute_max_pitch,
                                             signal=True, path=path)
    if algorithm == 'speaker_adjusted':
        speaker_data = {}
        if call_back is not None:
            call_back('Getting original speaker means and SDs...')
        for i, (k, v) in enumerate(segment_mapping.items()):
            if call_back is not None:
                call_back('Analyzing speaker {} ({} of {})'.format(k, i, num_speakers))
            output = analyze_file_segments(v, pitch_function, padding=PADDING, stop_check=stop_check)

            sum_pitch = 0
            sum_square_pitch = 0
            n = 0
            for seg, track in output.items():
                for t, v in track.items():
                    v = v['F0']
                    if v > 0:  # only voiced frames

                        n += 1
                        sum_pitch += v
                        sum_square_pitch += v * v
            speaker_data[k] = [sum_pitch / n, math.sqrt((n * sum_square_pitch - sum_pitch * sum_pitch) / (n * (n - 1)))]
        print(speaker_data)

    for i, (speaker, v) in enumerate(segment_mapping.items()):
        if call_back is not None:
            call_back('Analyzing speaker {} ({} of {})'.format(speaker, i, num_speakers))
        if algorithm == 'gendered':
            min_pitch = absolute_min_pitch
            max_pitch = absolute_max_pitch
            try:
                q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
                q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
                gender = q.all()[0]['Gender']
                if gender is not None:
                    if gender.lower()[0] == 'f':
                        min_pitch = 100
                    else:
                        max_pitch = 400
            except SpeakerAttributeError:
                pass
            pitch_function = generate_pitch_function(corpus_context.config.pitch_source, min_pitch, max_pitch,
                                                     signal=True, path=path)
        elif algorithm == 'speaker_adjusted':
            mean_pitch, sd_pitch = speaker_data[speaker]
            min_pitch = int(mean_pitch - 3 * sd_pitch)
            max_pitch = int(mean_pitch + 3 * sd_pitch)
            if min_pitch < absolute_min_pitch:
                min_pitch = absolute_min_pitch
            if max_pitch > absolute_max_pitch:
                max_pitch = absolute_max_pitch
            pitch_function = generate_pitch_function(corpus_context.config.pitch_source, min_pitch, max_pitch,
                                                     signal=True, path=path)
        output = analyze_file_segments(v, pitch_function, padding=PADDING, stop_check=stop_check)
        corpus_context.save_pitch_tracks(output, speaker)

def analyze_formants(corpus_context,
                     call_back=None,
                     stop_check=None):
    """
    Analyze formants of an entire utterance, and save the resulting formant tracks into the database.
    
    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    call_back : function
        call back function, optional
    stop_check : function
        stop check function, optional
    """
    segment_mapping, discourse_mapping = generate_speaker_segments(corpus_context)
    if call_back is not None:
        call_back('Analyzing files...')
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            formant_function = generate_base_formants_function(corpus_context, signal=True, gender=gender)
        else:
            formant_function = generate_base_formants_function(corpus_context, signal=True)
        output = analyze_file_segments(v, formant_function, padding=PADDING, stop_check=stop_check)
        corpus_context.save_formant_tracks(output, speaker)


def analyze_formants_vowel_segments(corpus_context,
                                    call_back=None,
                                    stop_check=None,
                                    vowel_inventory=None):
    """
    Analyze formants of individual vowels, and save the resulting formant tracks into the database for each phone.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    call_back : function
        call back function, optional
    stop_check : function
        stop check function, optional
    vowel_inventory : list of strings
        list of vowels used to encode a class 'vowel', optional. 
        if not used, it's assumed that 'vowel' is already a phone class
    """
    # encodes vowel inventory into a phone class if it's specified
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')
    # gets segment mapping of phones that are vowels
    segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel',
                                                                                       call_back=call_back)

    if call_back is not None:
        call_back('Analyzing files...')
    # goes through each phone and: makes a formant function, analyzes the phone, and saves the tracks
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            formant_function = generate_base_formants_function(corpus_context, signal=True, gender=gender)
        else:
            formant_function = generate_base_formants_function(corpus_context, signal=True)
        output = analyze_file_segments(v, formant_function, padding=None, stop_check=stop_check)
        corpus_context.save_formant_tracks(output, speaker)


def analyze_intensity(corpus_context,
                     call_back=None,
                     stop_check=None):
    """
    Analyze intensity of an entire utterance, and save the resulting intensity tracks into the database.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    call_back : function
        call back function, optional
    stop_check : function
        stop check function, optional
    """
    segment_mapping, discourse_mapping = generate_speaker_segments(corpus_context)
    if call_back is not None:
        call_back('Analyzing files...')
    #formant_function = generate_base_formants_function(corpus_context, signal=False, gender=g))
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            intensity_function = generate_base_intensity_function(corpus_context, signal=True, gender=gender)
        else:
            intensity_function = generate_base_intensity_function(corpus_context, signal=True)
        output = analyze_file_segments(v, intensity_function, padding=PADDING, stop_check=stop_check)
        corpus_context.save_intensity_tracks(output, speaker)


def make_path_safe(path):
    return path.replace('\\', '/').replace(' ', '%20')

def analyze_script(corpus_context,
                   phone_class,
                   script_path,
                   arguments=None,
                   call_back=None,
                   stop_check=None):
    """
    Perform acoustic analysis of phones using an input praat script.
    
    Saves the measurement results from the praat script into the database under the same names as the Praat output columns
    Praat script requirements: 
        -the only input is the full path to the soundfile containing (only) the phone
        -the script prints the output to the Praat Info window in two rows (i.e. two lines).
            -the first row is a space-separated list of measurement names: these are the names that will be saved into the database
            -the second row is a space-separated list of the value for each measurement
    
    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    phone_class : string
        the name of an already encoded phone class, on which the analysis will be run
    script_path : string
        full path to the praat script
    arguments : list
        a list containing any arguments to the praat script (currently not working)
    call_back : function
        call back function, optional
    stop_check : function
        stop check function, optional
    """
    print("analyzing sibilants")
    if call_back is not None:
        call_back('Analyzing phones...')
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import.csv'
    needs_header = True
    output_types = {}
    header = ['id', 'begin', 'end']
    time_section = time.time()
    segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, phone_class,
                                                                                       call_back=call_back)
    print("generate segments took: " + str(time.time() - time_section))
    if call_back is not None:
        call_back("generate segments took: " + str(time.time() - time_section))
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, arguments=arguments)
    with open(os.path.join(directory, csv_name), 'w', newline='') as f:
        for i, (speaker, v) in enumerate(segment_mapping.items()):
            if stop_check is not None and stop_check():
                break
            if call_back is not None:
                # call_back('Analyzing file {} of {} ({})...'.format(i, num_sound_files, sf.file_path))
                call_back(i)
            time_section = time.time()
            output = analyze_file_segments(v, script_function, padding=None, stop_check=stop_check)
            if call_back is not None:
                call_back("time analyzing segments: " + str(time.time() - time_section))
            print("time analyzing segments: " + str(time.time() - time_section))

            for vector in output.keys():
                output_dict = output[vector]
                if needs_header is True:
                    for measurement in output_dict:
                        header.append(measurement)
                    writer = csv.DictWriter(f, header, delimiter=',')
                    writer.writeheader()
                    needs_header = False
                filepath, begin, end, channel = vector[:4]
                row = {}
                row['id'] = phone_ids[vector]
                row['begin'] = begin
                row['end'] = end
                for measurement in output_dict:
                    if measurement in header:
                        row[measurement] = output_dict[measurement]
                        if measurement not in output_types:
                            output_types[measurement] = type(output_dict[measurement]).__name__
                writer.writerow(row)
    for measurement in output_types:
        script_data_from_csv(corpus_context, measurement, output_types[measurement])

def script_data_from_csv(corpus_context, result_measurement, output_type):
    """
    Save acoustic data from one column of a csv file into the database.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context
    result_measurement : string
        measurement label (label of the column)
    output_type : string 
        type of the measurement being saved
    """
    if output_type == 'int':
        cypher_set_template = 'n.{name} = toInt(csvLine.{name})'
    elif output_type == 'bool':
        cypher_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    elif output_type == 'float':
        cypher_set_template = 'n.{name} = toFloat(csvLine.{name})'
    else:
        cypher_set_template = 'n.{name} = csvLine.{name}'
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import.csv'
    path = os.path.join(directory, csv_name)
    feat_path = 'file:///{}'.format(make_path_safe(path))
    import_statement = '''CYPHER planner=rule
        LOAD CSV WITH HEADERS FROM "{path}" AS csvLine
        MATCH (n:phone:{corpus_name}) where n.id = csvLine.id
        SET {new_property}'''
    statement = import_statement.format(path=feat_path,
                                        corpus_name=corpus_context.cypher_safe_name,
                                        new_property=cypher_set_template.format(name=result_measurement))
    corpus_context.execute_cypher(statement)
    corpus_context.execute_cypher('CREATE INDEX ON :Phone(%s)' % result_measurement)
    types = {result_measurement: output_type}
    corpus_context.hierarchy.add_token_properties(corpus_context, 'phone', types.items())
    corpus_context.refresh_hierarchy()


def signal_to_praat_script(signal, sr, praat_path=None, time_step=0.01,
                           begin=None, padding=None, script_path=None, arguments=None):
    """
    Create a sound file for one phone from a signal and sample rate, and run the praat script on that phone.
    
    Parameters
    ----------
    signal
        input from acousticsim multiprocessing, used to get phone wavfile
    sr
        sampling rate. input from acousticsim multiprocessing, used to get phone wavfile
    praat_path : string
        full path to praat
    time_step
        parameter that is used by acousticsim, is input by acousticsim (not the user)
    begin
        parameter that is used by acousticsim, is input by acousticsim (not the user)
    padding : int
        time padding around segment: must be None or 0 for phone analysis to work!
    script_path : string
        path to the praat script to be run
    arguments : list
        a list containing any arguments to the praat script, optional (currently not implemented)
    
    Returns
    ----------
    script_output : dict
        dictionary of measurement : value, based on the columns output by the Praat script
    """
    with ASTemporaryWavFile(signal, sr) as wav_path:
        if praat_path is None:
            praat_path = 'praat'
            if sys.platform == 'win32':
                praat_path += 'con.exe'
        script_output = run_script(praat_path, script_path, wav_path)
        script_output = parse_script_output(script_output)
        return script_output

def generate_praat_script_function(praat_path, script_path, arguments=None):
    """
    Generate a partial function that calls the praat script specified.
    (used as input to analyze_file_segments)
    
    Parameters
    ----------
    praat_path : string
        full path to praat/praatcon
    script_path: string
        full path to the script
    arguments : list
        a list containing any arguments to the praat script, optional (currently not implemented)
    
    Returns
    ----------
    praat_function : partial 
        the partial function which applies the Praat script to a phone and returns the script output
    """
    praat_function = partial(signal_to_praat_script,
                             praat_path=praat_path,
                             script_path=script_path, arguments=arguments)
    return praat_function

def parse_script_output(script_output):
    """
    Parse the output from Praat into a dictionary of acoustic measurements. 
    See docstring of analyze_script for formatting requirements.
    Prints the Praat script output if it doesn't fit the specified format (usually because the Praat script crashed), and returns None in that case

    Parameters
    ----------
    script_output : string
        output from Praat. (This is what appears in the Info window when using the Praat GUI)

    Returns
    ----------
    output : dict
        dictionary of measurement : value, based on the columns output by the Praat script
    """
    headers = []
    output = {}
    unexpectedInput = False
    for line in script_output.split('\n'):
        if line.strip() is not "" and line.strip() is not "." and "Warning" not in line and "warning" not in line:
            values = line.strip().split(" ")
            if headers == []:
                headers = values
            else:
                for (measurement, value) in zip(headers, values):
                    if value.replace('.', '').strip('-').isnumeric():
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    elif value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    else:
                        unexpectedInput = True
                        value = None
                    output[measurement] = value
    if unexpectedInput == True:
        print('Praat output: ' + script_output)
    return output


def generate_pitch_function(algorithm, min_pitch, max_pitch, signal=False, path=None, pulses=False, kwargs=None):
    time_step = 0.01
    if algorithm == 'reaper':
        if signal:
            if pulses:
                ReaperPitch = ReaperPitch_signal_pulse
            else:
                ReaperPitch = ReaperPitch_signal
        else:
            if pulses:
                ReaperPitch = ReaperPitch_file_pulse
            else:
                ReaperPitch = ReaperPitch_file
        if path is not None:
            pitch_function = partial(ReaperPitch, reaper_path=path)
        else:
            raise (AcousticError('Could not find the REAPER executable'))
    elif algorithm == 'praat':
        if kwargs is None:
            kwargs = {}
        if signal:
            PraatPitch = PraatPitch_signal
        else:
            PraatPitch = PraatPitch_file
        if path is not None:
            pitch_function = partial(PraatPitch, praat_path=path, **kwargs)
        else:
            raise (AcousticError('Could not find the Praat executable'))
    else:
        if signal:
            ASPitch = ASPitch_signal
        else:
            ASPitch = ASPitch_file
        pitch_function = partial(ASPitch)
    pitch_function = partial(pitch_function, time_step=time_step, min_pitch=min_pitch, max_pitch=max_pitch)
    return pitch_function


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


def generate_base_intensity_function(corpus_context, signal=False, gender=None):
    algorithm = corpus_context.config.intensity_source
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        if signal:
            PraatIntensity = PraatIntensity_signal
        else:
            PraatIntensity = PraatIntensity_file
        intensity_function = partial(PraatIntensity,
                                     praat_path=corpus_context.config.praat_path,
                                     time_step=0.01)
    else:
        raise (NotImplementedError('Only function for intensity currently implemented is Praat.'))
    return intensity_function
import time
import logging

import os
import math
import csv

from functools import partial

from ..sql.models import SoundFile, Discourse

from ..exceptions import GraphQueryError, AcousticError

from acousticsim.analysis.pitch import (signal_to_pitch as ASPitch_signal, file_to_pitch as ASPitch_file,
                                        signal_to_pitch_praat as PraatPitch_signal,
                                        file_to_pitch_praat as PraatPitch_file,
                                        signal_to_pitch_reaper as ReaperPitch_signal,
                                        file_to_pitch_reaper as ReaperPitch_file
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

def generate_phone_segments_by_speaker(corpus_context, phone_class, call_back=None):
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
    speakers = corpus_context.speakers
    segment_mapping = {}
    discourse_mapping = {}
    phone_ids = {}
    for s in speakers:
        time_sp = time.time()
        segments = []
        speaker_has_phone = False
        discourses = corpus_context.census[s].discourses
        discourses = list(discourses)
        print(s)
        for d in discourses:
            # qr = corpus_context.query_graph(corpus_context.phone).filter(corpus_context.phone.id.in_(query))
            qr = corpus_context.query_graph(corpus_context.phone).filter(corpus_context.phone.type_subset == phone_class)
            qr = qr.filter(corpus_context.phone.discourse.name == d.discourse.name)
            qr = qr.filter(corpus_context.phone.speaker.name == s)
            if qr.count() == 0:
                continue
            phones = qr.all()
            speaker_has_phone = True
            q = corpus_context.sql_session.query(SoundFile).join(Discourse)
            q = q.filter(Discourse.name == d.discourse.name)
            sound_file = q.first()
            if sound_file is None:
                print(d.discourse.name)
            channel = d.channel
            if phones is not None:
                for ph in phones:
                    if 'vowel' in phone_class:
                        phone_ids[(sound_file.vowel_filepath, ph.begin, ph.end, channel)] = ph.id
                        segments.append((sound_file.vowel_filepath, ph.begin, ph.end, channel))
                    else:
                        phone_ids[(sound_file.consonant_filepath, ph.begin, ph.end, channel)] = ph.id
                        segments.append((sound_file.consonant_filepath, ph.begin, ph.end, channel))
            if phone_class is 'vowel':
                discourse_mapping[sound_file.discourse.name] = sound_file.consonant_filepath
            else:
                discourse_mapping[sound_file.discourse.name] = sound_file.consonant_filepath
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
        discourses = corpus_context.census[s].discourses
        for d in discourses:
            q = corpus_context.sql_session.query(SoundFile).join(Discourse)
            q = q.filter(Discourse.name == d.discourse.name)
            sound_file = q.first()
            if sound_file is None:
                print(d.discourse.name)
            channel = d.channel
            atype = corpus_context.hierarchy.highest
            prob_utt = getattr(corpus_context, atype)
            q = corpus_context.query_graph(prob_utt)
            q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
            q = q.filter(prob_utt.speaker.name == s)
            utterances = q.all()
            for u in utterances:
                segments.append((sound_file.vowel_filepath, u.begin, u.end, channel))
            discourse_mapping[sound_file.vowel_filepath] = d.discourse.name
        segment_mapping[s] = segments
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
    elif corpus_context.config.pitch_source == 'reaper':
        path = corpus_context.config.reaper_path
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
            gender = corpus_context.census[speaker].get('Gender')
            if gender is not None:
                if gender.lower()[0] == 'f':
                    min_pitch = 100
                else:
                    max_pitch = 400
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
    Analyze formants of an entire utterance using multiprocessing from acousticsim, and save the resulting formant tracks into the database.
    
    Arguments:
    -- corpus_context: corpus context to use
    (optional:) call_back: call back function
    (optional:) stop_check: stop check function
    """
    q = corpus_context.sql_session.query(SoundFile).join(Discourse)
    sound_files = q.all()

    num_sound_files = len(sound_files)
    segment_mapping, discourse_mapping = generate_speaker_segments(corpus_context)
    if call_back is not None:
        call_back('Analyzing files...')
        call_back(0, num_sound_files)
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        if corpus_context.hierarchy.has_speaker_property('gender'):
            gen = corpus_context.census[speaker].get('Gender')
            if gen is not None:
                formant_function = generate_base_formants_function(corpus_context, signal=True, gender=gen)
            else:
                formant_function = generate_base_formants_function(corpus_context, signal=True)
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

    Arguments:
    -- corpus_context: corpus context to use
    -- call_back: call back function
    (optional:) stop_check: stop check function
    (optional:) vowel_inventory: list of vowels used to encode a class 'vowel': if not used, it's assumed that 'vowel' is already a phone class
    """
    # encodes vowel inventory into a phone class if it's specified
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')
    # gets segment mapping of phones that are vowels
    segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, 'vowel', call_back=call_back)
    if call_back is not None:
        call_back('Analyzing files...')
    # goes through each phone and: makes a formant function, analyzes the phone, and saves the tracks
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        if corpus_context.hierarchy.has_speaker_property('gender'):
            gen = corpus_context.census[speaker].get('Gender')
            if gen is not None:
                formant_function = generate_base_formants_function(corpus_context, signal=True, gender=gen)
            else:
                formant_function = generate_base_formants_function(corpus_context, signal=True)
        else:
            formant_function = generate_base_formants_function(corpus_context, signal=True)
        output = analyze_file_segments(v, formant_function, padding=None, stop_check=stop_check)
        corpus_context.save_formant_tracks(output, speaker)

def analyze_intensity(corpus_context,
                     call_back=None,
                     stop_check=None):
    """
    Analyze intensity of an entire utterance using multiprocessing from acousticsim, and save the resulting intensity tracks into the database.

    Arguments:
    -- corpus_context: corpus context to use
    -- call_back: call back function
    -- stop_check: stop check function
    """
    q = corpus_context.sql_session.query(SoundFile).join(Discourse)
    sound_files = q.all()

    num_sound_files = len(sound_files)
    segment_mapping, discourse_mapping = generate_speaker_segments(corpus_context)
    if call_back is not None:
        call_back('Analyzing files...')
        call_back(0, num_sound_files)
    #formant_function = generate_base_formants_function(corpus_context, signal=False, gender=g))
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        if corpus_context.hierarchy.has_speaker_property('gender'):
            gen = corpus_context.census[speaker].get('Gender')
            if gen is not None:
                intensity_function = generate_base_intensity_function(corpus_context, signal=True, gender=gen)
            else:
                intensity_function = generate_base_intensity_function(corpus_context, signal=True)
        else:
            intensity_function = generate_base_intensity_function(corpus_context, signal=True)
        output = analyze_file_segments(v, intensity_function, padding=PADDING, stop_check=stop_check)
        corpus_context.save_intensity_tracks(output, speaker)


def make_path_safe(path):
    return path.replace('\\', '/').replace(' ', '%20')

def analyze_script(corpus_context,
                   phone_class,
                   script_path,
                   result_measurement,
                   arguments=None,
                   call_back=None,
                   stop_check=None):
    '''
    Perform acoustic analysis of phones using an input praat script.
    Praat script requirements: 
        -the only input is the full path to the soundfile containing (only) the phone
        -the script prints the output to the Praat Info window
    
    Arguments:
    -- corpus_context: corpus context to use
    -- phone_class: an already encoded phone class, on which the analysis will be run
    -- script_path: path to the praat script
    -- result_measurement: name to be used in the database for the measurement generated by the praat script
    (optional:) arguments: a list containing any arguments to the praat script (currently not working)
    (optional:) call_back: call back function
    (optional:) stop_check: stop check function
    
    Result: saves the measurement results from the praat script into the database in a column with the same name as result_measurement.
    '''
    output_type = None
    if call_back is not None:
        call_back('Analyzing phones...')
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import_' + result_measurement + '.csv'
    time_section = time.time()
    segment_mapping, discourse_mapping, phone_ids = generate_phone_segments_by_speaker(corpus_context, phone_class, call_back=call_back)
    print("generate segments took: " + str(time.time() - time_section))
    if call_back is not None:
        call_back("generate segments took: " + str(time.time() - time_section))
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, result_measurement, arguments=arguments)
    with open(os.path.join(directory, csv_name), 'w', newline='') as f:
        header = ['id', 'begin', 'end', result_measurement]
        writer = csv.DictWriter(f, header, delimiter=',')
        writer.writeheader()
        for i, (speaker, v) in enumerate(segment_mapping.items()):
            if stop_check is not None and stop_check():
                break
            if call_back is not None:
                #call_back('Analyzing file {} of {} ({})...'.format(i, num_sound_files, sf.filepath))
                call_back(i)
            time_section = time.time()
            output = analyze_file_segments(v, script_function, padding=None, stop_check=stop_check)
            if call_back is not None:
                call_back("time analyzing segments: " + str(time.time() - time_section))
            print("time analyzing segments: " + str(time.time() - time_section))

            for vector in output.keys():
                filepath, begin, end, channel = vector
                row = {}
                row['id'] = phone_ids[vector]
                row['begin'] = begin
                row['end'] = end
                row[result_measurement] = output[vector]
                writer.writerow(row)
                output_type = type(output[vector]).__name__
    script_data_from_csv(corpus_context, result_measurement, output_type)


def script_data_from_csv(corpus_context, result_measurement, output_type):
    '''
    Save data from a csv file into the database.
    
    Arguments:
    -- corpus_context: corpus context
    -- result_measurement: measurement label
    -- output_type: type of the result being saved
    '''
    if output_type == 'int':
        cypher_set_template = 'n.{name} = toInt(csvLine.{name})'
    elif output_type == 'bool':
        cypher_set_template = '''n.{name} = (CASE WHEN csvLine.{name} = 'False' THEN false ELSE true END)'''
    elif output_type == 'float':
        cypher_set_template = 'n.{name} = toFloat(csvLine.{name})'
    else:
        cypher_set_template = 'n.{name} = csvLine.{name}'
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import_' + result_measurement + '.csv'
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
    types = {result_measurement : output_type}
    corpus_context.hierarchy.add_token_properties(corpus_context, 'phone', types.items())
    corpus_context.refresh_hierarchy()


def signal_to_praat_script(signal, sr, praat_path=None,time_step=0.01,
                           begin=None, padding=None, script_path=None, result_measurement=None, arguments=None):
    '''
    Create a sound file for one phone from a signal and sample rate (using acousticsim), and run the praat script on that phone.
    
    Arguments:
    -- signal: input from acousticsim multiprocessing, used to get phone wavfile
    -- sr: input from acousticsim multiprocessing, used to get phone wavfile
    -- praat_path: path to praat
    -- time_step: parameter that can be used by acousticsim for multiprocessing?
    -- begin: parameter that can be used by acousticsim for multiprocessing?
    -- padding: time padding around segment: must be None or 0 for phone analysis to work!
    -- script_path: path to the praat script
    -- result_measurement: measurement label
    (optional:) arguments: a list containing any arguments to the praat script (currently not used)
    
    Returns:
    -- output from Praat script on the file
    '''
    with ASTemporaryWavFile(signal, sr) as wav_path:
        if praat_path is None:
            praat_path = 'praat'
            if sys.platform == 'win32':
                praat_path += 'con.exe'
        script_output = run_script(praat_path, script_path, wav_path).strip()
        if script_output.replace('.', '').isnumeric():
            if '.' in script_output:
                script_output = float(script_output)
            else:
                script_output = int(script_output)
        else:
            print('Praat output: ' + script_output)
            script_output = None
        return script_output

def generate_praat_script_function(praat_path, script_path, result_measurement, arguments=None):
    '''
    Generate a partial function that calls the praat script specified.
    (used as input to analyze_file_segments)
    
    Arguments:
    -- praat_path: path to praat/praatcon
    -- script_path: path to the script
    -- result_measurement: measurement label
    (optional:) arguments: a list containing any arguments to the praat script (not currently used)
    :return: the partial function
    '''
    praat_function = partial(signal_to_praat_script,
                             praat_path=praat_path,
                             script_path=script_path, result_measurement=result_measurement, arguments=arguments)
    return praat_function

def generate_pitch_function(algorithm, min_pitch, max_pitch, signal=False, path=None):
    time_step = 0.01
    if algorithm == 'reaper':
        if signal:
            ReaperPitch = ReaperPitch_signal
        else:
            ReaperPitch = ReaperPitch_file
        if path is not None:
            pitch_function = partial(ReaperPitch, reaper_path=path)
        else:
            raise (AcousticError('Could not find the REAPER executable'))
    elif algorithm == 'praat':
        if signal:
            PraatPitch = PraatPitch_signal
        else:
            PraatPitch = PraatPitch_file
        if path is not None:
            pitch_function = partial(PraatPitch, praat_path=path)
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


import time
import logging

import os

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
                                           signal_to_formants_praat as PraatFormants_signal, file_to_formants_praat as PraatFormants_file)
from acousticsim.analysis.intensity import signal_to_intensity_praat as PraatIntensity_signal, file_to_intensity_praat as PraatIntensity_file


from acousticsim.main import analyze_long_file
from acousticsim.multiprocessing import generate_cache, default_njobs

padding = 0.1

def acoustic_analysis(corpus_context,
                      pitch = True,
                      formants = False,
                      intensity = False,
                      call_back = None,
                      stop_check = None):

    """
    Calls get_pitch and get_formants for each sound file in a corpus

    Parameters
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus being analyzed

    """
    q = corpus_context.sql_session.query(SoundFile).join(Discourse)
    sound_files = q.all()

    num_sound_files = len(sound_files)
    if call_back is not None:
        call_back('Analyzing files...')
        call_back(0, num_sound_files)
    long_files = list(filter(lambda x: x.duration > 30, sound_files))
    short_files = list(filter(lambda x: x.duration <= 30, sound_files))
    for i, sf in enumerate(long_files):
        if stop_check is not None and stop_check():
            break
        if call_back is not None:
            call_back('Analyzing file {} of {} ({})...'.format(i, num_sound_files, sf.filepath))
            call_back(i)
        if pitch:
            analyze_pitch(corpus_context, sf, stop_check=stop_check)
        if formants:
            analyze_formants(corpus_context, sf, stop_check=stop_check)
        if intensity:
            analyze_intensity(corpus_context, sf, stop_check=stop_check)

    if call_back is not None:
        call_back('Analyzing short files...')
    if pitch:
        analyze_pitch_short_files(corpus_context, short_files,
                                  call_back = call_back, stop_check = stop_check)
    if formants:
        analyze_formants_short_files(corpus_context, short_files,
                                  call_back = call_back, stop_check = stop_check)
    if intensity:
        analyze_intensity_short_files(corpus_context, short_files,
                                  call_back = call_back, stop_check = stop_check)


def generate_base_pitch_function(corpus_context, signal=False, gender=None):
    algorithm = corpus_context.config.pitch_algorithm
    min_pitch = 70
    max_pitch = 300
    time_step = 0.01
    if gender is not None:
        if gender.lower().startswith('f'):
            min_pitch = 100
        elif gender.lower().startswith('m'):
            max_pitch = 250

    if algorithm == 'reaper':
        if signal:
            ReaperPitch = ReaperPitch_signal
        else:
            ReaperPitch = ReaperPitch_file
        if getattr(corpus_context.config, 'reaper_path', None) is not None:
            pitch_function = partial(ReaperPitch, reaper = corpus_context.config.reaper_path)
        else:
            raise(AcousticError('Could not find the REAPER executable'))
    elif algorithm == 'praat':
        if signal:
            PraatPitch = PraatPitch_signal
        else:
            PraatPitch = PraatPitch_file
        if getattr(corpus_context.config, 'praat_path', None) is not None:
            pitch_function = partial(PraatPitch, praat_path = corpus_context.config.praat_path)
        else:
            raise(AcousticError('Could not find the Praat executable'))
    else:
        if signal:
            ASPitch = ASPitch_signal
        else:
            ASPitch = ASPitch_file
        pitch_function = partial(ASPitch, window_shape = 'gaussian')
    pitch_function = partial(pitch_function, time_step = time_step, min_pitch = min_pitch, max_pitch = max_pitch)
    return pitch_function

def generate_base_formants_function(corpus_context, signal = False, gender = None):
    algorithm = corpus_context.config.formant_algorithm
    max_freq = 5500
    if gender == 'M':
        max_freq = 5000
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise(AcousticError('Could not find the Praat executable'))
        if signal:
            PraatFormants = PraatFormants_signal
        else:
            PraatFormants = PraatFormants_file
        formant_function = partial(PraatFormants,
                            praat_path = corpus_context.config.praat_path,
                            max_freq = max_freq, num_formants = 5, win_len = 0.025,
                            time_step = 0.01)
    else:
        if signal:
            ASFormants = ASFormants_signal
        else:
            ASFormants = ASFormants_file
        formant_function = partial(ASFormants, max_freq = max_freq,
                                        time_step = 0.01, num_formants = 5,
                                        win_len = 0.025, window_shape = 'gaussian')
    return formant_function

def generate_base_intensity_function(corpus_context, signal = False, gender = None):
    algorithm = corpus_context.config.intensity_algorithm
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise(AcousticError('Could not find the Praat executable'))
        if signal:
            PraatIntensity = PraatIntensity_signal
        else:
            PraatIntensity = PraatIntensity_file
        intensity_function = partial(PraatIntensity,
                            praat_path = corpus_context.config.praat_path,
                            time_step = 0.01)
    else:
        raise(NotImplementedError('Only function for intensity currently implemente is Praat.'))
        if signal:
            ASIntensity = ASIntensity_signal
        else:
            ASIntensity = ASIntensity_file
            intensity_function = partial(ASIntensity,
                                        time_step = 0.01)
    return intensity_function

def analyze_pitch_short_files(corpus_context, files, call_back = None, stop_check = None, use_gender = True):
    files = [x for x in files if not corpus_context.has_pitch(x.discourse.name,corpus_context.config.pitch_algorithm)]
    mappings = []
    functions = []
    discouse_sf_map = {os.path.expanduser(s.vowel_filepath):s.discourse.name  for s in files}
    speaker_mapping = {}
    if use_gender and corpus_context.hierarchy.has_speaker_property('gender'):
        # Figure out gender levels
        genders = corpus_context.genders()
        for g in genders:
            mappings.append([])
            functions.append(generate_base_pitch_function(corpus_context, signal = False, gender = g))
        for f in files:
            fg = f.genders()
            if len(fg) > 1:
                raise(AcousticError('We cannot process files with multiple genders.'))
            i = genders.index(fg[0])
            mappings[i].append((os.path.expanduser(f.vowel_filepath),))
    else:
        mappings.append([(os.path.expanduser(x.vowel_filepath),) for x in files])
        functions.append(generate_base_pitch_function(corpus_context, signal = False))
    for i in range(len(mappings)):
        cache = generate_cache(mappings[i], functions[i], default_njobs() - 1, call_back, stop_check)
        for k, v in cache.items():
            discourse = discouse_sf_map[k]
            corpus_context.save_pitch(discourse, v, channel = 0, # FIXME: Doesn't deal with multiple channels well!
                                        source = corpus_context.config.pitch_algorithm)

def analyze_pitch(corpus_context, sound_file, stop_check = None, use_gender = True):
    filepath = os.path.expanduser(sound_file.vowel_filepath)
    if not os.path.exists(filepath):
        return
    algorithm = corpus_context.config.pitch_algorithm
    if corpus_context.has_pitch(sound_file.discourse.name, algorithm):
        return

    atype = corpus_context.hierarchy.highest
    prob_utt = getattr(corpus_context, atype)
    q = corpus_context.query_graph(prob_utt)
    q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
    q = q.preload(prob_utt.discourse, prob_utt.speaker)
    utterances = q.all()
    segments = []
    gender = None
    for u in utterances:
        if use_gender and u.speaker.gender is not None:
            if gender is None:
                gender = u.speaker.gender
            elif gender != u.speaker.gender:
                raise(AcousticError('Using gender only works with one gender per file.'))

        segments.append((u.begin, u.end, u.channel))

    pitch_function = generate_base_pitch_function(corpus_context, signal = True, gender = gender)
    output = analyze_long_file(filepath, segments, pitch_function, padding = 1, stop_check = stop_check)

    for k, track in output.items():
        corpus_context.save_pitch(sound_file, track, channel = k[-1],
                                    source = algorithm)

def analyze_formants(corpus_context, sound_file, stop_check = None, use_gender = True):
    filepath = os.path.expanduser(sound_file.vowel_filepath)
    if not os.path.exists(filepath):
        return
    algorithm = corpus_context.config.formant_algorithm
    if corpus_context.has_formants(sound_file.discourse.name, algorithm):
        return
    atype = corpus_context.hierarchy.highest
    prob_utt = getattr(corpus_context, atype)
    q = corpus_context.query_graph(prob_utt)
    q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
    utterances = q.all()
    segments = []
    gender = None
    for u in utterances:
        if use_gender and u.speaker.gender is not None:
            if gender is None:
                gender = u.speaker.gender
            elif gender != u.speaker.gender:
                raise(AcousticError('Using gender only works with one gender per file.'))

        segments.append((u.begin, u.end, u.channel))

    formant_function = generate_base_formants_function(corpus_context, signal = True, gender = gender)
    output = analyze_long_file(filepath, segments, formant_function, padding = 1, stop_check = stop_check)
    for k, track in output.items():
        corpus_context.save_formants(sound_file, track, channel = k[-1], source = algorithm)

def analyze_formants_short_files(corpus_context, files, call_back = None, stop_check = None, use_gender = True):
    files = [x for x in files if not corpus_context.has_formants(x.discourse.name,corpus_context.config.formant_algorithm)]
    mappings = []
    functions = []
    discouse_sf_map = {os.path.expanduser(s.vowel_filepath):s.discourse.name  for s in files}
    if use_gender and corpus_context.hierarchy.has_speaker_property('gender'):
        # Figure out gender levels
        genders = corpus_context.genders()
        for g in genders:
            mappings.append([])
            functions.append(generate_base_formants_function(corpus_context, signal = False, gender = g))
        for f in files:
            fg = f.genders()
            if len(fg) > 1:
                raise(AcousticError('We cannot process files with multiple genders.'))
            i = genders.index(fg[0])
            mappings[i].append((os.path.expanduser(f.vowel_filepath),))
    else:
        mappings.append([(os.path.expanduser(x.vowel_filepath),) for x in files])
        functions.append(generate_base_formants_function(corpus_context, signal = False))
    for i in range(len(mappings)):
        cache = generate_cache(mappings[i], functions[i], default_njobs() - 1, call_back, stop_check)
        for k, v in cache.items():
            discourse = discouse_sf_map[k]
            corpus_context.save_formants(discourse, v, channel = 0, # FIXME: Doesn't deal with multiple channels well!
                                        source = corpus_context.config.pitch_algorithm)


def analyze_intensity(corpus_context, sound_file, stop_check = None, use_gender = True):
    filepath = os.path.expanduser(sound_file.vowel_filepath)
    if not os.path.exists(filepath):
        return
    algorithm = corpus_context.config.pitch_algorithm
    if corpus_context.has_pitch(sound_file.discourse.name, algorithm):
        return

    atype = corpus_context.hierarchy.highest
    prob_utt = getattr(corpus_context, atype)
    q = corpus_context.query_graph(prob_utt)
    q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
    q = q.preload(prob_utt.discourse, prob_utt.speaker)
    utterances = q.all()
    segments = []
    gender = None
    for u in utterances:
        if use_gender and u.speaker.gender is not None:
            if gender is None:
                gender = u.speaker.gender
            elif gender != u.speaker.gender:
                raise(AcousticError('Using gender only works with one gender per file.'))

        segments.append((u.begin, u.end, u.channel))

    intensity_function = generate_base_intensity_function(corpus_context, signal = True, gender = gender)
    output = analyze_long_file(filepath, segments, intensity_function, padding = 1, stop_check = stop_check)

    for k, track in output.items():
        corpus_context.save_pitch(sound_file, track, channel = k[-1], source = algorithm)

def analyze_intensity_short_files(corpus_context, files, call_back = None, stop_check = None, use_gender = True):
    files = [x for x in files if not corpus_context.has_intensity(x.discourse.name,corpus_context.config.intensity_algorithm)]
    mappings = []
    functions = []
    discouse_sf_map = {os.path.expanduser(s.vowel_filepath):s.discourse.name  for s in files}
    if use_gender and corpus_context.hierarchy.has_speaker_property('gender'):
        # Figure out gender levels
        genders = corpus_context.genders()
        for g in genders:
            mappings.append([])
            functions.append(generate_base_intensity_function(corpus_context, signal = False, gender = g))
        for f in files:
            fg = f.genders()
            if len(fg) > 1:
                raise(AcousticError('We cannot process files with multiple genders.'))
            i = genders.index(fg[0])
            mappings[i].append((os.path.expanduser(f.vowel_filepath),))
    else:
        mappings.append([(os.path.expanduser(x.vowel_filepath),) for x in files])
        functions.append(generate_base_intensity_function(corpus_context, signal = False))
    for i in range(len(mappings)):
        cache = generate_cache(mappings[i], functions[i], default_njobs() - 1, call_back, stop_check)
        for k, v in cache.items():
            discourse = discouse_sf_map[k]
            corpus_context.save_intensity(discourse, v, channel = 0, # FIXME: Doesn't deal with multiple channels well!
                                        source = corpus_context.config.pitch_algorithm)
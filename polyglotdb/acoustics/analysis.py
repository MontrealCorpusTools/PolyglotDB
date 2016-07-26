
import time
import logging

import os

from functools import partial

import sqlalchemy

from ..sql.models import SoundFile, Pitch, Formants, Discourse

from ..exceptions import GraphQueryError

from acousticsim.utils import extract_audio

from acousticsim.representations.pitch import signal_to_pitch as ASPitch
from acousticsim.representations.formants import signal_to_formants as ASFormants

from acousticsim.praat import (to_pitch_praat as PraatPitch,
                                to_intensity_praat as PraatIntensity,
                                to_formants_praat as PraatFormants)

from acousticsim.representations.reaper import signal_to_pitch_reaper as ReaperPitch

from acousticsim.main import analyze_long_file

padding = 0.1

def acoustic_analysis(corpus_context,
            acoustics = None,
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
    for i, sf in enumerate(sound_files):
        if stop_check is not None and stop_check():
            break
        if call_back is not None:
            call_back('Analyzing file {} of {} ({})...'.format(i, num_sound_files, sf.filepath))
            call_back(i)
        if acoustics is None:
            analyze_pitch(corpus_context, sf, stop_check = stop_check)
            analyze_formants(corpus_context, sf, stop_check = stop_check)
        elif acoustics == 'pitch':
            analyze_pitch(corpus_context, sf, stop_check = stop_check)
        elif acoustics == 'formants':
            analyze_formants(corpus_context, sf, stop_check = stop_check)

def analyze_pitch(corpus_context, sound_file, stop_check = None):
    filepath = os.path.expanduser(sound_file.vowel_filepath)
    if not os.path.exists(filepath):
        return
    algorithm = corpus_context.config.pitch_algorithm
    if corpus_context.has_pitch(sound_file.discourse.name, algorithm):
        return
    if algorithm == 'reaper':
        if getattr(corpus_context.config, 'reaper_path', None) is not None:
            pitch_function = partial(ReaperPitch, reaper = corpus_context.config.reaper_path,
                                time_step = 0.01, freq_lims = (50,500))
        else:
            return
    elif algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is not None:
            pitch_function = partial(PraatPitch, praatpath = corpus_context.config.praat_path,
                                time_step = 0.01, freq_lims = (75,500))
        else:
            return
    else:
        pitch_function = partial(ASPitch, time_step = 0.01, freq_lims = (75,500), window_shape = 'gaussian')

    atype = corpus_context.hierarchy.highest
    prob_utt = getattr(corpus_context, atype)
    q = corpus_context.query_graph(prob_utt)
    q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
    q = q.preload(prob_utt.discourse, prob_utt.speaker)
    utterances = q.all()
    segments = []
    for u in utterances:
        segments.append((u.begin, u.end, u.channel))

    output = analyze_long_file(filepath, segments, pitch_function, padding = 1)

    for k, track in output.items():
        corpus_context.save_pitch(sound_file, track, channel = k[-1], source = algorithm)

def analyze_formants(corpus_context, sound_file, stop_check = None):
    filepath = os.path.expanduser(sound_file.vowel_filepath)
    if not os.path.exists(filepath):
        return
    algorithm = corpus_context.config.formant_algorithm
    if corpus_context.has_formants(sound_file.discourse.name, algorithm):
        return
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is not None:
            formant_function = partial(PraatFormants,
                                praatpath = corpus_context.config.praat_path,
                                max_freq = 5500, num_formants = 5, win_len = 0.025,
                                time_step = 0.01)
        else:
            return
    else:

        formant_function = partial(ASFormants, freq_lims = (0, 5500),
                                        time_step = 0.01, num_formants = 5,
                                        win_len = 0.025, window_shape = 'gaussian')
    atype = corpus_context.hierarchy.highest
    prob_utt = getattr(corpus_context, atype)
    q = corpus_context.query_graph(prob_utt)
    q = q.filter(prob_utt.discourse.name == sound_file.discourse.name)
    utterances = q.all()
    segments = []
    for i, u in enumerate(utterances):
        segments.append((u.begin, u.end, u.channel))

    output = analyze_long_file(filepath, segments, formant_function, padding = 1)
    for k, track in output.items():
        corpus_context.save_formants(sound_file, track, channel = k[-1], source = algorithm)
    corpus_context.sql_session.flush()

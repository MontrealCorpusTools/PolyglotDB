
import time
import logging

import os

from functools import partial

from polyglotdb.sql.models import SoundFile, Pitch, Formants, Discourse

from acousticsim.utils import extract_audio

from acousticsim.representations.pitch import ACPitch as ASPitch
from acousticsim.representations.formants import LpcFormants as ASFormants

from acousticsim.praat import (to_pitch_praat as PraatPitch,
                                to_intensity_praat as PraatIntensity,
                                to_formants_praat as PraatFormants)

from acousticsim.representations.reaper import to_pitch_reaper as ReaperPitch

from acousticsim.multiprocessing import generate_cache, default_njobs

padding = 0.1

def acoustic_analysis(corpus_context):

    pauses = getattr(corpus_context.config, 'pause_words', None)
    sound_files = corpus_context.sql_session.query(SoundFile).join(Discourse).all()
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Beginning acoustic analysis for {} corpus...'.format(corpus_context.corpus_name))
    initial_begin = time.time()
    for sf in sound_files:
        log.info('Begin acoustic analysis for {}...'.format(sf.filepath))
        log_begin = time.time()
        if pauses is None:
            path = sf.filepath
        else:
            q = corpus_context.query_graph(corpus_context.utterance)
            q = q.filter(corpus_context.utterance.discourse == sf.discourse.name).times()
            utterances = q.all()

            outdir = corpus_context.config.temporary_directory(sf.discourse.name)
            for i, u in enumerate(utterances):
                outpath = os.path.join(outdir, 'temp-{}-{}.wav'.format(u.begin, u.end))
                extract_audio(sf.filepath, outpath, u.begin, u.end, padding = padding)
            path = outdir

        analyze_pitch(corpus_context, sf, path)
        analyze_formants(corpus_context, sf, path)
        log.info('Acoustic analysis finished!')
        log.debug('Acoustic analysis took: {} seconds'.format(time.time() - log_begin))



    log.info('Finished acoustic analysis for {} corpus!'.format(corpus_context.corpus_name))
    log.debug('Total time taken: {} seconds'.format(time.time() - initial_begin))

def analyze_pitch(corpus_context, sound_file, sound_file_path):
    if getattr(corpus_context.config, 'reaper_path', None) is not None:
        pitch_function = partial(ReaperPitch, reaper = corpus_context.config.reaper_path,
                                time_step = 0.01, freq_lims = (75,500))
        algorithm = 'reaper'
    elif getattr(corpus_context.config, 'praat_path', None) is not None:
        pitch_function = partial(PraatPitch, praatpath = corpus_context.config.praat_path,
                                time_step = 0.01, freq_lims = (75,500))
        algorithm = 'praat'
    else:
        pitch_function = partial(ASPitch, time_step = 0.01, freq_lims = (75,500))
        algorithm = 'acousticsim'
    if os.path.isdir(sound_file_path):
        path_mapping = [(os.path.join(sound_file_path, x),) for x in os.listdir(sound_file_path)]

        cache = generate_cache(path_mapping, pitch_function, None, default_njobs(), None, None)
        for k, v in cache.items():
            name = os.path.basename(k)
            name = os.path.splitext(name)[0]
            _, begin, end = name.split('-')
            begin = float(begin) - padding
            if begin < 0:
                begin = 0
            end = float(end)
            for timepoint, value in v.items():
                timepoint += begin # true timepoint
                try:
                    value = value[0]
                except TypeError:
                    pass
                p = Pitch(sound_file = sound_file, time = timepoint, F0 = value, source = algorithm)
                corpus_context.sql_session.add(p)
    else:
        pitch = pitch_function(sound_file_path)
        pitch.process()
        for timepoint, value in pitch.items():
            try:
                value = value[0]
            except TypeError:
                pass
            p = Pitch(sound_file = sound_file, time = timepoint, F0 = value, source = algorithm)
            corpus_context.sql_session.add(p)

def analyze_formants(corpus_context, sound_file, sound_file_path):
    if getattr(corpus_context.config, 'praat_path', None) is not None:
        formant_function = partial(PraatFormants,
                            praatpath = corpus_context.config.praat_path,
                            max_freq = 5500, num_formants = 5, win_len = 0.025,
                            time_step = 0.01)
        algorithm = 'praat'
    else:
        formant_function = partial(ASFormants, max_freq = 5500,
                            num_formants = 5, win_len = 0.025,
                            time_step = 0.01)
        algorithm = 'acousticsim'
    if os.path.isdir(sound_file_path):
        path_mapping = [(os.path.join(sound_file_path, x),) for x in os.listdir(sound_file_path)]

        cache = generate_cache(path_mapping, formant_function, None, default_njobs(), None, None)
        for k, v in cache.items():
            name = os.path.basename(k)
            name = os.path.splitext(name)[0]
            _, begin, end = name.split('-')
            begin = float(begin) - padding
            if begin < 0:
                begin = 0
            end = float(end)
            for timepoint, value in v.items():
                timepoint += begin # true timepoint
                f1, f2, f3 = sanitize_formants(value)
                f = Formants(sound_file = sound_file, time = timepoint, F1 = f1,
                        F2 = f2, F3 = f3, source = algorithm)
                corpus_context.sql_session.add(f)
    else:
        formants = formant_function(sound_file_path)
        for timepoint, value in formants.items():
            f1, f2, f3 = sanitize_formants(value)
            f = Formants(sound_file = sound_file, time = timepoint, F1 = f1,
                    F2 = f2, F3 = f3, source = algorithm)
            corpus_context.sql_session.add(f)

def sanitize_formants(value):
    f1 = value[0][0]
    if f1 is None:
        f1 = 0
    f2 = value[1][0]
    if f2 is None:
        f2 = 0
    f3 = value[2][0]
    if f3 is None:
        f3 = 0
    return f1, f2, f3

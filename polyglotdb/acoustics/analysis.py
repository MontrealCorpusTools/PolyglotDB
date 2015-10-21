
import time
import logging

import os

from functools import partial

from polyglotdb.sql.models import SoundFile, Pitch, Formants, Discourse

from acousticsim.representations.pitch import Pitch as ASPitch
from acousticsim.representations.formants import LpcFormants as ASFormants

from acousticsim.praat import (to_pitch_praat as PraatPitch,
                                to_intensity_praat as PraatIntensity,
                                to_formants_praat as PraatFormants)

import wave

def extract_audio(filepath, outpath, begin, end):
    padding = 0.1
    begin -= padding
    if begin < 0:
        begin = 0
    end += padding
    with wave.open(filepath,'rb') as inf, wave.open(outpath, 'wb') as outf:
        params = inf.getparams()
        sample_rate = inf.getframerate()
        duration = inf.getnframes() / sample_rate
        if end > duration:
            end = duration
        outf.setparams(params)
        outf.setnframes(0)
        begin_sample = int(begin * sample_rate)
        end_sample = int(end * sample_rate)
        inf.readframes(begin_sample)
        data = inf.readframes(end_sample - begin_sample)
        outf.writeframes(data)

def acoustic_analysis(corpus_context):

    pauses = getattr(corpus_context.config, 'pause_words', None)
    sound_files = corpus_context.sql_session.query(SoundFile).join(Discourse).all()
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Beginning acoustic analysis for {} corpus...'.format(corpus_context.corpus_name))
    initial_begin = time.time()
    for sf in sound_files:
        if pauses is None:
            log.info('Processing {}...'.format(sf.filepath))
            analyze_pitch(corpus_context, sf, sf.filepath)
            analyze_formants(corpus_context, sf, sf.filepath)
        else:
            utterances = corpus_context.get_utterances(sf.discourse, pauses,
                min_pause_length = getattr(corpus_context.config, 'min_pause_length', 0.5))

            for i, u in enumerate(utterances):
                outpath = os.path.join(corpus_context.config.temp_dir, 'temp.wav')
                extract_audio(sf.filepath, outpath, u[0], u[1])
                analyze_pitch(corpus_context, sf, outpath)
                analyze_formants(corpus_context, sf, outpath)


    log.info('Finished acoustic analysis for {} corpus!'.format(corpus_context.corpus_name))
    log.debug('Total time taken: {} seconds'.format(time.time() - initial_begin))

def analyze_pitch(corpus_context, sound_file, sound_file_path):
    if getattr(corpus_context.config, 'praat_path', None) is not None:
        pitch_function = partial(PraatPitch, praatpath = corpus_context.config.praat_path)
        algorithm = 'praat'
    else:
        pitch_function = ASPitch
        algorithm = 'acousticsim'
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Begin pitch analysis ({})...'.format(algorithm))
    log_begin = time.time()
    pitch = pitch_function(sound_file_path, time_step = 0.01, freq_lims = (75,500))
    pitch.process()
    for timepoint, value in pitch.items():
        p = Pitch(sound_file = sound_file, time = timepoint, F0 = value[0], source = algorithm)
        corpus_context.sql_session.add(p)
    log.info('Pitch analysis finished!')
    log.debug('Pitch analysis took: {} seconds'.format(time.time() - log_begin))

def analyze_formants(corpus_context, sound_file, sound_file_path):
    if getattr(corpus_context.config, 'praat_path', None) is not None:
        formant_function = partial(PraatFormants, praatpath = corpus_context.config.praat_path)
        algorithm = 'praat'
    else:
        formant_function = ASFormants
        algorithm = 'acousticsim'
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Begin formant analysis ({})...'.format(algorithm))
    log_begin = time.time()
    formants = formant_function(sound_file_path, max_freq = 5500, num_formants = 5, win_len = 0.025, time_step = 0.01)
    for timepoint, value in formants.items():
        f = Formants(sound_file = sound_file, time = timepoint, F1 = value[0][0],
                F2 = value[1][0], F3 = value[2][0], source = algorithm)
        corpus_context.sql_session.add(f)
    log.info('Formant analysis finished!')
    log.debug('Formant analysis took: {} seconds'.format(time.time() - log_begin))

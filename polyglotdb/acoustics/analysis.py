
import time
import logging

from functools import partial

from polyglotdb.sql.models import SoundFile, Pitch, Formants

from acousticsim.representations.pitch import Pitch as ASPitch
from acousticsim.representations.formants import LpcFormants as ASFormants

from acousticsim.praat import (to_pitch_praat as PraatPitch,
                                to_intensity_praat as PraatIntensity,
                                to_formants_praat as PraatFormants)

def acoustic_analysis(corpus_context):
    if getattr(corpus_context.config, 'praat_path', None) is not None:
        formant_function = partial(PraatFormants, praatpath = corpus_context.config.praat_path)
        pitch_function = partial(PraatPitch, praatpath = corpus_context.config.praat_path)
        intensity_function = partial(PraatIntensity, praatpath = corpus_context.config.praat_path)
        algorithm = 'praat'
    else:
        formant_function = ASFormants
        pitch_function = ASPitch
        algorithm = 'acousticsim'
    sound_files = corpus_context.sql_session.query(SoundFile).all()
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Beginning acoustic analysis for {} corpus...'.format(corpus_context.corpus_name))
    initial_begin = time.time()
    for sf in sound_files:
        log.info('Processing {}...'.format(sf.filepath))
        log.info('Begin pitch analysis ({})...'.format(algorithm))
        log_begin = time.time()
        pitch = pitch_function(sf.filepath, time_step = 0.01, freq_lims = (75,500))
        pitch.process()
        for timepoint, value in pitch.items():
            p = Pitch(sound_file = sf, time = timepoint, F0 = value[0], source = algorithm)
            corpus_context.sql_session.add(p)
        log.info('Pitch analysis finished!')
        log.debug('Pitch analysis took: {} seconds'.format(time.time() - log_begin))
        log.info('Begin formant analysis ({})...'.format(algorithm))
        log_begin = time.time()
        formants = formant_function(sf.filepath, max_freq = 5500, num_formants = 5, win_len = 0.025, time_step = 0.01)
        for timepoint, value in formants.items():
            f = Formants(sound_file = sf, time = timepoint, F1 = value[0][0],
                    F2 = value[1][0], F3 = value[2][0], source = algorithm)
            corpus_context.sql_session.add(f)
        log.info('Formant analysis finished!')
        log.debug('Formant analysis took: {} seconds'.format(time.time() - log_begin))
    log.info('Finished acoustic analysis for {} corpus!'.format(corpus_context.corpus_name))
    log.debug('Total time taken: {} seconds'.format(time.time() - initial_begin))

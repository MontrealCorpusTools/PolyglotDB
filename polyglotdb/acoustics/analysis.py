
import time
import logging

from polyglotdb.sql.models import SoundFile, Pitch, Formants

from acousticsim.representations.pitch import Pitch as ASPitch

from acousticsim.representations.formants import LpcFormants as ASFormants

def acoustic_analysis(corpus_context):
    sound_files = corpus_context.sql_session.query(SoundFile).all()
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Beginning acoustic analysis for {} corpus...'.format(corpus_context.corpus_name))
    initial_begin = time.time()
    for sf in sound_files:
        log.info('Processing {}...'.format(sf.filepath))
        log.info('Begin pitch analysis...')
        log_begin = time.time()
        pitch = ASPitch(sf.filepath, 0.01, (75,500))
        pitch.process()
        for timepoint, value in pitch.items():
            p = Pitch(sound_file = sf, time = timepoint, F0 = value[0], source = 'acousticsim')
            corpus_context.sql_session.add(p)
        log.info('Pitch analysis finished!')
        log.debug('Pitch analysis took: {} seconds'.format(time.time() - log_begin))
        log.info('Begin formant analysis...')
        log_begin = time.time()
        formants = ASFormants(sf.filepath, 5500, 5, 0.025, 0.01)
        for timepoint, value in formants.items():
            f = Formants(sound_file = sf, time = timepoint, F1 = value[0][0],
                    F2 = value[1][0], F3 = value[2][0], source = 'acousticsim')
            corpus_context.sql_session.add(f)
        log.info('Formant analysis finished!')
        log.debug('Formant analysis took: {} seconds'.format(time.time() - log_begin))
    log.info('Finished acoustic analysis for {} corpus!'.format(corpus_context.corpus_name))
    log.debug('Total time taken: {} seconds'.format(time.time() - initial_begin))

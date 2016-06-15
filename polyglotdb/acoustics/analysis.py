
import time
import logging

import os

from functools import partial

import sqlalchemy

from ..sql.models import SoundFile, Pitch, Formants, Discourse

from ..exceptions import GraphQueryError

from acousticsim.utils import extract_audio

from acousticsim.representations.pitch import ACPitch as ASPitch
from acousticsim.representations.formants import LpcFormants as ASFormants

from acousticsim.praat import (to_pitch_praat as PraatPitch,
                                to_intensity_praat as PraatIntensity,
                                to_formants_praat as PraatFormants)

from acousticsim.representations.reaper import to_pitch_reaper as ReaperPitch

from acousticsim.multiprocessing import generate_cache, default_njobs

padding = 0.1

def acoustic_analysis(corpus_context,
            speaker_subset = None,
            call_back = None,
            stop_check = None):
    
    """ 
    Calls get_pitch and get_formants for each sound file in a corpus

    Parameters
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus being analyzed

    """
    if speaker_subset is None:
        q = corpus_context.sql_session.query(SoundFile).join(Discourse)
        sound_files = q.all()
    else:
        sound_files = []
        for s in speaker_subset:
            q = corpus_context.sql_session.query(SoundFile).join(Discourse)
            q = q.filter(Discourse.name.like('{}%'.format(s)))
            sound_files += q.all()
    log = logging.getLogger('{}_acoustics'.format(corpus_context.corpus_name))
    log.info('Beginning acoustic analysis for {} corpus...'.format(corpus_context.corpus_name))
    initial_begin = time.time()
    num_sound_files = len(sound_files)
    if call_back is not None:
        call_back('Analyzing files...')
        call_back(0, num_sound_files)
    for i, sf in enumerate(sound_files):
        if stop_check is not None and stop_check():
            log.info('Exiting acoustic analysis! Stopping on {}.'.format(sf.filepath))
            break
        if call_back is not None:
            call_back('Analyzing file {} of {} ({})...'.format(i, num_sound_files, sf.filepath))
            call_back(i)
        log.info('Begin acoustic analysis for {}...'.format(sf.filepath))
        log_begin = time.time()

        get_pitch(corpus_context, sf)
        get_formants(corpus_context, sf)
        log.info('Acoustic analysis finished!')
        log.debug('Acoustic analysis took: {} seconds'.format(time.time() - log_begin))

    log.info('Finished acoustic analysis for {} corpus!'.format(corpus_context.corpus_name))
    log.debug('Total time taken: {} seconds'.format(time.time() - initial_begin))

def get_pitch(corpus_context, sound_file, calculate = True):
    """ 
    Tries to get the pitch of a sound file (F0), excepts sql error

    
    Parameters
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus
    sound_file : : class: `polyglotdb.sql.models.SoundFile`
        the .wav sound file

    Returns
    -------
    listing : list
        list of pitches
    """
    try:
        q = corpus_context.sql_session.query(Pitch).join(SoundFile)
        q = q.filter(SoundFile.id == sound_file.id)
        q = q.filter(Pitch.source == corpus_context.config.pitch_algorithm)
        q = q.order_by(Pitch.time)
        listing = q.all()
        if len(listing) == 0 and calculate:
            sound_file = corpus_context.sql_session.query(SoundFile).join(Discourse).filter(SoundFile.id == sound_file.id).first()

            analyze_pitch(corpus_context, sound_file)
            q = corpus_context.sql_session.query(Pitch).join(SoundFile)
            q = q.filter(SoundFile.id == sound_file.id)
            q = q.filter(Pitch.source == corpus_context.config.pitch_algorithm)
            q = q.order_by(Pitch.time)
            listing = q.all()
    except sqlalchemy.exc.OperationalError:
        return []
    return listing

def get_formants(corpus_context, sound_file, calculate = True):
    """
    Tries to get formants for a sound file (F1-F3), excepts sql error 

    Parameters
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus
    sound_file : : class: `polyglotdb.sql.models.SoundFile`
        the .wav sound file

    Returns
    -------
    listing : list
        list of pitches

    """
    try:
        q = corpus_context.sql_session.query(Formants).join(SoundFile)
        q = q.filter(SoundFile.id == sound_file.id)
        q = q.filter(Formants.source == corpus_context.config.formant_algorithm)
        q = q.order_by(Formants.time)
        listing = q.all()
        if len(listing) == 0 and calculate:
            sound_file = corpus_context.sql_session.query(SoundFile).join(Discourse).filter(SoundFile.id == sound_file.id).first()

            analyze_formants(corpus_context, sound_file)
            q = corpus_context.sql_session.query(Formants).join(SoundFile)
            q = q.filter(SoundFile.id == sound_file.id)
            q = q.filter(Formants.source == corpus_context.config.formant_algorithm)
            q = q.order_by(Formants.time)
            listing = q.all()
    except sqlalchemy.exc.OperationalError:
        return []
    return listing

def analyze_pitch(corpus_context, sound_file):
    """ 
    Analyzes the pitch using different algorithms based on the corpus the sound file is from 
    
    Parameters
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus
    sound_file : : class: `polyglotdb.sql.models.SoundFile`
        the .wav sound file
    """
    algorithm = corpus_context.config.pitch_algorithm
    if algorithm == 'reaper':
        if getattr(corpus_context.config, 'reaper_path', None) is not None:
            pitch_function = partial(ReaperPitch, reaper = corpus_context.config.reaper_path,
                                    time_step = 0.01, freq_lims = (75,500))
        else:
            return
    elif algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is not None:
            pitch_function = partial(PraatPitch, praatpath = corpus_context.config.praat_path,
                                time_step = 0.01, freq_lims = (75,500))
        else:
            return
    else:
        pitch_function = partial(ASPitch, time_step = 0.01, freq_lims = (75,500))

    if sound_file.duration > 5:
        atype = corpus_context.hierarchy.highest
        prob_utt = getattr(corpus_context, atype)
        q = corpus_context.query_graph(prob_utt)
        q = q.filter(prob_utt.discourse.name == sound_file.discourse.name).times()
        utterances = q.all()

        outdir = corpus_context.config.temporary_directory(sound_file.discourse.name)
        for i, u in enumerate(utterances):
            outpath = os.path.join(outdir, 'temp-{}-{}.wav'.format(u['begin'], u['end']))
            if not os.path.exists(outpath):
                extract_audio(sound_file.filepath, outpath, u['begin'], u['end'], padding = padding * 3)

        path_mapping = [(os.path.join(outdir, x),) for x in os.listdir(outdir)]
        try:
            cache = generate_cache(path_mapping, pitch_function, None, default_njobs() - 1, None, None)
        except FileNotFoundError:
            return
        for k, v in cache.items():
            name = os.path.basename(k)
            name = os.path.splitext(name)[0]
            _, begin, end = name.split('-')
            begin = float(begin) - padding * 3
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
        try:
            pitch = pitch_function(sound_file.filepath)
        except FileNotFoundError:
            return
        for timepoint, value in pitch.items():
            try:
                value = value[0]
            except TypeError:
                pass
            p = Pitch(sound_file = sound_file, time = timepoint, F0 = value, source = algorithm)
            corpus_context.sql_session.add(p)
    corpus_context.sql_session.flush()

def analyze_formants(corpus_context, sound_file):
    """ 
    Analyzes the formants using different algorithms based on the corpus the sound file is from 

    Parameters 
    ----------
    corpus_context : : class: `polyglotdb.corpus.BaseContext`
        the type of corpus
    sound_file : : class: `polyglotdb.sql.models.SoundFile`
        the .wav sound file
    """
    algorithm = corpus_context.config.formant_algorithm
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is not None:
            formant_function = partial(PraatFormants,
                                praatpath = corpus_context.config.praat_path,
                                max_freq = 5500, num_formants = 5, win_len = 0.025,
                                time_step = 0.01)
        else:
            return
    else:
        formant_function = partial(ASFormants, max_freq = 5500,
                            num_formants = 5, win_len = 0.025,
                            time_step = 0.01)
    if sound_file.duration > 5:
        atype = corpus_context.hierarchy.highest
        prob_utt = getattr(corpus_context, atype)
        q = corpus_context.query_graph(prob_utt)
        q = q.filter(prob_utt.discourse.name == sound_file.discourse.name).times()
        utterances = q.all()

        outdir = corpus_context.config.temporary_directory(sound_file.discourse.name)
        path_mapping = []
        for i, u in enumerate(utterances):
            outpath = os.path.join(outdir, 'temp-{}-{}.wav'.format(u['begin'], u['end']))
            if not os.path.exists(outpath):
                extract_audio(sound_file.filepath, outpath, u['begin'], u['end'], padding = padding)
            path_mapping.append((outpath,))

        cache = generate_cache(path_mapping, formant_function, None, default_njobs() - 1, None, None)
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
        formants = formant_function(sound_file.filepath)
        for timepoint, value in formants.items():
            f1, f2, f3 = sanitize_formants(value)
            f = Formants(sound_file = sound_file, time = timepoint, F1 = f1,
                    F2 = f2, F3 = f3, source = algorithm)
            corpus_context.sql_session.add(f)

def sanitize_formants(value):
    """ 
    sanitzies formants, making them 0 if they are None 
    
    Parameters
    ----------
    value : list
        the value of the formants

    Returns
    -------
    f1, f2, f3 : int
        the sanitized formants

    """
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

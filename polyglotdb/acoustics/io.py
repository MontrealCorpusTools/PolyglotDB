
import wave
import os


from ..sql import get_or_create

from ..sql.models import (SoundFile, Discourse)


def add_acoustic_info(corpus_context, data):
    """ 
    Add the duration, sampling rate, number of channels, and discourse to a sound file 
    
    Parameters
    ----------
    corpus_context : 
        The corpus type
    data : 
        the file to add info to
    """
    if data.wav_path is None or not os.path.exists(data.wav_path):
        return
    with wave.open(data.wav_path,'rb') as f:
        sample_rate = f.getframerate()
        n_channels = f.getnchannels()
        n_samples = f.getnframes()
        duration = n_samples / sample_rate
    discourse, _ = get_or_create(corpus_context.sql_session, Discourse, name = data.name)
    sf = get_or_create(corpus_context.sql_session, SoundFile, filepath = data.wav_path,
            duration = duration, sampling_rate = sample_rate,
            n_channels = n_channels, discourse = discourse)


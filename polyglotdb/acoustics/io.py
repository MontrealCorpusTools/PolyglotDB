import os
import subprocess
import shutil

import librosa
import audioread

from acousticsim.utils import write_wav

from ..sql import get_or_create

from ..sql.models import (SoundFile, Discourse)


def resample_audio(filepath, new_filepath, new_sr):
    if os.path.exists(new_filepath):
        return
    sox_path = shutil.which('sox')
    if sox_path is not None:
        subprocess.call(['sox', filepath.replace('\\', '/'), new_filepath.replace('\\', '/'),
                         'gain', '-1', 'rate', '-I', str(new_sr)])
    else:
        sig, sr = librosa.load(filepath, sr=new_sr, mono=False)
        if len(sig.shape) > 1:
            sig = sig.T
        write_wav(sig, sr, new_filepath)


def add_discourse_sound_info(corpus_context, discourse, filepath):
    with audioread.audio_open(filepath) as f:
        sample_rate = f.samplerate
        n_channels = f.channels
        duration = f.duration
    audio_dir = corpus_context.discourse_audio_directory(discourse)
    os.makedirs(audio_dir, exist_ok=True)
    consonant_rate = 16000
    consonant_path = os.path.join(audio_dir, 'consonant.wav')
    vowel_rate = 11000
    vowel_path = os.path.join(audio_dir, 'vowel.wav')
    low_freq_rate = 2000
    low_freq_path = os.path.join(audio_dir, 'low_freq.wav')
    if sample_rate > consonant_rate:
        resample_audio(filepath, consonant_path, consonant_rate)
    else:
        shutil.copy(filepath, consonant_path)
        consonant_rate = sample_rate
    if sample_rate > vowel_rate:
        resample_audio(consonant_path, vowel_path, vowel_rate)
    else:
        shutil.copy(filepath, vowel_path)
        vowel_rate = sample_rate
    if sample_rate > low_freq_rate:
        resample_audio(vowel_path, low_freq_path, low_freq_rate)
    else:
        shutil.copy(filepath, low_freq_path)
        low_freq_rate = sample_rate
    user_path = os.path.expanduser('~')
    statement = '''MATCH (d:Discourse:{corpus_name}) where d.name = {{discourse_name}}
                    SET d.filepath = {{filepath}},
                    d.consonant_filepath = {{consonant_filepath}},
                    d.vowel_filepath = {{vowel_filepath}},
                    d.low_freq_filepath = {{low_freq_filepath}},
                    d.duration = {{duration}},
                    d.sampling_rate = {{sampling_rate}},
                    d.n_channels = {{n_channels}}'''.format(corpus_name=corpus_context.cypher_safe_name)
    corpus_context.execute_cypher(statement, filepath=filepath,
                                  consonant_filepath=consonant_path.replace(user_path, '~'),
                                  vowel_filepath=vowel_path.replace(user_path, '~'),
                                  low_freq_filepath=low_freq_path.replace(user_path, '~'),
                                  duration=duration, sampling_rate=sample_rate,
                                  n_channels=n_channels, discourse_name=discourse)


def setup_audio(corpus_context, data):
    if data.wav_path is None or not os.path.exists(data.wav_path):
        return
    add_discourse_sound_info(corpus_context, data.name, data.wav_path)

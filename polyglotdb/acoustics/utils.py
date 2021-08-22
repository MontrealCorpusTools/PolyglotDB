import librosa
from functools import partial
import numpy as np
from librosa.core.spectrum import stft

PADDING = 0.1


def load_waveform(file_path, begin=None, end=None):
    """
    Load a waveform segment from an audio file

    Parameters
    ----------
    file_path : str
        Path to audio file
    begin : float
        Time stamp of beginning of segment
    end : float
        Time stamp of end of segment

    Returns
    -------
    numpy.array
        Signal data
    int
        Sample rate
    """
    if begin is None:
        begin = 0.0
    duration = None
    if end is not None:
        duration = end - begin
    signal, sr = librosa.load(file_path, sr=None, offset=begin, duration=duration)
    signal = lfilter([1., -0.95], 1, signal, axis=0)
    return signal, sr


def generate_spectrogram(signal, sr, log_color_scale=True):
    """
    Generate a spectrogram

    Parameters
    ----------
    signal : numpy.array
        Signal to generate spectrogram from
    sr : int
        Sample rate of the signal
    log_color_scale : bool
        Flag to make the color scale logarithmic

    Returns
    -------
    numpy.array
        Spectrogram data
    float
        Time step between frames
    float
        Frequency step between bins
    """
    from scipy.signal import lfilter
    from scipy.signal import gaussian
    n_fft = 256
    # if len(self._signal) / self._sr > 30:
    window_length = 0.005
    win_len = int(window_length * sr)
    if win_len > n_fft:
        n_fft = win_len
    num_steps = 500
    if len(signal) < num_steps:
        num_steps = len(signal)
    step_samp = int(len(signal) / num_steps)
    time_step = step_samp / sr
    freq_step = sr / n_fft
    # if step_samp < 28:
    #    step_samp = 28
    #    step = step_samp / self._sr
    # self._n_fft = 512
    # window = partial(gaussian, std = 250/12)
    window = 'gaussian'
    # win_len = None
    if window == 'gaussian':
        window = partial(gaussian, std=0.45 * win_len / 2)
    data = stft(signal, n_fft, step_samp, center=True, win_length=win_len, window=window)
    data = np.abs(data)
    if log_color_scale:
        data = 20 * np.log10(data)
    return data, time_step, freq_step


def make_path_safe(path):
    """
    Make a path safe for use in Cypher

    Parameters
    ----------
    path : str
        Path to sanitize

    Returns
    -------
    str
        Cypher-safe path
    """
    return path.replace('\\', '/').replace(' ', '%20')

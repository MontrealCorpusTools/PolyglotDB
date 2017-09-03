import librosa
from scipy.signal import lfilter

from functools import partial
import numpy as np
from scipy.signal import gaussian
from librosa.core.spectrum import stft


PADDING = 0.1

def load_waveform(file_path):
    signal, sr = librosa.load(file_path, sr=None)

    signal = lfilter([1., -0.95], 1, signal, axis=0)
    return signal, sr


def generate_spectrogram(signal, sr, color_scale='log'):
    n_fft = 256

    # if len(self._signal) / self._sr > 30:
    window_length = 0.005
    win_len = int(window_length * sr)
    if win_len > n_fft:
        n_fft = win_len
    num_steps = 1000
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
        window = partial(gaussian, std=0.45 * (win_len) / 2)
    # import matplotlib.pyplot as plt
    # plt.plot(window(250))
    # plt.show()
    data = stft(signal, n_fft, step_samp, center=True, win_length=win_len, window=window)

    data = np.abs(data)
    data = 20 * np.log10(data) if color_scale == 'log' else data
    return data, time_step, freq_step


def make_path_safe(path):
    return path.replace('\\', '/').replace(' ', '%20')

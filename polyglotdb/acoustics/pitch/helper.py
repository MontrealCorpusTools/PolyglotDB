
from functools import partial

from acousticsim.analysis.pitch import (signal_to_pitch as ASPitch_signal, file_to_pitch as ASPitch_file,
                                        signal_to_pitch_praat as PraatPitch_signal,
                                        file_to_pitch_praat as PraatPitch_file,
                                        signal_to_pitch_reaper as ReaperPitch_signal,
                                        file_to_pitch_reaper as ReaperPitch_file,
                                        signal_to_pitch_and_pulse_reaper as ReaperPitch_signal_pulse,
                                        file_to_pitch_and_pulse_reaper as ReaperPitch_file_pulse,
                                        )

from ...exceptions import GraphQueryError, AcousticError, SpeakerAttributeError


def generate_pitch_function(algorithm, min_pitch, max_pitch, signal=False, path=None, pulses=False, kwargs=None):
    time_step = 0.01
    if algorithm == 'reaper':
        if signal:
            if pulses:
                ReaperPitch = ReaperPitch_signal_pulse
            else:
                ReaperPitch = ReaperPitch_signal
        else:
            if pulses:
                ReaperPitch = ReaperPitch_file_pulse
            else:
                ReaperPitch = ReaperPitch_file
        if path is not None:
            pitch_function = partial(ReaperPitch, reaper_path=path)
        else:
            raise (AcousticError('Could not find the REAPER executable'))
    elif algorithm == 'praat':
        if kwargs is None:
            kwargs = {}
        if signal:
            PraatPitch = PraatPitch_signal
        else:
            PraatPitch = PraatPitch_file
        if path is not None:
            pitch_function = partial(PraatPitch, praat_path=path, **kwargs)
        else:
            raise (AcousticError('Could not find the Praat executable'))
    else:
        if signal:
            ASPitch = ASPitch_signal
        else:
            ASPitch = ASPitch_file
        pitch_function = partial(ASPitch)
    pitch_function = partial(pitch_function, time_step=time_step, min_pitch=min_pitch, max_pitch=max_pitch)
    return pitch_function
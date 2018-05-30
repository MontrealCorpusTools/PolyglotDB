from conch.analysis.pitch import ReaperPitchTrackFunction, PraatSegmentPitchTrackFunction, PitchTrackFunction


def generate_pitch_function(algorithm, min_pitch, max_pitch, path=None, kwargs=None):
    time_step = 0.01
    if algorithm == 'reaper':
        pitch_function = ReaperPitchTrackFunction(reaper_path=path, min_pitch=min_pitch, max_pitch=max_pitch,
                                                  time_step=time_step)
    elif algorithm == 'praat':
        if kwargs is None:
            kwargs = {}
        pitch_function = PraatSegmentPitchTrackFunction(praat_path=path, min_pitch=min_pitch, max_pitch=max_pitch,
                                                 time_step=time_step, **kwargs)
    else:
        pitch_function = PitchTrackFunction(min_pitch=min_pitch, max_pitch=max_pitch, time_step=time_step)
    return pitch_function

from functools import partial
from acousticsim.main import analyze_file_segments
from acousticsim.analysis.intensity import signal_to_intensity_praat as PraatIntensity_signal, \
    file_to_intensity_praat as PraatIntensity_file

from .segments import generate_utterance_segments
from ..exceptions import AcousticError, SpeakerAttributeError

from .utils import PADDING


def analyze_intensity(corpus_context,
                      call_back=None,
                      stop_check=None):
    """
    Analyze intensity of an entire utterance, and save the resulting intensity tracks into the database.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        corpus context to use
    call_back : callable
        call back function, optional
    stop_check : function
        stop check function, optional
    """
    segment_mapping = generate_utterance_segments(corpus_context).grouped_mapping('speaker')
    if call_back is not None:
        call_back('Analyzing files...')
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            intensity_function = generate_base_intensity_function(corpus_context, signal=True, gender=gender)
        else:
            intensity_function = generate_base_intensity_function(corpus_context, signal=True)
        output = analyze_file_segments(v, intensity_function, padding=PADDING, stop_check=stop_check)
        corpus_context.save_intensity_tracks(output, speaker)


def generate_base_intensity_function(corpus_context, signal=False, gender=None):
    algorithm = corpus_context.config.intensity_source
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        if signal:
            PraatIntensity = PraatIntensity_signal
        else:
            PraatIntensity = PraatIntensity_file
        intensity_function = partial(PraatIntensity,
                                     praat_path=corpus_context.config.praat_path,
                                     time_step=0.01)
    else:
        raise (NotImplementedError('Only function for intensity currently implemented is Praat.'))
    return intensity_function

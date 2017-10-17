from conch import analyze_segments
from conch.analysis.intensity import PraatSegmentIntensityTrackFunction

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
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING).grouped_mapping('speaker')
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
        intensity_function = generate_base_intensity_function(corpus_context)
        output = analyze_segments(v, intensity_function, stop_check=stop_check)
        corpus_context.save_intensity_tracks(output, speaker)


def generate_base_intensity_function(corpus_context):
    algorithm = corpus_context.config.intensity_source
    if algorithm == 'praat':
        if getattr(corpus_context.config, 'praat_path', None) is None:
            raise (AcousticError('Could not find the Praat executable'))
        intensity_function = PraatSegmentIntensityTrackFunction(praat_path=corpus_context.config.praat_path, time_step=0.01)
    else:
        raise (NotImplementedError('Only function for intensity currently implemented is Praat.'))
    return intensity_function

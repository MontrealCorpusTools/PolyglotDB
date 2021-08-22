from conch import analyze_segments
from conch.analysis.intensity import PraatSegmentIntensityTrackFunction

from .segments import generate_utterance_segments
from ..exceptions import AcousticError

from .utils import PADDING


def analyze_intensity(corpus_context,
                      source='praat',
                      call_back=None,
                      stop_check=None, multiprocessing=True):
    """
    Analyze intensity of an entire utterance, and save the resulting intensity tracks into the database.

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        corpus context to use
    source : str
        Source program to use (only `praat` available)
    call_back : callable
        call back function, optional
    stop_check : function
        stop check function, optional
    multiprocessing : bool
        Flag to use multiprocessing rather than threading
    """
    segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING, file_type='consonant')
    segment_mapping = segment_mapping.grouped_mapping('speaker')
    if call_back is not None:
        call_back('Analyzing files...')
    if 'intensity' not in corpus_context.hierarchy.acoustics:
        corpus_context.hierarchy.add_acoustic_properties(corpus_context, 'intensity', [('Intensity', float)])
        corpus_context.encode_hierarchy()
    for i, ((speaker,), v) in enumerate(segment_mapping.items()):
        intensity_function = generate_base_intensity_function(corpus_context)
        output = analyze_segments(v, intensity_function, stop_check=stop_check, multiprocessing=multiprocessing)
        corpus_context.save_acoustic_tracks('intensity', output, speaker)


def generate_base_intensity_function(corpus_context):
    """
    Generate an Intensity function from Conch

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.CorpusContext`
        CorpusContext to use for getting path to Praat (if not on the system path)

    Returns
    -------
    :class:`~conch.analysis.intensity.PraatSegmentIntensityTrackFunction`
        Intensity analysis function
    """
    if getattr(corpus_context.config, 'praat_path', None) is None:
        raise (AcousticError('Could not find the Praat executable'))
    intensity_function = PraatSegmentIntensityTrackFunction(praat_path=corpus_context.config.praat_path, time_step=0.01)
    return intensity_function

from conch import analyze_segments

from ..segments import generate_vowel_segments, generate_utterance_segments

from .helper import generate_formants_point_function, generate_base_formants_function

from ...exceptions import SpeakerAttributeError

from ..utils import PADDING


def analyze_formant_points(corpus_context, call_back=None, stop_check=None, vowel_label='vowel',
                           duration_threshold=None, multiprocessing=True):
    """First pass of the algorithm; generates prototypes.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    call_back : callable
        Information about callback.
    stop_check : string
        Information about stop check.
    vowel_label : str
        The subset of phones to analyze.
    duration_threshold : float, optional
        Segments with length shorter than this value (in milliseconds) will not be analyzed.

    Returns
    -------
    dict
        Track data
    """
    # ------------- Step 1: Prototypes -------------
    if not corpus_context.hierarchy.has_type_subset('phone', vowel_label):
        raise Exception('Phones do not have a "{}" subset.'.format(vowel_label))

    # Gets segment mapping of phones that are vowels

    segment_mapping = generate_vowel_segments(corpus_context, duration_threshold=duration_threshold, padding=.25, vowel_label=vowel_label)

    if call_back is not None:
        call_back('Analyzing files...')

    formant_function = generate_formants_point_function(corpus_context)  # Make formant function
    output = analyze_segments(segment_mapping, formant_function,
                              stop_check=stop_check, multiprocessing=multiprocessing)  # Analyze the phone
    return output


def analyze_formant_tracks(corpus_context, vowel_label=None, source='praat', call_back=None, stop_check=None, multiprocessing=True):
    """
    Analyze formants of an entire utterance, and save the resulting formant tracks into the database.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    vowel_label : str, optional
        Optional subset of phones to compute tracks over.  If None, then tracks over utterances are computed.
    call_back : callable
        call back function, optional
    stop_check : callable
        stop check function, optional
    """
    if vowel_label is None:
        segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING)
    else:
        if not corpus_context.hierarchy.has_type_subset('phone', vowel_label):
            raise Exception('Phones do not have a "{}" subset.'.format(vowel_label))
        segment_mapping = generate_vowel_segments(corpus_context, padding=0, vowel_label=vowel_label)
    if 'formants' not in corpus_context.hierarchy.acoustics:
        corpus_context.hierarchy.add_acoustic_properties(corpus_context, 'formants', [('F1', float), ('F2', float), ('F3', float)])
        corpus_context.encode_hierarchy()
    segment_mapping = segment_mapping.grouped_mapping('speaker')
    if call_back is not None:
        call_back('Analyzing files...')
    for i, ((speaker,), v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            formant_function = generate_base_formants_function(corpus_context, gender=gender, source=source)
        else:
            formant_function = generate_base_formants_function(corpus_context, source=source)
        output = analyze_segments(v, formant_function, stop_check=stop_check, multiprocessing=multiprocessing)
        corpus_context.save_acoustic_tracks('formants', output, speaker)


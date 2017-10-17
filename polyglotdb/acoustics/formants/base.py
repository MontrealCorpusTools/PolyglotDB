from conch import analyze_segments

from ..segments import generate_vowel_segments, generate_utterance_segments

from .helper import generate_formants_point_function, generate_base_formants_function

from ...exceptions import SpeakerAttributeError

from ..utils import PADDING


def analyze_formant_points(corpus_context, call_back=None, stop_check=None, vowel_inventory=None,
                           duration_threshold=None):
    """First pass of the algorithm; generates prototypes.

    Parameters
    ----------
    corpus_context : :class:`polyglot.corpus.context.CorpusContext`
        The CorpusContext object of the corpus.
    call_back : callable
        Information about callback.
    stop_check : string
        Information about stop check.
    vowel_inventory : list
        A list of all the vowels (in strings) used in the corpus.
    duration_threshold : float, optional
        Segments with length shorter than this value (in milliseconds) will not be analyzed.

    Returns
    -------
    dict
        Track data
    """
    # ------------- Step 1: Prototypes -------------
    # Encodes vowel inventory into a phone class if it's specified
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')

    # Gets segment mapping of phones that are vowels

    segment_mapping = generate_vowel_segments(corpus_context, duration_threshold=duration_threshold, padding=.25)

    if call_back is not None:
        call_back('Analyzing files...')

    formant_function = generate_formants_point_function(corpus_context)  # Make formant function
    output = analyze_segments(segment_mapping, formant_function,
                              stop_check=stop_check)  # Analyze the phone
    return output


def analyze_formant_tracks(corpus_context, call_back=None, stop_check=None):
    """
    Analyze formants of an entire utterance, and save the resulting formant tracks into the database.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    call_back : callable
        call back function, optional
    stop_check : callable
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
        if gender is not None:
            formant_function = generate_base_formants_function(corpus_context, gender=gender)
        else:
            formant_function = generate_base_formants_function(corpus_context)
        output = analyze_segments(v, formant_function, stop_check=stop_check)
        corpus_context.save_formant_tracks(output, speaker)


def analyze_vowel_formant_tracks(corpus_context,
                                 call_back=None,
                                 stop_check=None,
                                 vowel_inventory=None):
    """
    Analyze formants of individual vowels, and save the resulting formant tracks into the database for each phone.

    Parameters
    ----------
    corpus_context : CorpusContext
        corpus context to use
    call_back : callable
        call back function, optional
    stop_check : callable
        stop check function, optional
    vowel_inventory : list of strings
        list of vowels used to encode a class 'vowel', optional.
        if not used, it's assumed that 'vowel' is already a phone class
    """
    # encodes vowel inventory into a phone class if it's specified
    if vowel_inventory is not None:
        corpus_context.encode_class(vowel_inventory, 'vowel')
    # gets segment mapping of phones that are vowels
    segment_mapping = generate_vowel_segments(corpus_context, padding=None).grouped_mapping('speaker')

    if call_back is not None:
        call_back('Analyzing files...')
    # goes through each phone and: makes a formant function, analyzes the phone, and saves the tracks
    for i, (speaker, v) in enumerate(segment_mapping.items()):
        gender = None
        try:
            q = corpus_context.query_speakers().filter(corpus_context.speaker.name == speaker)
            q = q.columns(corpus_context.speaker.gender.column_name('Gender'))
            gender = q.all()[0]['Gender']
        except SpeakerAttributeError:
            pass
        if gender is not None:
            formant_function = generate_base_formants_function(corpus_context, gender=gender)
        else:
            formant_function = generate_base_formants_function(corpus_context)
        output = analyze_segments(v, formant_function, stop_check=stop_check)
        corpus_context.save_formant_tracks(output, speaker)

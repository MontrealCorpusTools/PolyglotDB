import time

from conch import analyze_segments

from conch.analysis.praat import PraatAnalysisFunction

from .segments import generate_segments, generate_utterance_segments

from .io import point_measures_to_csv, point_measures_from_csv
from .utils import PADDING


def generate_praat_script_function(praat_path, script_path, arguments=None):
    """
    Generate a partial function that calls the praat script specified.
    (used as input to analyze_file_segments)

    Parameters
    ----------
    praat_path : string
        full path to praat/praatcon
    script_path: string
        full path to the script
    arguments : list
        a list containing any arguments to the praat script, optional (currently not implemented)

    Returns
    ----------
    function
        the partial function which applies the Praat script to a phone and returns the script output
    """
    praat_function = PraatAnalysisFunction(script_path, praat_path=praat_path, arguments=arguments)
    return praat_function


def analyze_script(corpus_context,
                   phone_class=None,
                   subset=None,
                   annotation_type=None,
                   script_path=None,
                   duration_threshold=0.01,
                   arguments=None,
                   call_back=None,
                   file_type='consonant',
                   stop_check=None, multiprocessing=True):
    """
    Perform acoustic analysis of phones using an input praat script.

    Saves the measurement results from the praat script into the database under the same names as the Praat output columns
    Praat script requirements:

    - the only input is the full path to the sound file containing (only) the phone
    - the script prints the output to the Praat Info window in two rows (i.e. two lines).
    - the first row is a space-separated list of measurement names: these are the names that will be saved into the database
    - the second row is a space-separated list of the value for each measurement

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        corpus context to use
    phone_class : str
        DEPRECATED, the name of an already encoded subset of phones on which the analysis will be run
    subset : str, optional
        the name of an already encoded subset of an annotation type, on which the analysis will be run
    annotation_type : str
        the type of annotation that the analysis will go over
    script_path : str
        full path to the praat script
    duration_threshold : float
        Minimum duration of segments to be analyzed
    file_type : str
        File type to use for the script (consonant = 16kHz sample rate, vowel = 11kHz, low_freq = 1200 Hz)
    arguments : list
        a list containing any arguments to the praat script (currently not working)
    call_back : callable
        call back function, optional
    stop_check : callable
        stop check function, optional
    multiprocessing : bool
        Flag to use multiprocessing, otherwise will use threading
    """
    if file_type not in ['consonant', 'vowel', 'low_freq']:
        raise ValueError('File type must be one of: consonant, vowel, or low_freq')

    if phone_class is not None:
        raise DeprecationWarning("The phone_class parameter has now been deprecated, please use annotation_type='phone' and subset='{}'".format(phone_class))
        annotation_type = corpus_context.phone_name
        subset = phone_class

    if call_back is not None:
        call_back('Analyzing {}...'.format(annotation_type))
    time_section = time.time()
    segment_mapping = generate_segments(corpus_context, annotation_type, subset, file_type=file_type,
                                        padding=0, duration_threshold=duration_threshold)
    if call_back is not None:
        call_back("generate segments took: " + str(time.time() - time_section))
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, arguments=arguments)
    time_section = time.time()
    output = analyze_segments(segment_mapping.segments, script_function, stop_check=stop_check,
                              multiprocessing=multiprocessing)
    if call_back is not None:
        call_back("time analyzing segments: " + str(time.time() - time_section))
    header = sorted(list(output.values())[0].keys())
    header_info = {h: float for h in header}
    point_measures_to_csv(corpus_context, output, header)
    point_measures_from_csv(corpus_context, header_info, annotation_type=annotation_type)
    return [x for x in header if x != 'id']


def analyze_track_script(corpus_context,
                         acoustic_name,
                         properties,
                         script_path,
                         duration_threshold=0.01,
                         phone_class=None,
                         arguments=None,
                         call_back=None,
                         file_type='consonant',
                         stop_check=None, multiprocessing=True):
    if file_type not in ['consonant', 'vowel', 'low_freq']:
        raise ValueError('File type must be one of: consonant, vowel, or low_freq')
    if acoustic_name not in corpus_context.hierarchy.acoustics:
        corpus_context.hierarchy.add_acoustic_properties(corpus_context, acoustic_name, properties)
        corpus_context.encode_hierarchy()
    if call_back is not None:
        call_back('Analyzing phones...')
    if phone_class is None:
        segment_mapping = generate_utterance_segments(corpus_context, padding=PADDING)
    else:
        segment_mapping = generate_segments(corpus_context, corpus_context.phone_name, phone_class, file_type=file_type,
                                            padding=PADDING, duration_threshold=duration_threshold)

    segment_mapping = segment_mapping.grouped_mapping('speaker')
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, arguments=arguments)
    for i, ((speaker,), v) in enumerate(segment_mapping.items()):
        output = analyze_segments(v, script_function, stop_check=stop_check, multiprocessing=multiprocessing)
        corpus_context.save_acoustic_tracks(acoustic_name, output, speaker)

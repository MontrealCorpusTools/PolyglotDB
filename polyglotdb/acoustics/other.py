import time

from conch import analyze_segments

from conch.analysis.praat import PraatAnalysisFunction

from .segments import generate_segments

from .io import point_measures_to_csv, point_measures_from_csv


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
                   phone_class,
                   script_path,
                   arguments=None,
                   call_back=None,
                   stop_check=None):
    """
    Perform acoustic analysis of phones using an input praat script.

    Saves the measurement results from the praat script into the database under the same names as the Praat output columns
    Praat script requirements:
        -the only input is the full path to the soundfile containing (only) the phone
        -the script prints the output to the Praat Info window in two rows (i.e. two lines).
            -the first row is a space-separated list of measurement names: these are the names that will be saved into the database
            -the second row is a space-separated list of the value for each measurement

    Parameters
    ----------
    corpus_context : :class:`~polyglot.corpus.context.CorpusContext`
        corpus context to use
    phone_class : str
        the name of an already encoded phone class, on which the analysis will be run
    script_path : str
        full path to the praat script
    arguments : list
        a list containing any arguments to the praat script (currently not working)
    call_back : callable
        call back function, optional
    stop_check : callable
        stop check function, optional
    """
    # print("analyzing sibilants")
    if call_back is not None:
        call_back('Analyzing phones...')
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import.csv'
    needs_header = True
    output_types = {}
    header = ['id', 'begin', 'end']
    time_section = time.time()
    segment_mapping = generate_segments(corpus_context, corpus_context.phone_name, phone_class, file_type='consonant',
                                        padding=None)
    if call_back is not None:
        call_back("generate segments took: " + str(time.time() - time_section))
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, arguments=arguments)
    time_section = time.time()
    output = analyze_segments(segment_mapping.segments, script_function, stop_check=stop_check)
    if call_back is not None:
        call_back("time analyzing segments: " + str(time.time() - time_section))
    header = sorted(list(output.values())[0].keys())
    header_info = {h: float for h in header}
    point_measures_to_csv(corpus_context, output, header)
    point_measures_from_csv(corpus_context, header_info)

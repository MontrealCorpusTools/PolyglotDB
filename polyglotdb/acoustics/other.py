import sys
import time

from functools import partial

from acousticsim.analysis.helper import ASTemporaryWavFile
from acousticsim.analysis.praat import run_script, read_praat_out
from acousticsim.main import analyze_file_segments

from .segments import generate_segments


from .io import point_measures_to_csv, point_measures_from_csv


def signal_to_praat_script(signal, sr, praat_path=None, time_step=0.01,
                           begin=None, padding=None, script_path=None, arguments=None):
    """
    Create a sound file for one phone from a signal and sample rate, and run the praat script on that phone.

    Parameters
    ----------
    signal
        input from acousticsim multiprocessing, used to get phone wavfile
    sr
        sampling rate. input from acousticsim multiprocessing, used to get phone wavfile
    praat_path : string
        full path to praat
    time_step
        parameter that is used by acousticsim, is input by acousticsim (not the user)
    begin
        parameter that is used by acousticsim, is input by acousticsim (not the user)
    padding : int
        time padding around segment: must be None or 0 for phone analysis to work!
    script_path : string
        path to the praat script to be run
    arguments : list
        a list containing any arguments to the praat script, optional (currently not implemented)

    Returns
    ----------
    script_output : dict
        dictionary of measurement : value, based on the columns output by the Praat script
    """
    with ASTemporaryWavFile(signal, sr) as wav_path:
        if praat_path is None:
            praat_path = 'praat'
            if sys.platform == 'win32':
                praat_path += 'con.exe'
        script_output = run_script(praat_path, script_path, wav_path)
        script_output = parse_script_output(script_output)
        return script_output


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
    praat_function = partial(signal_to_praat_script,
                             praat_path=praat_path,
                             script_path=script_path, arguments=arguments)
    return praat_function


def parse_script_output(script_output):
    """
    Parse the output from Praat into a dictionary of acoustic measurements.
    See docstring of analyze_script for formatting requirements.
    Prints the Praat script output if it doesn't fit the specified format (usually because the Praat script crashed),
    and returns None in that case

    Parameters
    ----------
    script_output : str
        output from Praat. (This is what appears in the Info window when using the Praat GUI)

    Returns
    ----------
    dict
        dictionary of measurement : value, based on the columns output by the Praat script
    """
    headers = []
    output = {}
    unexpected_input = False
    for line in script_output.split('\n'):
        if line.strip() is not "" and line.strip() is not "." and "Warning" not in line and "warning" not in line:
            values = line.strip().split(" ")
            if not headers:
                headers = values
            else:
                for (measurement, value) in zip(headers, values):
                    if value.replace('.', '').strip('-').isnumeric():
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    elif value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    else:
                        unexpected_input = True
                        value = None
                    output[measurement] = value
    if unexpected_input:
        print('Praat output: ' + script_output)
    return output


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
    #print("analyzing sibilants")
    if call_back is not None:
        call_back('Analyzing phones...')
    directory = corpus_context.config.temporary_directory('csv')
    csv_name = 'analyze_script_import.csv'
    needs_header = True
    output_types = {}
    header = ['id', 'begin', 'end']
    time_section = time.time()
    segment_mapping = generate_segments(corpus_context, corpus_context.phone_name, phone_class, file_type='consonant')
    if call_back is not None:
        call_back("generate segments took: " + str(time.time() - time_section))
    praat_path = corpus_context.config.praat_path
    script_function = generate_praat_script_function(praat_path, script_path, arguments=arguments)
    time_section = time.time()
    output = analyze_file_segments(segment_mapping.segments, script_function, padding=None, stop_check=stop_check)
    if call_back is not None:
        call_back("time analyzing segments: " + str(time.time() - time_section))
    header = sorted(output.values()[0].keys())
    header_info = {h: float for h in header}
    point_measures_to_csv(corpus_context, output, header)
    point_measures_from_csv(corpus_context, header_info)


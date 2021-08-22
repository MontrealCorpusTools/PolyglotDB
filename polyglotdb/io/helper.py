
import os
import logging
import operator
import hashlib
import wave
from collections import Counter
from praatio import tgio


from polyglotdb.exceptions import DelimiterError, TextGridError

ATT_TYPES = ['orthography', 'transcription', 'numeric',
             'morpheme', 'tobi', 'grouping']

tobi_characters = set('LH%-+!*')
morph_delimiters = set('-=')


def get_n_channels(file_path):
    """
    Get the number of channels in an audio file

    Parameters
    ----------
    file_path : str
        Path to audio file

    Returns
    -------
    int
        Number of channels
    """
    with wave.open(file_path, 'rb') as soundf:
        n_channels = soundf.getnchannels()
    return n_channels


def normalize_values_for_neo4j(dictionary):
    """
    Sanitizes dictionary for neo4j format by making non-existent values be the string 'NULL'

    Parameters
    ----------
    dictionary : dict
        the dictionary to be sanitized

    Returns
    -------
    dict
        sanitized dictionary
    """
    out = {}
    for k, v in dictionary.items():
        if isinstance(v, list):
            v = '.'.join(map(str, v))
        if not v:
            v = 'NULL'
        out[k] = v
    return out


def guess_type(values, trans_delimiters=None):
    """
    Given a set of values, guesses the value type (numeric, transcription, grouping, tobi, morpheme, orthography)

    Parameters
    ----------
    values : dict
        a dictionary of the possible values
    trans_delimiters : list
        List of transcription delimiters, optional
    
    Returns
    -------
    str
        most probable type (highest count)
    """
    if trans_delimiters is None:
        trans_delimiters = ['.', ' ', ';', ',']
    probable_values = {x: 0 for x in ATT_TYPES}
    for i, v in enumerate(values):
        try:
            t = float(v)
            probable_values['numeric'] += 1
            continue
        except ValueError:
            for d in trans_delimiters:
                if d in v:
                    probable_values['transcription'] += 1
                    break
            else:
                if v == '':
                    probable_values['grouping'] += 1
                elif set(v).issubset(tobi_characters):
                    probable_values['tobi'] += 1
                elif len(set(v) & morph_delimiters) > 0:
                    probable_values['morpheme'] += 1
                else:
                    probable_values['orthography'] += 1
    if probable_values['orthography'] > 0:
        del probable_values['grouping']
    return max(probable_values.items(), key=operator.itemgetter(1))[0]


def guess_trans_delimiter(values):
    """"
    Given a set of values, guess the transition delimiter
    
    Parameters
    ----------
     values : dict
        a dictionary of the possible values

    Returns
    -------
    str
        the most probable delimiter (highest count)

    """
    trans_delimiters = ['.', ' ', ';', ',']
    probable_values = {x: 0 for x in trans_delimiters}
    for l in values:
        for delim in trans_delimiters:
            if delim in l:
                probable_values[delim] += 1
    return max(probable_values.items(), key=operator.itemgetter(1))[0]


def inspect_directory(directory):
    """
    Function to inspect a directory and return the most likely type of
    files within it.

    Searches currently for 'textgrid', 'text', 'buckeye', 'timit', and 'partitur' file
    types.

    Parameters
    ----------
    directory : str
        Full path to the directory

    Returns
    -------
    str
        Most likely type of files
    dict
        Dictionary of the found files separated by the types searched for
    """
    types = ['textgrid', 'text', 'buckeye', 'timit', 'partitur']
    counter = {x: 0 for x in types}
    relevant_files = {x: [] for x in types}
    for root, subdirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[-1].lower()
            if ext == '.textgrid':
                t = 'textgrid'
            elif ext == '.txt':
                t = 'text'
            elif ext == '.words':
                t = 'buckeye'
            elif ext == '.wrd':
                t = 'timit'
            elif ext == '.par,2':
                t = 'partitur'
            else:
                continue
            counter[t] += 1
            relevant_files[t].append(f)
    max_value = max(counter.values())
    for t in ['textgrid', 'buckeye', 'timit', 'text', 'partitur']:
        if counter[t] == max_value:
            likely_type = t
            break

    return likely_type, relevant_files


def text_to_lines(path):
    """
    Parse a text file into lines.

    Parameters
    ----------
    path : str
        Fully specified path to text file

    Returns
    -------
    list
        Non-empty lines in the text file
    """
    delimiter = None
    with open(path, encoding='utf-8-sig', mode='r') as f:
        text = f.read()
        if delimiter is not None and delimiter not in text:
            e = DelimiterError(
                'The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise (e)
    lines = [x.strip().split(delimiter) for x in text.splitlines() if x.strip() != '']
    return lines


def most_frequent_value(dictionary):
    """ 
    Gets the most frequent value in the dictionary

    Parameters
    ----------
    dictionary  : dict
        The dictionary to search through

    Returns
    -------
    object
        the most frequent value
    """
    c = Counter(dictionary.values())
    return max(c.keys(), key=lambda x: c[x])


def calculate_lines_per_gloss(lines):
    """ 
    Calculates lines per gloss of lines

    Parameters
    ----------
    lines : list
        lines in the corpus

    Returns
    -------
    int
        the count of lines per gloss
    """
    line_counts = [len(x[1]) for x in lines]
    equaled = list()
    number = 1
    for i, line in enumerate(line_counts):
        if i == 0:
            equaled.append(False)
        else:
            equaled.append(line == line_counts[i - 1])
    if False not in equaled[1:]:
        # All lines happen to have the same length
        for i in range(2, 6):
            if len(lines) % i == 0:
                number = i
    else:
        false_intervals = list()
        ind = 0
        for i, e in enumerate(equaled):
            if i == 0:
                continue
            if not e:
                false_intervals.append(i - ind)
                ind = i
        false_intervals.append(i + 1 - ind)
        counter = Counter(false_intervals)
        number = max(counter.keys(), key=lambda x: (counter[x], x))
        if number > 10:
            prev_maxes = set([number])
            while number > 10:
                prev_maxes.add(number)
                number = max(x for x in false_intervals if x not in prev_maxes)
    return number


def ilg_text_to_lines(path):
    """
    Converts an ilg file to text lines

    Parameters
    ----------
    path : string
        path to ilg file

    Returns 
    -------
    list
        a sanitized list of lines in the file
    """
    delimiter = None
    with open(path, encoding='utf-8-sig', mode='r') as f:
        text = f.read()
        if delimiter is not None and delimiter not in text:
            e = DelimiterError(
                'The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise (e)
    lines = enumerate(text.splitlines())
    lines = [(x[0], x[1].strip().split(delimiter)) for x in lines if x[1].strip() != '']
    return lines


def find_wav_path(path):
    """
    Find a sound file for a given file, by looking for a .wav file with the
    same base name as the given path

    Parameters
    ----------
    path : str
        Full path to an annotation file

    Returns
    -------
    str or None
        Full path of the wav file if it exists or None if it does not
    """
    name, ext = os.path.splitext(path)

    wav_path = name + '.wav'
    if os.path.exists(wav_path):
        return wav_path

    wav_path = name + '.WAV'
    if os.path.exists(wav_path):
        return wav_path

    return None


def log_annotation_types(annotation_types):
    """
    Writes annotation types to log

    Parameters
    ----------
    annotation_types : list
        a list of types of annotations in a corpus
    """
    logging.info('Annotation type info')
    logging.info('--------------------')
    logging.info('')
    for a in annotation_types:
        logging.info(a.pretty_print())


def make_type_id(type_values, corpus):
    """
    Construct a type ID from the type values and the corpus name

    Parameters
    ----------
    type_values : list
        list of type values
    corpus : str
        the corpus 

    Returns
    -------
    str
        a hex string for the type ID
    """
    m = hashlib.sha1()
    value = ' '.join(map(str, type_values))
    value += ' ' + corpus
    m.update(value.encode())
    return m.hexdigest()


def guess_textgrid_format(path):
    """
    Given a directory, tries to guess what format the TextGrid files are in

    Parameters
    ----------
    path : str
        the path of the directory containing the TextGrid files

    Returns
    -------
    str or None
        textgrid format or None if file is not textgrid and directory doesn't contain TextGrid files
    """
    from .inspect import inspect_labbcat, inspect_mfa, inspect_fave, inspect_maus
    if os.path.isdir(path):
        counts = {'mfa': 0, 'labbcat': 0, 'fave': 0, 'maus': 0, None: 0}
        for root, subdirs, files in os.walk(path):
            for f in files:
                if not f.lower().endswith('.textgrid'):
                    continue
                tg_path = os.path.join(root, f)
                try:
                    tg = tgio.openTextgrid(tg_path)
                except ValueError as e:
                    raise (TextGridError('The file {} could not be parsed: {}'.format(tg_path, str(e))))

                labbcat_parser = inspect_labbcat(tg_path)
                mfa_parser = inspect_mfa(tg_path)
                fave_parser = inspect_fave(tg_path)
                maus_parser = inspect_maus(path)
                if labbcat_parser._is_valid(tg):
                    counts['labbcat'] += 1
                elif mfa_parser._is_valid(tg):
                    counts['mfa'] += 1
                elif fave_parser._is_valid(tg):
                    counts['fave'] += 1
                elif maus_parser._is_valid(tg):
                    counts['maus'] += 1
                else:
                    counts[None] += 1
        return max(counts.keys(), key=lambda x: counts[x])
    elif path.lower().endswith('.textgrid'):
        try:
            tg = tgio.openTextgrid(path)
        except ValueError as e:
            raise (TextGridError('The file {} could not be parsed: {}'.format(path, str(e))))

        labbcat_parser = inspect_labbcat(path)
        mfa_parser = inspect_mfa(path)
        fave_parser = inspect_fave(path)
        maus_parser = inspect_maus(path)
        if labbcat_parser._is_valid(tg):
            return 'labbcat'
        elif mfa_parser._is_valid(tg):
            return 'mfa'
        elif fave_parser._is_valid(tg):
            return 'fave'
        elif maus_parser._is_valid(tg):
            return 'maus'
    return None

import re
import os
import string
import logging
import operator
import hashlib

from collections import Counter

from textgrid import TextGrid

from polyglotdb.exceptions import DelimiterError

ATT_TYPES = ['orthography', 'transcription', 'numeric',
            'morpheme', 'tobi', 'grouping']

tobi_characters = set('LH%-+!*')
morph_delimiters = set('-=')

def normalize_values_for_neo4j(dictionary):
    out = {}
    for k,v in dictionary.items():
        if isinstance(v, list):
            v = '.'.join(map(str,v))
        if not v:
            v = 'NULL'
        out[k] = v
    return out

def guess_type(values, trans_delimiters = None):
    if trans_delimiters is None:
        trans_delimiters = ['.',' ', ';', ',']
    probable_values = {x: 0 for x in ATT_TYPES}
    for i,v in enumerate(values):
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
    trans_delimiters = ['.',' ', ';', ',']
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

    Searches currently for 'textgrid', 'text', 'buckeye' and 'timit' file
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
    types = ['textgrid', 'text', 'buckeye', 'timit']
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
            else:
                continue
            counter[t] += 1
            relevant_files[t].append(f)
    max_value = max(counter.values())
    for t in ['textgrid', 'buckeye', 'timit', 'text']:
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
            e = DelimiterError('The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise(e)
    lines = [x.strip().split(delimiter) for x in text.splitlines() if x.strip() != '']
    return lines

def most_frequent_value(dictionary):
    c = Counter(dictionary.values())
    return max(c.keys(), key = lambda x: c[x])

def calculate_lines_per_gloss(lines):
    line_counts = [len(x[1]) for x in lines]
    equaled = list()
    number = 1
    for i,line in enumerate(line_counts):
        if i == 0:
            equaled.append(False)
        else:
            equaled.append(line == line_counts[i-1])
    if False not in equaled[1:]:
        #All lines happen to have the same length
        for i in range(2,6):
            if len(lines) % i == 0:
                number = i
    else:
        false_intervals = list()
        ind = 0
        for i,e in enumerate(equaled):
            if i == 0:
                continue
            if not e:
                false_intervals.append(i - ind)
                ind = i
        false_intervals.append(i+1 - ind)
        counter = Counter(false_intervals)
        number = max(counter.keys(), key = lambda x: (counter[x],x))
        if number > 10:
            prev_maxes = set([number])
            while number > 10:
                prev_maxes.add(number)
                number = max(x for x in false_intervals if x not in prev_maxes)
    return number


def ilg_text_to_lines(path):
    delimiter = None
    with open(path, encoding='utf-8-sig', mode='r') as f:
        text = f.read()
        if delimiter is not None and delimiter not in text:
            e = DelimiterError('The delimiter specified does not create multiple words. Please specify another delimiter.')
            raise(e)
    lines = enumerate(text.splitlines())
    lines = [(x[0],x[1].strip().split(delimiter)) for x in lines if x[1].strip() != '']
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
    return None

def log_annotation_types(annotation_types):
    logging.info('Annotation type info')
    logging.info('--------------------')
    logging.info('')
    for a in annotation_types:
        logging.info(a.pretty_print())

def make_type_id(type_values, corpus):
    m = hashlib.sha1()
    value = ' '.join(map(str, type_values))
    value += ' ' + corpus
    m.update(value.encode())
    return m.hexdigest()

def guess_textgrid_format(path):
    from .inspect import inspect_labbcat, inspect_mfa
    if os.path.isdir(path):
        counts = {'mfa': 0, 'labbcat': 0, None: 0}
        for root, subdirs, files in os.walk(path):
            for f in files:
                if not f.lower().endswith('.textgrid'):
                    continue
                tg_path = os.path.join(root, f)
                tg = TextGrid()
                tg.read(tg_path)

                labbcat_parser = inspect_labbcat(tg_path)
                mfa_parser = inspect_mfa(tg_path)
                if labbcat_parser._is_valid(tg):
                    counts['labbcat'] += 1
                elif mfa_parser._is_valid(tg):
                    counts['mfa'] += 1
                else:
                    counts[None] += 1
        return max(counts.keys(), key = lambda x: counts[x])
    elif path.lower().endswith('.textgrid'):
        tg = TextGrid()
        tg.read(path)
        labbcat_parser = inspect_labbcat(path)
        mfa_parser = inspect_mfa(path)
        if labbcat_parser._is_valid(tg):
            return 'labbcat'
        elif mfa_parser._is_valid(tg):
            return 'mfa'
    return None

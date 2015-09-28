
import os
import re
import sys

from ..helper import (DiscourseData, AnnotationType,
                            Annotation, BaseAnnotation, find_wav_path)

def phone_match(one,two):
    if one != two and one not in two:
        return False
    return True

def inspect_discourse_timit(word_path):
    """
    Generate a list of AnnotationTypes for TIMIT

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    list of AnnotationTypes
        Auto-detected AnnotationTypes for TIMIT
    """
    annotation_types = [AnnotationType('spelling', 'surface_transcription', None, anchor = True),
                       AnnotationType('surface_transcription', None, 'spelling', base = True, token = True)]
    return annotation_types

def timit_to_data(word_path, phone_path, annotation_types = None,
                            stop_check = None, call_back = None):
    """
    This function creates a DiscourseData object from a words/phones
    file pair for TIMIT.

    In general, this function should not be called by users; loading
    of TIMIT should be done through the `load_directory_timit` function

    Parameters
    ----------
    word_path : str
        Fully specified path to the words text file
    phone_path : str
        Fully specified path to the phones text file
    annotation_types : list, optional
        List of annotation types to use, will be auto constructed if
        not given
    stop_check : callable or None
        Optional function to check whether to gracefully terminate early
    call_back : callable or None
        Optional function to supply progress information during the loading

    Returns
    -------
    DiscourseData
        Object containing the data for for the file pair
    """
    if annotation_types is None:
        annotation_types = inspect_discourse_timit(word_path)
    for a in annotation_types:
        a.reset()
    name = os.path.splitext(os.path.split(word_path)[1])[0]

    if call_back is not None:
        call_back('Reading files...')
        call_back(0,0)
    words = read_words(word_path)
    phones = read_phones(phone_path)

    data = DiscourseData(name, annotation_types)

    if call_back is not None:
        call_back('Parsing files...')
        call_back(0,len(words))
        cur = 0
    for i, w in enumerate(words):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            if cur % 20 == 0:
                call_back(cur)
        annotations = {}
        word = Annotation(w['spelling'])
        beg = w['begin']
        end = w['end']
        found_all = False
        found = []
        while not found_all:
            p = phones.pop(0)
            if p.begin < beg:
                continue
            found.append(p)
            if p.end == end:
                found_all = True
        n = data.base_levels[0]
        level_count = data.level_length(n)
        word.references.append(n)
        word.begins.append(level_count)
        word.ends.append(level_count + len(found))
        annotations[n] = found

        annotations[data.word_levels[0]] = [word]
        data.add_annotations(**annotations)
    return data

def load_directory_timit(corpus_context, path,
                            annotation_types = None,
                            feature_system_path = None,
                            stop_check = None, call_back = None):
    """
    Loads a directory of TIMIT files (separated into words files
    and phones files)

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Path to directory of text files
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse the glosses.
        Auto-generated based on dialect.
    feature_system_path : str, optional
        File path of FeatureMatrix binary to specify segments
    stop_check : callable or None
        Optional function to check whether to gracefully terminate early
    call_back : callable or None
        Optional function to supply progress information during the loading

    """
    if call_back is not None:
        call_back('Finding  files...')
        call_back(0, 0)
    file_tuples = []
    for root, subdirs, files in os.walk(path):
        for filename in files:
            if stop_check is not None and stop_check():
                return
            if not filename.lower().endswith('.wrd'):
                continue
            file_tuples.append((root, filename))
    if call_back is not None:
        call_back('Parsing files...')
        call_back(0,len(file_tuples))
        cur = 0
    for i, t in enumerate(file_tuples):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back('Parsing file {} of {}...'.format(i+1, len(file_tuples)))
            call_back(i)
        root, filename = t
        name,ext = os.path.splitext(filename)
        if ext == '.WRD':
            phone_ext = '.PHN'
        elif ext == '.wrd':
            phone_ext = '.phn'
        word_path = os.path.join(root,filename)
        phone_path = os.path.splitext(word_path)[0] + phone_ext
        load_discourse_timit(corpus_context, word_path, phone_path, annotation_types)

    #if feature_system_path is not None:
    #    feature_matrix = load_binary(feature_system_path)
    #    corpus.lexicon.set_feature_matrix(feature_matrix)

def load_discourse_timit(corpus_context, word_path, phone_path,
                                    annotation_types = None,
                                    feature_system_path = None,
                                    stop_check = None, call_back = None):
    """
    Load a discourse from a TIMIT style corpus

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    word_path : str
        Full path to words text file
    phone_path : str
        Full path to phones text file
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse the glosses.
        Auto-generated based on dialect.
    feature_system_path : str
        Full path to pickled FeatureMatrix to use with the corpus
    stop_check : callable or None
        Optional function to check whether to gracefully terminate early
    call_back : callable or None
        Optional function to supply progress information during the loading
    """
    data = timit_to_data(word_path, phone_path,
                                    annotation_types,
                                    stop_check, call_back)
    data.wav_path = find_wav_path(word_path)
    corpus_context.add_discourse(data)

def read_phones(path):
    output = []
    sr = 16000
    with open(path,'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1])/ sr
            label = l[2]
            output.append(BaseAnnotation(label, begin, end))
    return output

def read_words(path):
    output = []
    sr = 16000
    with open(path,'r') as file_handle:
        for line in file_handle:
            l = line.strip().split(' ')
            begin = float(l[0]) / sr
            end = float(l[1]) / sr
            word = l[2]
            output.append({'spelling':word, 'begin':begin, 'end':end})
    return output

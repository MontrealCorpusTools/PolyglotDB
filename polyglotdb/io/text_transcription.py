import os
import re

from polyglotdb.exceptions import DelimiterError

from .helper import (compile_digraphs, parse_transcription, DiscourseData,
                    AnnotationType, text_to_lines,
                    Annotation, BaseAnnotation, Attribute)


def inspect_discourse_transcription(path):
    """
    Generate a list of AnnotationTypes for a specified text file for parsing
    it as a transcribed text

    Parameters
    ----------
    path : str
        Full path to text file

    Returns
    -------
    list of AnnotationTypes
        Autodetected AnnotationTypes for the text file
    """
    trans_delimiters = ['.', ';', ',']

    att = Attribute('transcription','tier','Transcription')
    a = AnnotationType('transcription', None, 'spelling', attribute = att,
                                            base = True)

    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.txt'):
                    continue
                with open(os.path.join(root,filename),
                            encoding='utf-8-sig', mode='r') as f:
                    for line in f.readlines():
                        trial = line.strip().split()
                        if a.trans_delimiter is None:
                            for t in trial:
                                for delim in trans_delimiters:
                                    if delim in t:
                                        a.trans_delimiter = delim
                                        break

                        a.add(trial, save = False)
    else:
        with open(path, encoding='utf-8-sig', mode='r') as f:
            for line in f.readlines():
                trial = line.strip().split()
                if a.trans_delimiter is None:
                    for t in trial:
                        for delim in trans_delimiters:
                            if delim in t:
                                a.trans_delimiter = delim
                                break

                a.add(trial, save = False)
    annotation_types = [a]
    annotation_types.append(AnnotationType('spelling', None, None,
                attribute = Attribute('spelling','spelling','Spelling'),
                                            anchor = True))
    return annotation_types

def transcription_text_to_data(path, annotation_types = None,
                            stop_check = None, call_back = None):


    name = os.path.splitext(os.path.split(path)[1])[0]

    if annotation_types is None:
        annotation_types = inspect_discourse_transcription(path)

    for a in annotation_types:
        a.reset()
    annotation_types.append(a)

    data = DiscourseData(name, annotation_types)

    lines = text_to_lines(path)
    if call_back is not None:
        call_back('Processing file...')
        call_back(0, len(lines))
        cur = 0
    trans_check = False
    n = 'transcription'

    for line in lines:
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            if cur % 20 == 0:
                call_back(cur)
        if not line or line == '\n':
            continue
        for word in line:
            annotations = {}
            trans = parse_transcription(word, data[n])
            if not trans_check and data[n].delimiter is not None and len(trans) > 1:
                trans_check = True
            spell = ''.join(x.label for x in trans)
            if spell == '':
                continue

            word = Annotation(spell)
            for x in trans:
                x.super_id = word.id
            tier_elements = trans
            level_count = data.level_length(n)
            word.references.append(n)
            word.begins.append(level_count)
            word.ends.append(level_count + len(tier_elements))
            annotations[n] = tier_elements
            annotations['spelling'] = [word]
            data.add_annotations(**annotations)
    if data[n].delimiter and not trans_check:
        raise(DelimiterError('The transcription delimiter specified does not create multiple segments. Please specify another delimiter.'))

    return data

def load_directory_transcription(corpus_context, path, annotation_types = None,
                                feature_system_path = None,
                                stop_check = None, call_back = None):
    """
    Loads a directory of transcribed texts.

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Path to directory of text files
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse text files
    feature_system_path : str, optional
        File path of FeatureMatrix binary to specify segments
    stop_check : callable, optional
        Optional function to check whether to gracefully terminate early
    call_back : callable, optional
        Optional function to supply progress information during the loading
    """
    if call_back is not None:
        call_back('Finding  files...')
        call_back(0, 0)
    file_tuples = []
    for root, subdirs, files in os.walk(path, followlinks = True):
        for filename in files:
            if not filename.lower().endswith('.txt'):
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
            call_back('Parsing file {} of {}...'.format(i+1,len(file_tuples)))
            call_back(i)
        root, filename = t
        path = os.path.join(root, filename)
        name = os.path.splitext(filename)[0]
        load_discourse_transcription(corpus_context, path, annotation_types,
                    feature_system_path)


def load_discourse_transcription(corpus_context, path, annotation_types = None,
                    feature_system_path = None,
                    stop_check = None, call_back = None):
    """
    Load a discourse from a text file containing running transcribed text

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Full path to text file
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse text files
    feature_system_path : str, optional
        Full path to pickled FeatureMatrix to use with the Corpus
    stop_check : callable, optional
        Optional function to check whether to gracefully terminate early
    call_back : callable, optional
        Optional function to supply progress information during the loading
    """
    if feature_system_path is not None:
        if not os.path.exists(feature_system_path):
            raise(PCTOSError("The feature path specified ({}) does not exist".format(feature_system_path)))

    data = transcription_text_to_data(path, annotation_types,
                            stop_check, call_back)
    corpus_context.add_discourse(data)

    #if feature_system_path is not None:
    #    feature_matrix = load_binary(feature_system_path)
    #    discourse.lexicon.set_feature_matrix(feature_matrix)


def export_discourse_transcription(discourse, path, trans_delim = '.', single_line = False):
    """
    Export an transcribed discourse to a text file

    Parameters
    ----------
    discourse : Discourse
        Discourse object to export
    path : str
        Path to export to
    trans_delim : str, optional
        Delimiter for segments, defaults to ``.``
    single_line : bool, optional
        Flag to enforce all text to be on a single line, defaults to False.
        If False, lines are 10 words long.
    """
    with open(path, encoding='utf-8', mode='w') as f:
        count = 0
        for i, wt in enumerate(discourse):
            count += 1
            f.write(trans_delim.join(wt.transcription))
            if i != len(discourse) -1:
                if not single_line and count <= 10:
                    f.write(' ')
                else:
                    count = 0
                    f.write('\n')

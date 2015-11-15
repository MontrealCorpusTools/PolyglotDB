import os

from polyglotdb.exceptions import DelimiterError

from .helper import (DiscourseData, Annotation, BaseAnnotation,
                        AnnotationType, text_to_lines)

def inspect_discourse_spelling(path, support_corpus_path = None):
    """
    Generate a list of AnnotationTypes for a specified text file for parsing
    it as an orthographic text

    Parameters
    ----------
    path : str
        Full path to text file
    support_corpus_path : str, optional
        Full path to a corpus to look up transcriptions from spellings
        in the text

    Returns
    -------
    list of AnnotationTypes
        Autodetected AnnotationTypes for the text file
    """
    a = AnnotationType('spelling', None, None, anchor = True, token = False)
    if os.path.isdir(path):
        for root, subdirs, files in os.walk(path):
            for filename in files:
                if not filename.lower().endswith('.txt'):
                    continue
                with open(os.path.join(root,filename),
                            encoding='utf-8-sig', mode='r') as f:
                    for line in f.readlines():
                        trial = line.strip().split()

                        a.add(trial, save = False)
    else:
        with open(path, encoding='utf-8-sig', mode='r') as f:
            for line in f.readlines():
                trial = line.strip().split()

                a.add(trial, save = False)
    annotation_types = [a]
    if support_corpus_path is not None:
        annotation_types += [AnnotationType('transcription', None, None)]
    return annotation_types

def spelling_text_to_data(path, annotation_types = None,
                            support_corpus_path = None, ignore_case = True,
                            stop_check = None, call_back = None):

    name = os.path.splitext(os.path.split(path)[1])[0]
    if support_corpus_path is not None:
        if not os.path.exists(support_corpus_path):
            raise(PCTOSError("The corpus path specified ({}) does not exist".format(support_corpus_path)))
        support = load_binary(support_corpus_path)
    if annotation_types is None:
        annotation_types = inspect_discourse_spelling(path, support_corpus_path)

    for a in annotation_types:
        a.reset()
    data = DiscourseData(name, annotation_types)

    lines = text_to_lines(path)
    if call_back is not None:
        call_back('Processing file...')
        call_back(0, len(lines))
        cur = 0

    for line in lines:
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            cur += 1
            if cur % 20 == 0:
                call_back(cur)
        if not line or line == '\n':
            continue
        annotations = {}
        for word in line:
            spell = word.strip()
            spell = ''.join(x for x in spell if not x in data['word'].ignored_characters)
            if spell == '':
                continue
            word = Annotation(spell)
            if support_corpus_path is not None:
                trans = None
                try:
                    trans = support.find(spell, ignore_case = ignore_case).transcription
                except KeyError:
                    trans = []
                n = data.base_levels[0]
                tier_elements = [BaseAnnotation(x) for x in trans]
                level_count = data.level_length(n)
                word.references.append(n)
                word.begins.append(level_count)
                word.ends.append(level_count + len(tier_elements))
                annotations[n] = tier_elements
            annotations['word'] = [word]
            data.add_annotations(**annotations)

    return data

def load_directory_spelling(corpus_context, path, annotation_types = None,
                            support_corpus_path = None, ignore_case = False,
                            stop_check = None, call_back = None):
    """
    Loads a directory of orthographic texts

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Path to directory of text files
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse text files
    support_corpus_path : str, optional
        File path of corpus binary to load transcriptions from
    ignore_case : bool, optional
        Specifies whether lookups in the support corpus should ignore case
    stop_check : callable, optional
        Optional function to check whether to gracefully terminate early
    call_back : callable, optional
        Optional function to supply progress information during the function
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
    parsed_data = {}
    for i, t in enumerate(file_tuples):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back('Parsing file {} of {}...'.format(i+1, len(file_tuples)))
            call_back(i)
        root, filename = t
        path = os.path.join(root, filename)
        name = os.path.splitext(filename)[0]
        data = spelling_text_to_data(path, annotation_types,
                    support_corpus_path, ignore_case,
                        stop_check, call_back)
        parsed_data[t] = data

    if call_back is not None:
        call_back('Parsing annotation types...')
    corpus_context.add_types(parsed_data)
    for i,(t,data) in enumerate(sorted(parsed_data.items(), key = lambda x: x[0])):
        if call_back is not None:
            name = t[1]
            call_back('Importing discourse {} of {} ({})...'.format(i+1, len(file_tuples), name))
            call_back(i)
        corpus_context.add_discourse(data)

def load_discourse_spelling(corpus_context, path, annotation_types = None,
                            support_corpus_path = None, ignore_case = False,
                            stop_check = None, call_back = None):
    """
    Load a discourse from a text file containing running text of
    orthography

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Full path to text file
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse text files
    support_corpus_path : str, optional
        Full path to a corpus to look up transcriptions from spellings
        in the text
    ignore_case : bool, optional
        Specify whether to ignore case when using spellings in the text
        to look up transcriptions
    stop_check : callable, optional
        Callable that returns a boolean for whether to exit before
        finishing full calculation
    call_back : callable, optional
        Function that can handle strings (text updates of progress),
        tuples of two integers (0, total number of steps) and an integer
        for updating progress out of the total set by a tuple
    """

    data = spelling_text_to_data(path, annotation_types,
                support_corpus_path, ignore_case,
                    stop_check, call_back)
    corpus_context.add_types({data.name: data})
    corpus_context.add_discourse(data)

def export_discourse_spelling(corpus_context, discourse,
                            path, words_per_line = 10):
    """
    Export an orthography discourse to a text file

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    discourse : str
        Discourse to export
    path : str
        Path to export to
    words_per_line : int, optional
        Max number of words per line, set to -1 for a single line
    """

    discourse = corpus_context.discourse(discourse)
    with open(path, encoding='utf-8', mode='w') as f:
        count = 0
        for i, wt in enumerate(discourse):
            count += 1
            f.write(wt.label)
            if i != len(discourse) -1:
                if words_per_line > 0 and count <= words_per_line:
                    f.write(' ')
                else:
                    count = 0
                    f.write('\n')

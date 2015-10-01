
import os
import re
import sys

FILLERS = set(['uh','um','okay','yes','yeah','oh','heh','yknow','um-huh',
                'uh-uh','uh-huh','uh-hum','mm-hmm'])

from ..helper import (DiscourseData, AnnotationType,
                            Annotation, BaseAnnotation, find_wav_path)

from polyglotdb.exceptions import BuckeyeParseError

def phone_match(one,two):
    if one != two and one not in two:
        return False
    return True

def inspect_discourse_buckeye(word_path):
    """
    Generate a list of AnnotationTypes for the Buckeye corpus

    Parameters
    ----------
    word_path : str
        Full path to text file

    Returns
    -------
    list of AnnotationTypes
        Auto-detected AnnotationTypes for the Buckeye corpus
    """
    annotation_types = [AnnotationType('spelling', 'surface_transcription', None, anchor = True),
                        AnnotationType('transcription', None, 'spelling', base = False, token = False),
                        AnnotationType('surface_transcription', None, 'spelling', base = True, token = True),
                        AnnotationType('category', None, 'spelling', base = False, token = True)]

    return annotation_types

def buckeye_to_data(word_path, phone_path, annotation_types = None,
                           stop_check = None, call_back = None):
    """
    This function creates a DiscourseData object from a words/phones
    file pair for the Buckeye corpus.

    In general, this function should not be called by users; loading
    of Buckeye should be done through the `load_directory_buckeye` function

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
        annotation_types = inspect_discourse_buckeye(word_path)
    for a in annotation_types:
        a.reset()
    name = os.path.splitext(os.path.split(word_path)[1])[0]

    if call_back is not None:
        call_back('Reading files...')
        call_back(0,0)
    try:

        words = read_words(word_path)
    except Exception as e:
        print(e)
        return
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
        for n in data.base_levels:
            if data[n].token:
                if w[n] is None:
                    found = [BaseAnnotation('?',w['begin'], w['end'])]
                else:
                    expected = w[n]
                    found = []
                    while len(found) < len(expected):
                        cur_phone = phones.pop(0)
                        if phone_match(cur_phone.label,expected[len(found)]) \
                            and cur_phone.end >= beg and cur_phone.begin <= end:
                                found.append(cur_phone)

                        if not len(phones) and i < len(words)-1:
                            print(BuckeyeParseError(word_path, [w]))
                            return
            else:
                if w[n] is None:
                    found = [BaseAnnotation('?')]
                else:
                    found = [BaseAnnotation(x) for x in w[n]]
            level_count = data.level_length(n)
            word.references.append(n)
            word.begins.append(level_count)
            word.ends.append(level_count+len(found))
            annotations[n] = found
        for at in annotation_types:
            if at.ignored:
                continue
            if at.base:
                continue
            if at.anchor:
                continue
            value = w[at.name]
            if at.delimited:
                value = [BaseAnnotation(x) for x in parse_transcription(value)]
            if at.token:
                word.token_properties[at.name] = value
            else:
                word.type_properties[at.name] = value
        annotations[data.word_levels[0]] = [word]
        data.add_annotations(**annotations)
    return data

def load_directory_buckeye(corpus_context, path,
                                    annotation_types = None,
                                    feature_system_path = None,
                                    stop_check = None, call_back = None):
    """
    Loads a directory of Buckeye files (separated into words files
    and phones files)

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    path : str
        Path to directory of text files
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse the files.
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
    for root, subdirs, files in os.walk(path, followlinks = True):
        subdirs.sort()
        for filename in sorted(files):
            if stop_check is not None and stop_check():
                return
            if not filename.lower().endswith('.words'):
                continue
            file_tuples.append((root, filename))
    if call_back is not None:
        call_back('Parsing files...')
        call_back(0, len(file_tuples))
        cur = 0
    for i, t in enumerate(file_tuples):
        if stop_check is not None and stop_check():
            return
        root, filename = t
        name,ext = os.path.splitext(filename)
        if call_back is not None:
            call_back('Parsing discourse {} of {} ({})...'.format(i+1, len(file_tuples), name))
            call_back(i)
        if ext == '.words':
            phone_ext = '.phones'
        elif ext == '.WORDS':
            phone_ext = '.PHONES'
        word_path = os.path.join(root,filename)
        phone_path = os.path.splitext(word_path)[0] + phone_ext
        load_discourse_buckeye(corpus_context, word_path, phone_path, annotation_types)

    #if feature_system_path is not None:
    #    feature_matrix = load_binary(feature_system_path)
    #    corpus.lexicon.set_feature_matrix(feature_matrix)

def load_discourse_buckeye(corpus_context, word_path, phone_path,
                                    annotation_types = None,
                                    feature_system_path = None,
                                    stop_check = None, call_back = None):
    """
    Load a discourse from a Buckeye file pair

    Parameters
    ----------
    corpus_context : CorpusContext
        Context manager for the corpus
    word_path : str
        Full path to words text file
    phone_path : str
        Full path to phones text file
    annotation_types : list of AnnotationType, optional
        List of AnnotationType specifying how to parse the files.
        Auto-generated based on dialect.
    feature_system_path : str
        Full path to pickled FeatureMatrix to use with the Corpus
    stop_check : callable or None
        Optional function to check whether to gracefully terminate early
    call_back : callable or None
        Optional function to supply progress information during the loading
    """
    data = buckeye_to_data(word_path,phone_path,
                                    annotation_types,
                                    stop_check, call_back)
    if data is None:
        return
    data.wav_path = find_wav_path(word_path)
    corpus_context.add_discourse(data)

def read_phones(path):
    output = []
    with open(path,'r') as file_handle:
        header_pattern = re.compile("#\r{0,1}\n")
        line_pattern = re.compile("\s+\d{3}\s+")
        label_pattern = re.compile(" {0,1};| {0,1}\+")
        f = header_pattern.split(file_handle.read())[1]
        flist = f.splitlines()
        begin = 0.0
        for l in flist:
            line = line_pattern.split(l.strip())
            try:
                end = float(line[0])
            except ValueError: # Missing phone label
                print('Warning: no label found in line: \'{}\''.format(l))
                continue
            label = sys.intern(label_pattern.split(line[1])[0])
            output.append(BaseAnnotation(label, begin, end))
            begin = end
    return output

def read_words(path):
    output = []
    misparsed_lines = []
    with open(path,'r') as file_handle:
        f = re.split(r"#\r{0,1}\n",file_handle.read())[1]
        line_pattern = re.compile("; | \d{3} ")
        begin = 0.0
        flist = f.splitlines()
        for l in flist:
            line = line_pattern.split(l.strip())
            try:
                end = float(line[0])
                word = sys.intern(line[1])
                if word[0] != "<" and word[0] != "{":
                    citation = line[2].split(' ')
                    phonetic = line[3].split(' ')
                    if len(line) > 4:
                        category = line[4]
                        if word in FILLERS:
                            category = 'UH'
                    else:
                        category = None
                else:
                    citation = None
                    phonetic = None
                    category = None
            except IndexError:
                misparsed_lines.append(l)
                continue
            line = {'spelling':word,'begin':begin,'end':end,
                    'transcription':citation,'surface_transcription':phonetic,
                    'category':category}
            output.append(line)
            begin = end
    if misparsed_lines:
        raise(BuckeyeParseError(path, misparsed_lines))
    return output

import re

def inspect_speaker_globalphone(path):
    return

def read_text_file(path):
    line_number = re.compile('^;\s+(?P<sentence_num>\d+):$')
    current = None
    data = {}
    with open(path, mode = 'r', encoding = 'utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith(';SprecherID'):
                continue
            if current is None:
                m = line_number.match(line)
                sentence_num = m.group('sentence_num')
                current = sentence_num
            else:
                data[current] = line
                current = None
    return data

def read_spk_file(path):
    line_pattern = re.compile('^(?P<key>.+):(?P<value>.+)$')
    begin = False
    data = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()[1:]
            if line == 'BEGIN':
                begin = True
                continue
            if line == 'END':
                continue
            if line == 'SPEAKERDATA -------------':
                continue
            if line == 'RECORDING SETUP ------------':
                continue
            if not begin:
                continue
            print(line)
            m = line_pattern.match(line)
            data[m.group('key')] = m.group('value')
    return data

def globalphone_to_data(trl_path, spk_path, rmn_path, adc_directory, annotation_types = None,
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
    speaker_name = os.path.extname(os.path.basename(spk_path))[0]
    speaker_data = read_spk_file(spk_path)

    trl_data = read_text_file(trl_path)

    rmn_data = read_text_file(rmn_path)



def load_speaker_globalphone(corpus_context, trl_path, spk_path, adc_path,
                                    annotation_types = None,
                                    feature_system_path = None,
                                    stop_check = None, call_back = None):
    pass

def load_directory_globalphone(corpus_context, path,
                                    annotation_types = None,
                                    feature_system_path = None,
                                    stop_check = None, call_back = None):
    """
    Loads a directory of GlobalPhone files (separate directories for
    transcripts, sound files, speaker information, and alignments.

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
    for root, subdirs, files in os.walk(path, followlinks = True):
        for filename in files:
            if stop_check is not None and stop_check():
                return
            if not filename.lower().endswith('.words'):
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


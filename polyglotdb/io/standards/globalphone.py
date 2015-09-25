

def read_trl_file(path):
    pass

def read_spk_file(path):
    pass

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
    for root, subdirs, files in os.walk(path):
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


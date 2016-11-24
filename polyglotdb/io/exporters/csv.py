from csv import DictWriter

def make_safe(value, delimiter):
    """
    Recursively parse transcription lists into strings for saving

    Parameters
    ----------
    value : list or None
        Object to make into string

    delimiter : str
        Character to mark boundaries between list elements

    Returns
    -------
    str
        Safe string
    """
    if isinstance(value,list):
        return delimiter.join(map(lambda x: make_safe(x, delimiter),value))
    if value is None:
        return ''
    return str(value)


def save_results(results, path, header = None, mode = 'w'):
    """
    Writes results to path specified 

    Parameters
    ----------
    results : dict
        the results to write
    path : str
        the path to the save file
    header : list
        Defaults to none
    mode : str
        defaults to 'w', or write. Can be 'a', append
    """
    if header is None:
        header = results.columns
    with open(path, mode, encoding = 'utf8', newline = '') as f:
        writer = DictWriter(f, header)
        if mode != 'a':
            writer.writeheader()
        for line in results:
            line = {k: make_safe(line[k], '/') for k in header}
            writer.writerow(line)

def export_corpus_csv(corpus, path,
                    delimiter = ',', trans_delimiter = '.',
                    variant_behavior = None):
    """
    Save a corpus as a column-delimited text file

    Parameters
    ----------
    corpus : :class:`~polyglotdb.corpus.CorpusContext`
        Corpus to save to text file
    path : str
        Full path to write text file
    delimiter : str
        Character to mark boundaries between columns.  Defaults to ','
    trans_delimiter : str
        Character to mark boundaries in transcriptions.  Defaults to '.'
    variant_behavior : str, optional
        How to treat variants, 'token' will have a line for each variant,
        'column' will have a single column for all variants for a word,
        and the default will not include variants in the output
    """
    header = []
    for a in corpus.attributes:
        header.append(str(a))

    if variant_behavior == 'token':
        for a in corpus.attributes:
            if a.att_type == 'tier':
                header.append('Token_' + str(a))
        header.append('Token_Frequency')
    elif variant_behavior == 'column':
        header += ['Variants']

    with open(path, encoding='utf-8', mode='w') as f:
        print(delimiter.join(header), file=f)

        for word in corpus.iter_sort():
            word_outline = []
            for a in corpus.attributes:
                word_outline.append(make_safe(getattr(word, a.name),trans_delimiter))
            if variant_behavior == 'token':
                var = word.variants()
                for v, freq in var.items():
                    token_line = []
                    for a in corpus.attributes:
                        if a.att_type == 'tier':
                            if a.name == 'transcription':
                                token_line.append(make_safe(v, trans_delimiter))
                            else:
                                segs = a.range
                                t = v.match_segments(segs)
                                token_line.append(make_safe(v, trans_delimiter))
                    token_line.append(make_safe(freq, trans_delimiter))
                    print(delimiter.join(word_outline + token_line), file=f)
                continue
            elif variant_behavior == 'column':
                var = word.variants()
                d = ', '
                if delimiter == ',':
                    d = '; '
                var = d.join(make_safe(x,trans_delimiter) for x in sorted(var.keys(), key = lambda y: var[y]))
                word_outline.append(var)
            print(delimiter.join(word_outline), file=f)

def export_feature_matrix_csv(feature_matrix, path, delimiter = ','):
    """
    Save a FeatureMatrix as a column-delimited text file

    Parameters
    ----------
    feature_matrix : FeatureMatrix
        FeatureMatrix to save to text file
    path : str
        Full path to write text file
    delimiter : str
        Character to mark boundaries between columns.  Defaults to ','
    """
    with open(path, encoding='utf-8', mode='w') as f:
        header = ['symbol'] + feature_matrix.features
        writer = DictWriter(f, header,delimiter=delimiter)
        writer.writerow({h: h for h in header})
        for seg in feature_matrix.segments:
            #If FeatureMatrix uses dictionaries
            #outdict = feature_matrix[seg]
            #outdict['symbol'] = seg
            #writer.writerow(outdict)
            if seg in ['#','']: #wtf
                continue
            featline = feature_matrix.seg_to_feat_line(seg)
            outdict = {header[i]: featline[i] for i in range(len(header))}
            writer.writerow(outdict)


def load_feature_matrix_csv(name, path, delimiter, stop_check=None, call_back=None):
    """
    Load a FeatureMatrix from a column-delimited text file

    Parameters
    ----------
    name : str
        Informative identifier to refer to feature system
    path : str
        Full path to text file
    delimiter : str
        Character to use for spliting lines into columns
    stop_check : callable, optional
        Optional function to check whether to gracefully terminate early
    call_back : callable, optional
        Optional function to supply progress information during the function

    Returns
    -------
    FeatureMatrix
        FeatureMatrix generated from the text file

    """
    text_input = []
    with open(path, encoding='utf-8-sig', mode='r') as f:
        reader = DictReader(f, delimiter=delimiter)
        lines = list(reader)

    if call_back is not None:
        call_back('Reading file...')
        call_back(0, len(lines))

    for i, line in enumerate(lines):
        if stop_check is not None and stop_check():
            return
        if call_back is not None:
            call_back(i)

        if line:
            if len(line.keys()) == 1:
                raise (DelimiterError)
            if 'symbol' not in line:
                raise (KeyError)
            # Compat
            newline = {}
            for k, v in line.items():
                if k == 'symbol':
                    newline[k] = v
                elif v is not None:
                    newline[k] = v[0]
            text_input.append(newline)

    feature_matrix = FeatureMatrix(name, text_input)
    feature_matrix.validate()
    return feature_matrix

def export_discourse_ilg(corpus_context, discourse, path,
                         trans_delim='.', annotations=None, words_per_line=10):
    """
    Export a discourse to an interlinear gloss text file, with a maximal
    line size of 10 words

    Parameters
    ----------
    corpus_context : :class:`~polyglotdb.corpus.CorpusContext`
        the type of corpus
    discourse : str
        discourse name 
    path : str
        Path to export to
    trans_delim : str, optional
        Delimiter for segments, defaults to ``.``
    """
    if annotations is None:
        raise (Exception('Must specify annotations to output'))
    discourse = corpus_context.discourse(discourse, annotations)
    with open(path, encoding='utf-8', mode='w') as f:
        line = {x: [] for x in annotations}
        count = 0
        for i, wt in enumerate(discourse):
            count += 1
            for a in annotations:
                line[a].append(getattr(wt, a))
            if i != len(discourse) - 1:
                if words_per_line > 0 and count == words_per_line:
                    for a in annotations:
                        f.write(' '.join(line[a]) + '\n')
                    count = 0
                    line = {x: [] for x in annotations}
        if count != 0:
            for a in annotations:
                f.write(' '.join(line[a]) + '\n')
            count = 0
            line = {x: [] for x in annotations}

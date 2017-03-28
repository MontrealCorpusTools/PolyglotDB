def export_discourse_spelling(corpus_context, discourse,
                              path, words_per_line=10):
    """
    Export an orthography discourse to a text file

    Parameters
    ----------
    corpus_context: :class:`~polyglotdb.corpus.CorpusContext`
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
            if i != len(discourse) - 1:
                if words_per_line > 0 and count <= words_per_line:
                    f.write(' ')
                else:
                    count = 0
                    f.write('\n')
